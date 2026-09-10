# Email verification

Bad email addresses must never get a cold send. A bounce hurts the sending domain's
reputation, and that reputation is the entire asset `/inbox-setup` provisions. This doc
covers how an address is checked, what the result means, and where it is read.

The check runs twice:

1. **`/lead-find`, after contact enrichment** (its step 3b) — verify every enriched email,
   set the `email_status` contract field.
2. **`/lead-outreach`, before every email send** (its step 4) — a hard guard: an address
   whose `email_status` is `invalid` is never handed to the Gmail send.

## The `email_status` values

`email_status` is a normalized contract field (`docs/pipeline-contract.md`). Airtable column
`Email Status`, a single select (`docs/pipeline-schema.md`).

| value | meaning | outreach treatment |
|---|---|---|
| `valid` | a paid verifier or Instantly confirmed the mailbox exists | send |
| `catchall` | the domain accepts all mail; the specific mailbox cannot be confirmed | send, note `catchall` in the Activity Log line |
| `unknown` | syntax and mail route are OK, the mailbox was not probed. **The normal free-tier pass.** | send by default; `/lead-outreach allow_unknown=false` blocks it. Note `unknown` in the log |
| `invalid` | bad syntax, disposable domain, no mail route, or a role inbox | **never sent.** `/lead-outreach` skips it and sets `next_action` to "find new contact" |

The free checker only ever returns `unknown` or `invalid`. `valid` and `catchall` come from
the paid upgrade path or from an Instantly import.

## Free tier: `scripts/verify_email.py`

No API key, no credits, standard library plus a shell DNS lookup. Checks, in order:

- **Syntax** — practical work-address shape, consecutive dots rejected. Fail -> `invalid`.
- **Disposable domain** — a short built-in list of throwaway providers (mailinator, guerrillamail,
  yopmail, ...). Match -> `invalid`.
- **MX / mail route** — `nslookup -type=mx <domain>`, then `dig +short mx`, then a plain
  `getaddrinfo` for the RFC 5321 implicit-MX case. No route, an RFC 7505 null MX, or a domain
  that does not resolve -> `invalid`. A route exists -> continue.
- **Role address** — `info@ sales@ hello@ team@ admin@ support@ billing@ careers@ ...` and the
  like. A founder-signed cold email to a shared inbox is wrong even when it would deliver, and
  ICP hard exclusions already bar generic-inbox-only leads. Match -> `invalid`.
- Otherwise -> `unknown` (with a reason noting the mailbox was not probed).

`python scripts/verify_email.py jane@acme.com` prints `<status>\t<reason>`. `classify()` is the
pure decision and has the self-check; `mx_lookup()` is the DNS call.

**Ceiling (`# ponytail:` in the script):** syntax + MX + disposable + role catches most dead
addresses with zero dependencies and zero spend. It cannot tell a real mailbox from a made-up
one on a live domain (that lead lands `unknown`), and it does not detect catch-all domains.
SMTP `RCPT TO` probing and a paid list are the upgrade.

## Paid upgrade path

A managed-retainer client funds real mailbox verification. Wire one provider, call it in place
of (or after) the free checker in `/lead-find` step 3b, and map its result onto the four
`email_status` values.

| provider | rough cost | notes |
|---|---|---|
| MillionVerifier | ~$0.0004 / verify | cheapest, bulk + real-time API |
| ZeroBounce | ~$0.0008 / verify | adds activity-score and abuse flags |
| NeverBounce | ~$0.001 / verify | real-time API, dedupe built in |

Key goes in `.env` as `EMAIL_VERIFIER_API_KEY` (commented in `.env.example`). Provider result
mapping: their `valid` -> `valid`, `catch-all`/`accept-all` -> `catchall`, `unknown` -> `unknown`,
everything else (`invalid`, `disposable`, `spamtrap`, `abuse`, `do-not-mail`) -> `invalid`.

## Per adapter

- **`airtable` (Gmail-sending, e.g. smart-ai-workspace):** the free checker is the verification
  step. `/lead-find` writes `email_status`; `/lead-outreach` re-reads it and re-runs the checker
  when the Activity Log shows no prior verification, then guards the Gmail send.
- **`instantly`:** Instantly verifies every lead on import as part of the campaign. `/lead-find`
  can skip `scripts/verify_email.py` for an `instantly` client and read Instantly's verification
  status back into `email_status` instead. `/lead-outreach` does not send for an `instantly`
  client (the campaign does), so the pre-send guard there is a no-op.
- **`hubspot` / `gohighlevel`:** stubs. When implemented, use the free checker unless the client
  funds a paid verifier.

## How `/lead-find` sets it

After enrichment, per surviving row:

1. `verify_email(email)` -> `email_status` + reason.
2. `invalid` **and the lead has a personal `linkedin_url`:** keep the ICP-band Stage, set
   `channel` to `linkedin` (drop `email`), `next_action` notes "email failed verification, LinkedIn only".
3. `invalid` **and no LinkedIn:** Stage `Nurture` regardless of score, `next_action` =
   "needs a valid contact, re-enrich or find another decision-maker". The record is still created
   so the company is not re-sourced, but it does not flow to outreach.
4. `valid` / `catchall` / `unknown`: no change to Stage from this check.

The reason string goes in the seeded Activity Log line.

## How `/lead-outreach` consumes it

Step 4, before the Gmail send, for an email-channel lead:

1. If the Activity Log shows no prior verification, run `verify_email(email)` now.
2. `invalid` -> skip the send. `next_action` -> "find new contact" (same as the bounce line),
   `append_activity` a dated line noting the skip and the reason. Stage is left as it was.
3. `unknown` -> send by default, log `unknown`. `allow_unknown=false` on the invocation skips it
   the same way as `invalid`.
4. `catchall` / `valid` -> send, log the status.

LinkedIn-channel leads are unaffected (no email is sent).
