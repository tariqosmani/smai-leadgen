"""Free-tier email verification for the lead funnel.

A bad address that gets cold-emailed burns the sending domain's reputation, which is
the whole thing `/inbox-setup` provisions. `/lead-find` runs this after contact
enrichment to set the `email_status` field; `/lead-outreach` runs it again as a hard
pre-send guard. Full write-up: docs/email-verification.md

Checks, in order: syntax -> disposable domain -> MX / mail route -> role address.
Returns one of the `email_status` enum values with a reason string:

    invalid   bad syntax, disposable domain, no mail route, or a role inbox
    unknown   syntax + domain OK, mailbox not probed (this is the normal free-tier pass)
    catchall  only a paid verifier or Instantly sets this
    valid     only a paid verifier or Instantly sets this

# ponytail: syntax + MX + disposable + role gets ~80% of the value with zero deps and
# zero API spend. SMTP RCPT probing and a paid list (MillionVerifier / ZeroBounce /
# NeverBounce, ~$0.0004-$0.001 per verify) are the upgrade a retainer client funds.
# See docs/email-verification.md > Paid upgrade path.

Run:  python scripts/verify_email.py                 # self-check
      python scripts/verify_email.py jane@acme.com   # verify one address
"""
import re
import socket
import subprocess
import sys

STATUSES = ("valid", "catchall", "unknown", "invalid")

# Practical syntax gate. Not full RFC 5322 (that matches almost anything); this is the
# shape a real work address takes. Consecutive dots are rejected separately.
_SYNTAX_RE = re.compile(r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
                        r"@(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$")

_MX_RE = re.compile(r"mail exchanger\s*=\s*([^\s,]+)", re.I)

# Short built-in list of throwaway / disposable mailbox providers. Not exhaustive by
# design (a full list is thousands of domains and goes stale). Add the ones that show
# up in real enrichment output. ponytail: static list, swap for a maintained feed only
# if disposables actually get through.
DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "guerrillamailblock.com", "sharklasers.com",
    "10minutemail.com", "10minutemail.net", "tempmail.com", "temp-mail.org", "tempmail.dev",
    "throwawaymail.com", "yopmail.com", "yopmail.fr", "getnada.com", "nada.email",
    "trashmail.com", "trashmail.de", "maildrop.cc", "dispostable.com", "fakeinbox.com",
    "mailnesia.com", "mintemail.com", "spamgourmet.com", "mailcatch.com", "tempinbox.com",
    "emailondeck.com", "moakt.com", "mohmal.com", "spam4.me", "mytemp.email",
    "harakirimail.com", "incognitomail.com", "spambog.com", "maileater.com", "burnermail.io",
    "33mail.com", "anonaddy.me", "mailsac.com", "inboxkitten.com", "tmail.ws", "tmailor.com",
}

# Local-parts that are a shared inbox, not a named person. A founder-signed cold email to
# one of these is wrong regardless of whether it would technically deliver, and ICP hard
# exclusions already bar generic-inbox-only leads, so we flag it as `invalid`.
ROLE_LOCALPARTS = {
    "info", "sales", "hello", "team", "admin", "administrator", "support", "help",
    "contact", "contactus", "office", "enquiries", "inquiries", "enquiry", "inquiry",
    "billing", "accounts", "accounting", "finance", "ap", "ar", "hr", "jobs", "careers",
    "recruiting", "recruitment", "marketing", "press", "media", "pr", "legal",
    "webmaster", "postmaster", "hostmaster", "abuse", "noreply", "no-reply", "donotreply",
    "do-not-reply", "newsletter", "notifications", "notification", "mailer", "mail",
    "service", "services", "feedback", "general", "hi", "hey", "orders", "booking",
    "bookings", "reservations", "hello-there",
}


