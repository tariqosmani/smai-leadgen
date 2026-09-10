---
name: deliverability-monitor
description: "Recurring health check for the active client's cold-email sending infrastructure, run weekly or whenever reply rates drop. Reads what /inbox-setup provisioned (clients/<client>/infrastructure.md), then: counts bounce-backs against emails sent in the window (Gmail inbox scan for a Gmail-sending client, campaign analytics for an Instantly client), re-checks SPF / DKIM / DMARC / MX on every sending domain against the templates in inbox-setup/references/deliverability.md, checks each sending domain against the public DNSBLs with scripts/dnsbl_check.py, compares this window's reply rate to the prior window, and returns a GREEN / YELLOW / RED verdict with specific next actions and a DMARC tightening recommendation. Also takes an inbox-placement score (a placement=NN arg, Instantly analytics, or a seed test) and treats below 90% as RED. Read-only on the pipeline and on DNS. Appends one dated line to infrastructure.md. Companion to /inbox-setup (the one-time build) and /lead-report (the weekly client scorecard); not a funnel stage. Spam-complaint rate on a Gmail send is not tracked and is never estimated."
---

# Deliverability Monitor

> Invoke with `/deliverability-monitor` weekly, or when `/lead-pipeline` / `/lead-report` shows reply rate falling. Companion to `/inbox-setup` (one-time infra build) and `/lead-report` (weekly client scorecard). Not a funnel stage. Catches a sending problem before it burns the domains.

## Client config
Resolve the active client: a `client=<slug>` invocation arg wins, else `ACTIVE_CLIENT` in `.env`. Then read:
- `clients/<client>/identity.md`: business name, founder name, primary website domain, `crm_target`, from-email.
- `clients/<client>/infrastructure.md`: sending domains, mailboxes, mailbox provider, warmup finish date, and the previous `## Deliverability checks` lines. **If this file does not exist, print `run /inbox-setup first (no clients/<client>/infrastructure.md)` and stop.** The sending infrastructure has not been stood up, there is nothing to monitor.

Args: `since=YYYY-MM-DD` or `days=N` set the window start. `client=<slug>`.

## Read first
- `.claude/skills/inbox-setup/references/deliverability.md`: **the single source of every threshold** (bounce %, spam-complaint %, inbox placement, warmup health, auth), the DNS record templates, and the DMARC tighten path (`p=none` -> `p=quarantine` -> `p=reject`). This skill cites those numbers, it does not restate them. `Monitoring thresholds` table columns map to the verdict: **Healthy = GREEN, Warning = YELLOW, Pause sending = RED**.
- `docs/pipeline-contract.md`: `report_metrics(since)` (`touches_since` = emails sent in the window) and `list_leads`. Skills never call a CRM directly.
- `docs/pipeline-adapters/<crm_target>.md`: how those map for this client. Note: an Instantly client gets bounce + complaint + open + reply from campaign analytics; a Gmail-sending `airtable` client gets **no** open or complaint telemetry.
- `docs/outreach-playbook.md`: send window (Tue-Thu, 9-11am / 1-3pm local) and the `email touch N SENT` Activity Log convention.
- `.claude/skills/lead-pipeline/SKILL.md` **step 4**: the stage-count + conversion method. Reuse it for the reply-rate trend, scoped to the window. Do not re-derive it.

## Config
- **Pipeline metrics:** the **pipeline adapter** for `crm_target` (`report_metrics`, `list_leads`), mapped in `docs/pipeline-adapters/<crm_target>.md`. Read-only.
- **Bounce scan (Gmail-sending client):** Gmail MCP `mcp__claude_ai_Gmail__search_threads` on the connected `from-email` inbox.
- **Bounce + complaint (Instantly client):** `GET https://api.instantly.ai/api/v2/campaigns/analytics/overview?id=<INSTANTLY_CAMPAIGN_ID>&start_date=<since>&end_date=<today>` (Bearer `INSTANTLY_API_KEY`), per the instantly adapter doc.
- **DNS re-check:** `mcp__hostinger-dns__DNS_getDNSRecordsV1` per sending domain. **Read-only. Recommend fixes, never write DNS, that is `/inbox-setup`'s job.**
- **Blocklist:** `python scripts/dnsbl_check.py <domain> [<domain> ...]`.

## Steps

### 1. Window + inputs
- `since`: from the arg (`since=` / `days=`), else the date of the last `## Deliverability checks` line in `infrastructure.md`, else today minus 7.
- `until` = today. **Prior window** = the same-length window immediately before `since` (for the reply-rate trend in step 5).
- From `infrastructure.md`: the sending domains, the mailbox count, the mailbox provider (Google Workspace unless stated), the warmup finish date.
- `sending_domains` = the domains listed. If none are listed (Gmail-only, no dedicated sending domains bought yet), use the primary website domain from `identity.md` and say so.

