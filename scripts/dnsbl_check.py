"""DNSBL check for cold-email sending domains.

Checks a domain against the public blocklists that move email deliverability,
using only the standard library (system DNS via socket). Called by
/deliverability-monitor step 4. What counts as a problem and what to do about a
listing live in .claude/skills/inbox-setup/references/deliverability.md
> Monitoring thresholds (the "Auth ... any fail" row and the "On a pause"
recovery path). This script only reports listed / clean / blocked; it defines no
thresholds.

A DNSBL answers a normal A-record query: an answer in 127.0.0.0/8 means "listed",
NXDOMAIN means "not listed". Spamhaus returns 127.255.255.x and SURBL returns
127.0.0.1 when the query itself was refused (public resolver, rate limit): that
is inconclusive, not a hit.

Run:  python scripts/dnsbl_check.py                          # offline self-check
      python scripts/dnsbl_check.py getexample.com example.com
      python scripts/dnsbl_check.py dbltest.com              # live smoke -> LISTED on Spamhaus DBL
"""
import socket
import sys

# Domain-based lists: query "<domain>.<zone>".
DOMAIN_ZONES = {
    "Spamhaus DBL": "dbl.spamhaus.org",
    "SURBL multi": "multi.surbl.org",
}
# IP-based lists: query "<reversed A-record octets>.<zone>".
# ponytail: for a Gmail-sending client the real sending IP is Google's shared
# pool, not the sending domain's own A record, so a hit here only matters when the
# domain also hosts mail. Cheap to check anyway; upgrade path is to pass the
# provider's dedicated sending IPs directly when a client sends on its own IPs.
IP_ZONES = {
    "Spamhaus ZEN": "zen.spamhaus.org",
    "SpamCop": "bl.spamcop.net",
    "Barracuda": "b.barracudacentral.org",
}


def _resolve(name):
    """First A record for `name`, or None on NXDOMAIN / no answer."""
    try:
        return socket.gethostbyname(name)
    except socket.gaierror:
        return None


def classify(answer):
    """'listed', 'clean', or 'blocked' (query refused / rate-limited: inconclusive)."""
    if answer is None:
        return "clean"
    if answer == "127.0.0.1" or answer.startswith("127.255.255."):
        return "blocked"
    if answer.startswith("127."):
        return "listed"
    return "clean"  # unexpected non-127 answer: not a hit


def reverse_ip(ip):
    return ".".join(reversed(ip.split(".")))


def check_domain(domain):
    """{list_name: 'listed'|'clean'|'blocked'} across every zone for one domain."""
    domain = domain.strip().lower().strip(".")
    out = {}
    for name, zone in DOMAIN_ZONES.items():
        out[name] = classify(_resolve(f"{domain}.{zone}"))
    ip = _resolve(domain)
    for name, zone in IP_ZONES.items():
        label = f"{name} (A {ip})" if ip else name
        out[label] = classify(_resolve(f"{reverse_ip(ip)}.{zone}")) if ip else "clean"
    return out


def _selfcheck():
    assert reverse_ip("127.0.1.2") == "2.1.0.127"
    assert reverse_ip("8.8.4.4") == "4.4.8.8"
    assert classify(None) == "clean"
    assert classify("127.0.1.2") == "listed"
    assert classify("127.0.0.2") == "listed"
    assert classify("127.255.255.254") == "blocked"   # Spamhaus: query via public resolver
    assert classify("127.0.0.1") == "blocked"          # SURBL: query refused
    assert classify("93.184.216.34") == "clean"        # non-127 answer is not a hit
    assert f"a.com.{DOMAIN_ZONES['Spamhaus DBL']}" == "a.com.dbl.spamhaus.org"
    print("dnsbl_check.py: all checks passed")
    # ponytail: self-check is offline only. Live reachability is one line:
    #   python scripts/dnsbl_check.py dbltest.com   -> Spamhaus DBL should read LISTED


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _selfcheck()
    else:
        for d in sys.argv[1:]:
            print(d)
            for name, verdict in check_domain(d).items():
                print(f"  {verdict.upper():8} {name}")
            print()
