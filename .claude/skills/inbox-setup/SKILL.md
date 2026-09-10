---
name: inbox-setup
description: "Stand up cold-email sending infrastructure for the active client so outreach lands in the inbox. Sizes the setup from a daily send target (domains, mailboxes, warmup) with scripts/inbox_math.py, generates sending-domain candidates from the client's primary domain, checks availability + price via the Hostinger domains MCP, buys them only after an explicit in-session yes, auto-creates SPF / DMARC / MX (then DKIM) and a redirect to the primary site via the Hostinger DNS MCP, outputs the exact Google Workspace or cold-email-provider mailbox steps, the Instantly / Smartlead warmup schedule and rotation config, then writes a client-ready handover doc and records what was provisioned in clients/<slug>/infrastructure.md. Run once when onboarding a client."
---

# Inbox Setup

> Invoke with `/inbox-setup` or "set up sending infrastructure". Client onboarding, run once. Not a funnel stage.

Produces a warmed, authenticated cold-email sending setup plus a handover doc. Order:
**size -> generate domain candidates -> check availability + price -> PURCHASE GATE -> buy -> DNS -> mailboxes (guided) -> connect + warm (guided) -> rotation -> handover -> record**.

## Client config
Resolve the active client: a `client=<slug>` invocation arg wins, else `ACTIVE_CLIENT` in `.env`. Then read:
- `clients/<client>/identity.md`: **business name**, **founder name**, **primary website domain**, secondary sending domains, `crm_target`.
- `clients/<client>/infrastructure.md` if it exists: what is already provisioned (this skill is re-runnable, never double-buy).

Args: `volume=50` (daily cold-send target; if absent, ask before sizing). `client=<slug>`.

## Read first
- `.claude/skills/inbox-setup/references/deliverability.md`: sizing rules + citations, DNS record templates, warmup schedule, rotation math, monitoring thresholds. Every value below comes from here.
- `docs/outreach-playbook.md`: send-day / send-window rules the rotation must match.

## Config
- **Sizing:** `python scripts/inbox_math.py <volume>` -> domains, mailboxes, sends/mailbox/day, warmup weeks.
- **Domains + DNS:** Hostinger MCPs. Availability `mcp__hostinger-domains__domains_checkDomainAvailabilityV1`. Price + `item_id` `mcp__hostinger-billing__billing_getCatalogItemListV1` (prices are in cents; `first_period_price` = year 1, `price` = renewal). Purchase `mcp__hostinger-domains__domains_purchaseNewDomainV1`. DNS `mcp__hostinger-dns__DNS_updateDNSRecordsV1` / `_validateDNSRecordsV1` / `_getDNSRecordsV1`. Redirect `mcp__hostinger-domains__domains_createDomainForwardingV1`.
- **Mailboxes + warmup:** not automatable by us. The skill outputs exact steps; the client or Tariq does them in Google Workspace / the mailbox provider and in Instantly or Smartlead.
- **Handover doc:** `mcp__claude_ai_Google_Drive__create_file` (Google Doc). Fallback: a Markdown file in `clients/<client>/`.

## HARD money guardrail (blocking)
**Never call `domains_purchaseNewDomainV1` without an explicit in-session "yes" to a shown total.**
A default payment method on the Hostinger account means a purchase call settles real money immediately. Step 4 is a stop. No yes in the transcript -> no purchase, full stop. "Buy the domains" earlier in the conversation does not count; the yes must follow the itemised total in Step 4. If in doubt, stop and ask.

## Steps

### 1. Inputs
- `volume`: from the arg, else ask "daily cold-send target?" and wait.
- `primary_domain`, `business_name`, `founder_name`: from `clients/<client>/identity.md`.
- If `clients/<client>/infrastructure.md` lists domains already bought, treat those as done and only fill the gap.

### 2. Sizing
Run `python scripts/inbox_math.py <volume>`. Report the four numbers in a line:
`volume 50/day -> 1 domain, 2 mailboxes, 25 sends/mailbox/day, 3-week warmup`.
If `volume` needs more domains than the client wants to buy now, say so and offer the volume that N domains supports (N x ~105/day).

