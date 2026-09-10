# Deliverability reference

Sizing rules, DNS record templates, warmup schedule, and monitoring thresholds for
`/inbox-setup`. `scripts/inbox_math.py` encodes the sizing math; this file is the
source it is derived from.

## Sizing rules (2026 consensus)

| Rule | Value used | Source range |
|---|---|---|
| Cold sends/day per **warmed** mailbox | **35** | 30-50 (Smartlead), 30-50 "safe ceiling" Google/M365 (outbound-system, scaledmail), task brief says 30-40 |
| Mailboxes per sending domain | **3** | 2-3 (every source) |
| Sends/day per domain | ~105 | ~100 (500/day tier = 5 domains, MailTester / howmanycoldemailsperday) |
| Warmup before first campaign send | **3 weeks** | 2-4 weeks (Instantly), 2-3 weeks (Smartlead), 30 days min for a brand-new domain (Smartlead) |
| Warmup start volume | ~5/day, ramp +3-5/day | 5-10 start (Smartlead, general best practice) |
| Keep the primary domain out of cold sending | always | universal: cold volume burns reputation, never risk the domain that runs the real site + transactional mail |

Formula (`inbox_math.py`):

```
mailboxes = ceil(volume / 35)
domains   = ceil(mailboxes / 3)
per_mailbox_per_day = ceil(volume / mailboxes)   # even split, always <= 35
warmup    = 3 weeks
```

Worked examples:

| Daily volume | Domains | Mailboxes | Sends/mailbox/day | Warmup |
|---|---|---|---|---|
| 50  | 1 | 2  | 25 | 3 wk |
| 100 | 1 | 3  | 34 | 3 wk |
| 200 | 2 | 6  | 34 | 3 wk |
| 500 | 5 | 15 | 34 | 3 wk |

Sources (retrieved 2026-09-10):
- <https://mailtester.com/blog/cold-email-infrastructure-calculator-domains-mailboxes-volume/>
- <https://outboundsystem.com/blog/cold-email-infrastructure-setup>
- <https://www.scaledmail.com/blogs/cold-email-infrastructure-guide>
- <https://www.smartlead.ai/blog/email-warm-up-guide> and <https://www.smartlead.ai/blog/how-many-cold-emails-per-day>
- <https://instantly.ai/blog/scaling-email-warm-up/>
- <https://blog.101domain.com/dmarc/microsoft-cold-email-policy-2026> (DMARC p=reject as the 2026 inbox-placement default)

## DNS record templates

Placeholders: `SENDING_DOMAIN` = the cold-email domain (e.g. `getexample.com`),
`PRIMARY_DOMAIN` = the client's real site (e.g. `example.com`), `DKIM_SELECTOR` /
`DKIM_VALUE` = issued by the mailbox provider after the mailbox exists.

All records go on the sending domain's zone, which is on Hostinger nameservers when
the domain is bought through Hostinger (so the Hostinger DNS MCP can write them).
Create SPF + DMARC + MX right after purchase; add DKIM once the provider issues it.

### SPF (TXT, name `@`, one record only)

| Mailbox provider | content |
|---|---|
| Google Workspace | `v=spf1 include:_spf.google.com ~all` |
| Microsoft 365 | `v=spf1 include:spf.protection.outlook.com ~all` |
| Cold-email provider | use the exact `include:` the provider gives; still one record, still ends `~all` |

Never publish two SPF TXT records on one name. If the provider needs an extra
include, merge it into the single record.

### DMARC (TXT, name `_dmarc`)

Create with `p=none` (monitor only, cannot hurt mail):

```
v=DMARC1; p=none; rua=mailto:dmarc@PRIMARY_DOMAIN; fo=1; adkim=s; aspf=s
```

After ~1 week of clean aggregate reports (SPF + DKIM aligning, warmup healthy),
tighten in the sending tool's DNS or via the DNS MCP:

```
v=DMARC1; p=quarantine; rua=mailto:dmarc@PRIMARY_DOMAIN; fo=1; adkim=s; aspf=s
```