### 2. Volume, bounce, complaint
- **Emails sent in window:** `report_metrics(since).touches_since` via the adapter (distinct `email touch N SENT` lines dated in `[since, until]`). Also note follow-ups vs first touches if cheap.
- **Gmail-sending client (airtable + Gmail, e.g. smart-ai-workspace):**
  - `mcp__claude_ai_Gmail__search_threads` with `from:mailer-daemon OR subject:"Delivery Status Notification" OR subject:"Undelivered Mail Returned to Sender" OR subject:"Delivery incomplete"` and `after:<since>`.
  - Count distinct bounce-back messages. `bounce_rate = bounces / emails_sent`.
  - **Spam-complaint rate: `not tracked (Gmail send)`.** Never estimate it, never infer it from replies or bounces.
  - Warmup health score: only if the client runs a warmup tool that exposes one; otherwise `not tracked (Gmail send)`. Inbox placement is its own step, step 6.
- **Instantly client:** from `analytics/overview` for the window: `bounce_rate = bounced_count / contacted_count`, `complaint_rate` from the complaint field if present, plus `open_count`, `reply_count`. These are reliable, use them directly.
- Report each rate with the band it falls in per `deliverability.md` > Monitoring thresholds (do not restate the numbers, cite the row).

### 3. Auth + DNS re-check (per sending domain, READ-ONLY)
`mcp__hostinger-dns__DNS_getDNSRecordsV1` for each sending domain, then compare to `deliverability.md` > DNS record templates for the client's mailbox provider:
- **SPF:** exactly one TXT on `@`, `v=spf1`, the correct `include:` for the provider, ends `~all`. Flag: missing, more than one SPF record, wrong include, `-all`/`+all`.
- **DMARC:** one TXT on `_dmarc`, has a `p=` policy. Record the current policy (`none` / `quarantine` / `reject`) for step 8.
- **DKIM:** the provider's record present (`google._domainkey` TXT for Google Workspace; selector CNAMEs for M365 / a cold-email provider).
- **MX:** matches the provider's expected host(s) and priority.
- **Redirect:** the sending domain still 301s to the primary site (a bare sending domain is a spam signal).
Output a small per-domain table (record, expected, found, OK/DRIFT). For any DRIFT: state the fix and that `/inbox-setup` (step 5 for SPF/DMARC/MX, step 7 for DKIM) applies it. This skill does not call `DNS_updateDNSRecordsV1`.