### 3. Domain candidates + availability + price
Derive 5-10 sending-domain candidates from `primary_domain` (root = the primary's second-level label). Patterns, `.com` first (cold-email default; `.co` / `.io` / `.net` only if every `.com` is taken, and flag their higher renewal):
`get<root>.com` · `try<root>.com` · `<root>-team.com` · `<root>-hq.com` · `<root>hq.com` · `join<root>.com` · `<root>app.com` · `with<root>.com` · `the<root>.com` · `<root>-mail.com`
Keep them readable and close to the brand. Skip hyphen-heavy or long ones if cleaner options pass.

For each candidate: `domains_checkDomainAvailabilityV1`. For each **available** one, get the price from `billing_getCatalogItemListV1` (`name` filter e.g. `.COM*`); record `item_id` (the `*-usd-1y` price id), year-1 price, renewal price.

Present a shortlist of the N cheapest clean available domains (N = domains needed from Step 2), plus 1-2 spares:

```
Need 2 sending domains for 200/day.
  getsmartaiworkspace.com    $9.99 yr1 / $19.99 renew   available
  trysmartaiworkspace.com    $9.99 yr1 / $19.99 renew   available
  smartaiworkspace-hq.com    $9.99 yr1 / $19.99 renew   available  (spare)
Total to buy 2: $19.98 now, ~$39.98/yr renewal.
```

### 4. Purchase gate (STOP)
Show: the exact domains to buy, year-1 total, renewal total. Then wait for an explicit "yes".
- **No yes -> stop here.** Everything above (availability, price) is done and useful on its own.
- **Yes ->** for each domain: confirm a WHOIS profile covers the TLD (`domains_getWHOISProfileListV1`; `.com` needs a generic/`com` profile, create one with `domains_createWHOISProfileV1` if missing), then `domains_purchaseNewDomainV1(domain, item_id)` (uses the account default payment method).
  - Response `200` -> registered.
  - Response `202` -> **payment still processing, domain NOT registered.** Tell Tariq to finish the order in hPanel (<https://hpanel.hostinger.com/>), then re-run this skill (Step 1 skips what is already bought).
  - Error (no payment method, TLD needs `additional_details`, WHOIS missing) -> report it, give the manual steps: buy the listed domains in hPanel, point them at Hostinger nameservers, re-run this skill from Step 5.

### 5. DNS (per purchased domain)
Templates and exact values: `references/deliverability.md` > DNS record templates. Assume Google Workspace unless Tariq names a different mailbox provider.
1. `DNS_getDNSRecordsV1` -> see what the registrar pre-populated.
2. Build the zone: SPF (TXT `@`), DMARC (TXT `_dmarc`, `p=none` to start), MX (`@`). `DNS_validateDNSRecordsV1` first, then `DNS_updateDNSRecordsV1` with `overwrite=true` for the SPF / DMARC / MX names so a pre-populated record does not collide.
3. `domains_createDomainForwardingV1(domain, "301", "https://<primary_domain>")`.
4. DKIM is added in Step 7, after the mailbox provider issues the key.
Report each domain's records as a table for the handover doc.

### 6. Mailboxes (guided, output steps)
Per domain, `sends_per_mailbox` count aside, create the mailbox count from Step 2 (2-3/domain). Output the exact steps:
- **Google Workspace (1-2 domains, simplest):** add each sending domain to one Workspace account as a secondary domain (Admin > Domains > Manage domains > Add), verify the TXT, create users. One Business Starter seat (~$7/user/mo) per mailbox.
- **Dedicated cold-email provider (3+ domains, lowest cost):** Maildoso / Mailreef / Hypertide / Instantly-managed domains. They provision mailboxes + set DNS; you either delegate the nameservers or paste the records they give. ~$2-4/mailbox/mo.
- **Naming:** real-person addresses only. `firstname@` and `firstname.lastname@` using the founder (`founder_name`) and any real team members. Never `info@`, `sales@`, `hello@`, `team@` (role addresses = spam signal, and `/lead-find` suppresses them anyway).
- Set the display name to the person, "First Last".

### 7. DKIM
Once the provider issues the DKIM key(s) per mailbox/domain, add them via `DNS_updateDNSRecordsV1` (TXT for Google `google._domainkey`, CNAMEs for M365 / providers). Validate first. Re-check that SPF, DKIM, DMARC all pass (provider's auth checker or a seed test) before any sending.

### 8. Connect + warm (guided, output settings)
Per mailbox, in Instantly or Smartlead:
- Add the mailbox (Google OAuth, or IMAP/SMTP with an app password).
- Enable warmup with the settings in `references/deliverability.md` > Warmup schedule: gradual ramp on, max 40/day, reply rate 30%, weekdays only.
- Give the 3-week ramp table and the "campaign sends start week 4" rule.
- Compute the **warmup finish date** = today + `warmup_weeks` (7 x weeks days) and put it in the handover.

### 9. Rotation
In the sending tool: attach all mailboxes to one campaign / sending group.
- Per-mailbox daily limit = `sends_per_mailbox_per_day` from Step 2 (cap 40).
- Campaign daily cap = ~85% of (mailboxes x per-mailbox limit).
- Min delay between sends 8-15 min randomised; send window Tue-Thu 9-11am / 1-3pm prospect-local (`docs/outreach-playbook.md`).
- Give the capacity math: `mailboxes x per-mailbox = total/day`.

### 10. Handover doc
Create a Google Doc (`Google_Drive__create_file`, title `{business_name} - Cold Email Infrastructure Handover ({YYYY-MM-DD})`), fallback `clients/<client>/handover-inbox-setup-{YYYY-MM-DD}.md`. Contents:
- The sizing line and what it means.
- Every sending domain, with year-1 + renewal cost and renewal date.
- Every mailbox address and its provider.
- Every DNS record per domain (name, type, value) and the redirect target.
- Warmup finish date; "no campaign sends before this date".
- Rotation config (per-mailbox limit, campaign cap, window).
- Monitoring thresholds table (`references/deliverability.md`): bounce < 2%, spam complaints < 0.3%, pause if inbox placement < 90%; and the DMARC tighten path (`p=none` -> `p=quarantine` -> `p=reject`).
- Voice rules apply to any prose in the doc: no em dashes.

### 11. Record it
Create or append `clients/<client>/infrastructure.md`:
```
## Cold email infrastructure

### Provisioned YYYY-MM-DD (target: NN sends/day)
- Sending domains: getX.com, tryX.com  (Hostinger, renew YYYY-MM-DD, $19.99/yr each)
- Mailboxes: first@getX.com, first.last@getX.com, first@tryX.com, ...  (Google Workspace)
- DNS: SPF + DMARC(p=none) + MX + DKIM set on all; each 301 -> https://<primary_domain>
- Warmup: Instantly, started YYYY-MM-DD, campaign-ready YYYY-MM-DD
- Handover: <doc link or file path>
```
Append, never overwrite, on a re-run.

### 12. Report
`Sized NN/day -> D domains, M mailboxes. Checked A domains (price $X). [Bought B / awaiting your yes / awaiting hPanel]. DNS set on B. Mailbox + warmup steps below. Handover: <link>. Campaign-ready <date>.`

## Idempotency
Re-runnable. Step 1 reads `infrastructure.md` and skips domains already bought; DNS writes validate-then-`overwrite` so re-applying is safe; the handover and the `infrastructure.md` entry are dated and appended. A `202` purchase or a missing payment method is the normal reason to re-run after Tariq finishes in hPanel.

## What the Hostinger MCP does / does not do autonomously
- **Does:** domain availability, catalog price + `item_id`, DNS record create / validate / read, domain forwarding, WHOIS profile create. Domain **purchase** settles autonomously *when a default payment method exists on the account* (it does).
- **Does not / may not:** a `202` means the charge is processing and the domain is not registered (finish in hPanel). A TLD that needs `additional_details`, or a missing WHOIS profile for the TLD, fails the purchase call. Nameserver / propagation delays mean DNS and mailbox verification can lag minutes to hours.

## Delegate (optional)
Channel strategy / whether cold email is even the right motion for this client -> `sales-outbound-strategist`.