then, once quarantine is clean, `p=reject` (the 2026 inbox-placement default at
Google / Yahoo / Microsoft; `p=quarantine` is the documented minimum bar).

### MX

| Mailbox provider | records (name `@`) |
|---|---|
| Google Workspace | `1 smtp.google.com` |
| Microsoft 365 | `0 SENDING_DOMAIN-com.mail.protection.outlook.com` (value from the M365 admin center) |
| Cold-email provider | the provider's MX host(s), priorities as given |

TTL 3600 is fine for all of the above.

### DKIM (added after the mailbox provider issues the key)

| Provider shape | record |
|---|---|
| Google Workspace | TXT, name `google._domainkey`, content `v=DKIM1; k=rsa; p=DKIM_VALUE` (generate the 2048-bit key in Admin console > Apps > Google Workspace > Gmail > Authenticate email) |
| Microsoft 365 | 2x CNAME, `selector1._domainkey` and `selector2._domainkey` pointing to the `*.onmicrosoft.com` targets M365 shows |
| Cold-email provider | usually 1-3 CNAMEs like `provider-a._domainkey` -> `...provider.com.`; paste exactly as given |

### Redirect the sending domain to the primary site

A bare sending domain with no website is a spam signal. 301 the root to the real site:

- Hostinger domains MCP: `createDomainForwardingV1(domain=SENDING_DOMAIN, redirect_type="301", redirect_url="https://PRIMARY_DOMAIN")`.
- Web forwarding is HTTP-level and coexists with the MX records above.

## Warmup schedule (enter in Instantly / Smartlead)

Per mailbox. Warmup runs inside the sending tool and cannot be automated by us.

| Week | Warmup emails/day | Daily increase | Reply rate | Campaign sends |
|---|---|---|---|---|
| 1 | 5 -> 12 | +1-2/day | 25-35% | none |
| 2 | 14 -> 26 | +2-3/day | 25-35% | none |
| 3 | 28 -> 40 | +2-3/day | 25-35% | none |
| 4+ | hold ~20-30 (keep warmup on permanently) | - | 20-30% | ramp real sends: +5/mailbox/day up to the per-mailbox cap |

Settings to set explicitly:
- Warmup enabled, "gradual ramp-up" / "auto-increase" on.
- Max warmup emails/day: 40.
- Reply rate: 30%.
- Mark as important / archive: on.
- Custom warmup pool: default (provider pool) is fine.
- Weekdays only for both warmup and sending.

## Inbox rotation

All mailboxes attach to one campaign / one sending account group in the tool. The
tool round-robins sends across them.

- Per-mailbox daily send limit = `sends_per_mailbox_per_day` from `inbox_math.py`
  (25-35). Never raise above 40.
- Total daily capacity = mailboxes x per-mailbox limit. Keep the campaign's daily
  cap at ~85% of that so no mailbox runs to its ceiling.
- Min delay between sends: 8-15 min, randomised ("wait time" / "random interval").
- Daily send window: the prospect's business hours (playbook: Tue-Thu, 9-11am or
  1-3pm local).
- One mailbox flagged unhealthy (see thresholds) -> pause just that mailbox; the
  rotation absorbs it. Do not raise the others to compensate.

## Monitoring thresholds (put in the handover doc)

Check weekly for the first month, then monthly.

| Metric | Healthy | Warning | Pause sending |
|---|---|---|---|
| Bounce rate | < 2% | 2-5% | > 5% |
| Spam complaint rate | < 0.1% | 0.1-0.3% | > 0.3% |
| Inbox placement (seed test / tool score) | > 90% | 80-90% | < 90% |
| Warmup health score (Instantly/Smartlead) | > 95% | 90-95% | < 90% |
| Google Postmaster domain reputation | High / Medium | Low | Bad |
| Auth (SPF + DKIM + DMARC all pass) | 100% | any fail | any fail |

On a pause: stop campaign sends for that domain, keep warmup running, fix the cause
(list hygiene, content, auth), resume at 50% volume for 3 days, then full.