### 4. Blocklist check
`python scripts/dnsbl_check.py <each sending domain> <primary domain>`. It checks Spamhaus DBL + SURBL (domain-based) and Spamhaus ZEN / SpamCop / Barracuda (against each domain's A record) using only stdlib DNS.
- `LISTED` on a sending domain -> RED signal. Note which list. Spamhaus DBL especially: request delisting at the list's site after fixing the cause, and pause sending from that domain meanwhile.
- `BLOCKED` = the DNSBL refused the query (public resolver / rate limit), inconclusive. Re-run later or check by hand.
- `clean` across the board -> note it and move on.
- If DNSBL lookups ever stop working from the run environment, fall back to the manual check: MXToolbox blacklist lookup (`https://mxtoolbox.com/blacklists.aspx`) and Google Postmaster Tools domain reputation, and say so in the output.

### 5. Reply-rate trend (this window vs prior)
Reuse the `/lead-pipeline` step 4 method (Activity Log timestamps), scoped to the window:
- `reply_rate` = distinct leads that replied in `[since, until]` / distinct leads with an `email touch N SENT` line in `[since, until]`.
- Prior window: from the last `## Deliverability checks` line in `infrastructure.md` if it recorded a reply rate, else a second `report_metrics(prior_since)` pass. No prior data: say "first check, no trend".
- **A sharp reply-rate drop with send volume roughly flat is a deliverability signal even when bounce looks clean** (mail is landing in spam). Treat a drop of more than about a third, volume flat, as at least YELLOW.
- Denominator under 3 either window: show the raw count, not a percentage.

### 6. Inbox-placement score
One number: the share of campaign-style sends landing in the inbox, not spam. Source, in order:
- **`placement=NN` arg** - a seed-test result the operator ran and passed in. Use it as given.
- **Instantly client** - the campaign / mailbox deliverability score from Instantly analytics.
- **Gmail-sending client, no arg** - `not tracked (Gmail send)`. Prompt once:
  `run a seed test for a real number, see inbox-setup/references/deliverability.md > Inbox-placement test`.

Where a number exists, band it through `deliverability.md` > Monitoring thresholds, the "Inbox placement" row: **above 90% GREEN, 80 to 90% YELLOW, below 90% RED (pause sending)**. `not tracked` cannot raise or lower the verdict, note that it is unmeasured.

### 7. Verdict
Take the **worst** signal across steps 2 to 6, mapped through `deliverability.md` > Monitoring thresholds (Healthy = GREEN, Warning = YELLOW, Pause sending = RED):
- **Bounce rate** -> its band in the thresholds table.
- **Spam-complaint rate** -> its band (Instantly only; `not tracked` for Gmail, so it cannot raise the verdict, note that).
- **Auth (SPF + DKIM + DMARC all pass)** -> any fail is the Pause column: RED.
- **Blocklist** -> any confirmed `LISTED` on a sending domain: RED.
- **Reply-rate drop with flat volume** -> YELLOW (RED only if it coincides with a bounce or auth problem).
- **Inbox placement** -> its band per the "Inbox placement" row: below 90% is the Pause column, RED. `not tracked` does not affect the verdict.
- **Warmup health score** -> its band, where the client tracks it.

- **GREEN:** keep sending at current volume.
- **YELLOW:** slow down. Cut campaign volume (roughly halve it), extend warmup, tighten targeting / list hygiene, fix the flagged item, re-check in a few days.
- **RED:** pause campaign sends for the affected domain(s), keep warmup running, fix the cause (list hygiene, content, auth, delisting), resume at 50% for 3 days, then full. This mirrors `deliverability.md` > "On a pause".

### 8. Output
A short status block, then the verdict and actions:

```
Deliverability check - {business name} - {since} to {until}
Sending: {N} domain(s) [list], {M} mailboxes, {provider}. Warmup finished {date or "not yet: <date>"}.
Volume:   {sent} emails sent in window ({first-touch}/{follow-up})
Bounce:   {x.x}% ({bounces}/{sent})  [GREEN|YELLOW|RED per thresholds]
Complaints: not tracked (Gmail send)   |   {x.x}%  [band]   (Instantly)
Placement: {NN}%  [GREEN|YELLOW|RED per thresholds]   |   not tracked (Gmail send)
Auth:     per domain - SPF {ok|DRIFT} / DKIM {ok|DRIFT} / DMARC p={policy} / MX {ok|DRIFT}
Blocklist: {clean | LISTED on <list> for <domain>}
Reply rate: {this}% vs {prior}% ({+/-} pts)   [or "first check, no trend"]

VERDICT: {GREEN | YELLOW | RED}
Actions:
- {specific, ordered}
DMARC: currently p={policy on each domain}. {recommendation, see below}
```

**DMARC progression recommendation** (cite `deliverability.md` > DMARC): advance one step only, `p=none` -> `p=quarantine` -> `p=reject`, and only after **2+ weeks of clean, aligned traffic** (SPF + DKIM passing on every send, bounce in the healthy band, no blocklist hit). If this check is GREEN and the domain has held clean for 2+ weeks at the current policy, recommend the next step and note that `/inbox-setup` applies it. Otherwise: hold at the current policy and say why.

### 9. Log
Append one line to `clients/<client>/infrastructure.md` under a `## Deliverability checks` heading (add the heading at the end of the file if it is missing):

```
- {until} (since {since}): sent {n}, bounce {x.x}%, complaints {x.x}% or "n/t", placement {NN}% or "n/t", reply rate {x}% ({+/- pts} or "n/a"), auth {all pass | DRIFT: ...}, blocklist {clean | LISTED ...}, verdict {GREEN|YELLOW|RED}. Actions: {one line}.
```

This line is the next run's prior baseline. No em dashes. **Nothing else is written: not the pipeline, not DNS.**

## Writes
- `clients/<client>/infrastructure.md`: append one line (and the `## Deliverability checks` heading on first run).
- **Nothing else.** Read-only on the pipeline (adapter reads only) and on DNS (`DNS_getDNSRecordsV1` only).

## Idempotency
Re-running for the same window appends another dated line with the same numbers and creates no other change. Safe to re-run. Remove a duplicate line by hand if needed.

## Guardrail
A **RED** verdict means campaign sends pause for the affected domain(s) until the cause is fixed (CLAUDE.md > Guardrails). Warmup keeps running. `/lead-outreach` should not send for that client while the last recorded verdict is RED. An inbox-placement score below 90% is a RED signal on its own and pauses sending for the affected domain(s), same as a bounce or auth failure.

## Delegate (optional)
Whether cold email is still the right motion for this client, or a deeper channel-strategy rethink after a sustained RED: `sales-outbound-strategist`.