def _run(cmd):
    """Run a lookup tool. Returns (returncode_or_None, combined_output)."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (OSError, subprocess.SubprocessError):
        return None, ""


def _parse_nslookup(out):
    """'mx' | 'none' | 'refused' | None (no verdict) from nslookup -type=mx output.

    'refused' = the resolver failed to answer (REFUSED / SERVFAIL / timeout). That is
    NOT proof the domain is dead, so the caller falls through instead of concluding
    'none' (which would hard-flag the address invalid).
    """
    low = out.lower()
    if "non-existent domain" in low or "nxdomain" in low:
        return "none"
    if any(p in low for p in ("query refused", "servfail", "server failed", "refused",
                              "timed out", "timeout", "no response from server",
                              "no servers could be reached", "unspecified error")):
        return "refused"
    hosts = [h.strip().strip(".").lower() for h in _MX_RE.findall(out)]
    if hosts:
        # a lone "(root)" / "." is an RFC 7505 null MX: the domain says "no mail here".
        real = [h for h in hosts if h and h != "(root)"]
        return "mx" if real else "none"
    return None


def mx_lookup(domain):
    """Does `domain` have a mail route?  'mx' (yes) | 'none' (checked, no route) |
    'error' (could not check - no DNS tool and no resolver).

    # ponytail: presence check only. No MX priority ordering, no A/AAAA of the MX host,
    # no SMTP banner. nslookup (Windows + most Linux) is tried first, then dig, then a
    # plain getaddrinfo for the implicit-MX (RFC 5321 s5) case.
    """
    if not domain:
        return "none"
    resolver_failed = False
    _, out = _run(["nslookup", "-type=mx", domain])
    if out:
        verdict = _parse_nslookup(out)
        if verdict == "refused":
            resolver_failed = True          # can't trust this resolver, keep trying
        elif verdict:
            return verdict
    rc, out = _run(["dig", "+short", "mx", domain])
    if rc == 0:
        lines = [ln for ln in out.splitlines() if ln.strip()]
        if lines:
            real = [ln for ln in lines if ln.split()[-1].strip(".")]
            return "mx" if real else "none"
    try:
        socket.getaddrinfo(domain, None)
        return "mx"          # resolves to an address -> mail can route to it
    except socket.gaierror:
        # A prior resolver REFUSED/SERVFAIL means we can't call this a dead domain.
        return "error" if resolver_failed else "none"
    except OSError:
        return "error"       # no network / resolver in this environment


def classify(email, mx):
    """Pure decision. `mx` is a mx_lookup() result: 'mx' | 'none' | 'error'.
    Returns (status, reason). Kept separate from the DNS call so the branching is
    testable offline."""
    e = (email or "").strip().lower()
    if not e:
        return "invalid", "no email address"
    if ".." in e or not _SYNTAX_RE.match(e):
        return "invalid", "bad syntax"
    local, _, domain = e.rpartition("@")
    if domain in DISPOSABLE_DOMAINS:
        return "invalid", f"disposable domain ({domain})"
    if mx == "none":
        return "invalid", "domain has no mail route (no MX, no A record)"
    if local in ROLE_LOCALPARTS:
        return "invalid", f"role address ({local}@), not a named person"
    if mx == "error":
        return "unknown", "domain not checked (DNS lookup failed here), not confirmed"
    return "unknown", "syntax and mail route OK, mailbox not probed (free tier)"


def verify_email(email):
    """(status, reason) for one address. status is one of STATUSES."""
    e = (email or "").strip().lower()
    domain = e.rpartition("@")[2]
    return classify(e, mx_lookup(domain) if domain else "none")


def _selfcheck():
    # --- classify(): pure, offline, exhaustive over the branches ---
    assert classify("", "mx") == ("invalid", "no email address")
    assert classify("not-an-email", "mx")[0] == "invalid"
    assert classify("a@@b.com", "mx")[0] == "invalid"
    assert classify("jane.doe@", "mx")[0] == "invalid"
    assert classify("a..b@acme.com", "mx")[0] == "invalid"
    assert classify("jane@acme", "mx")[0] == "invalid"            # no TLD
    assert classify("jane@mailinator.com", "mx")[0] == "invalid"
    s, r = classify("jane@guerrillamail.com", "mx")
    assert s == "invalid" and "disposable" in r, (s, r)
    assert classify("jane@acme.com", "none")[0] == "invalid"      # dead domain beats role check
    s, r = classify("info@acme.com", "mx")
    assert s == "invalid" and "role address" in r, (s, r)
    assert classify("sales@acme.com", "mx")[0] == "invalid"
    assert classify("no-reply@acme.com", "mx")[0] == "invalid"
    s, r = classify("jane.doe@acme.com", "mx")
    assert s == "unknown" and "mailbox not probed" in r, (s, r)
    s, r = classify("jane.doe@acme.com", "error")
    assert s == "unknown" and "not checked" in r, (s, r)
    assert classify("info@acme.com", "none")[0] == "invalid"      # role on dead domain still invalid
    for out in (classify("x", "mx"), classify("j@ex.com", "error"), classify("j@ex.com", "mx")):
        assert out[0] in STATUSES, out

    # --- _parse_nslookup(): the three real-world shapes ---
    assert _parse_nslookup("google.com\tMX preference = 10, mail exchanger = smtp.google.com") == "mx"
    assert _parse_nslookup("example.com\tMX preference = 0, mail exchanger = (root)") == "none"
    assert _parse_nslookup("*** can't find nope.invalid: Non-existent domain") == "none"
    assert _parse_nslookup("** server can't find nope.invalid: NXDOMAIN") == "none"
    assert _parse_nslookup("*** gpon.net can't find bamf.com: Query refused") == "refused"
    assert _parse_nslookup("connection timed out; no servers could be reached") == "refused"
    assert _parse_nslookup("Server: x\nAddress: 1.2.3.4\n") is None  # no MX line, no verdict

    # --- verify_email(): one live smoke, network-tolerant (result must stay a legal status) ---
    for e in ("tariq.osmani@google.com", "info@google.com", "x@nxdomain-zzz-000.invalid"):
        assert verify_email(e)[0] in STATUSES, e

    print("verify_email.py: all checks passed")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _selfcheck()
    else:
        status, reason = verify_email(sys.argv[1])
        print(f"{status}\t{reason}")
