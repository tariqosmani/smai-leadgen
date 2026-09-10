---
name: lead-report
description: "Weekly client-facing performance summary for the active client's outbound program. Sets a window (default last 7 days), pulls activity and pipeline metrics via the pipeline adapter (report_metrics + list_leads, plus Instantly campaign analytics for an instantly client), computes week-over-week deltas, reply and conversion rates, and pipeline value, writes a short plain-language narrative with one recommended focus for next week, and produces a branded Google Doc scorecard plus a one-time Airtable Interface spec for a live dashboard. Read-only on the pipeline. Honest about untracked metrics: Gmail sends have no open or click tracking and are never estimated."
---

# Lead Report

> Invoke with `/lead-report` (weekly, client-facing) or "run the weekly report". A reporting layer on top of `/lead-pipeline`, not a funnel stage. `/lead-pipeline` is the internal daily driver; `/lead-report` is the external weekly scorecard.

## Client config
Resolve the active client: a `client=<slug>` invocation arg wins, else `ACTIVE_CLIENT` in `.env`. Then read:
- `clients/<client>/identity.md`: business name + founder name (Doc title and branding), `crm_target`
- `clients/<client>/voice.md`: register for the narrative
- `clients/<client>/scoring.md`: ICP bands, only if a by-band line is shown

## Read first
- `docs/pipeline-contract.md`: the operations (`report_metrics`, `list_leads`) and the normalized lead fields
- `docs/pipeline-adapters/<crm_target>.md`: how those operations map for this client
- `.claude/skills/lead-pipeline/SKILL.md` **step 4**: the stage-count and conversion-rate method this skill reuses. Do not re-derive it, scope the same method to the report window.
- `references/metrics.md` (this skill): the exact definition and per-adapter derivation of every metric, the "not tracked" rules, the Deal Value handling, and the Airtable Interface spec.

## Config
Metrics come from the **pipeline adapter** for the active client's `crm_target` (`clients/<client>/identity.md`): `report_metrics(since)` + `list_leads`, mapped in `docs/pipeline-adapters/<crm_target>.md`. For `smart-ai-workspace` that is `airtable` (Airtable MCP `mcp__airtable__*`, base + table from `identity.md`).
For `crm_target: instantly`, also call campaign analytics per the adapter doc: `GET /api/v2/campaigns/analytics/overview?id=<campaign>&start_date=<since>&end_date=<until>` and `GET /api/v2/campaigns/analytics/daily` for per-day send counts.
Google Doc via `mcp__claude_ai_Google_Drive__create_file` (Google Doc), same pattern as `/lead-proposal`.

## Steps

### 1. Set the window
- Default: `until` = today, `since` = today minus 7 days.
- `since=YYYY-MM-DD` sets an explicit start (`until` stays today). `days=30` sets `since` = today minus 30.
- **Prior window** for week-over-week: the same-length window immediately before `since` (`prior_since` = `since` minus the window length; `prior_until` = `since`). Get its numbers from the last line of `clients/<client>/report-log.md`, else from a second `report_metrics` / analytics call for the prior dates. No prior data anywhere means run current-only and say "first report, no prior period to compare".

### 2. Pull the data
- `report_metrics(since)` via the adapter: `stage_counts`, `touches_since`, `replies_since`, and any conversion counts the target derives. A `null` count means the skill derives it from `list_leads` + `activity_log` (the `/lead-pipeline` step 4 fallback).
- `list_leads` with no filter via the adapter: every lead with `stage`, `channel`, `icp_score`, `next_action_date`, `activity_log`, `deal_value` (if that field exists on this client), `company`.
- `crm_target: instantly` only: the analytics calls above give `sent`, `open_count`, `reply_count`, `total_meeting_booked`, `total_opportunities`, `total_closed` for the exact window.
- Repeat for the prior window only where a prior `report-log.md` line is missing and the adapter can still supply the numbers.

### 3. Compute the metrics
Every definition and per-adapter derivation is in `references/metrics.md`. Three groups; show each metric's window value and the WoW delta wherever a prior value exists:
- **Activity:** emails sent, follow-ups sent, LinkedIn touches, opens + open rate (Gmail client: `not tracked (Gmail send)`), replies + reply rate, positive replies + positive-reply rate.
- **Pipeline:** new leads added, leads by stage (current snapshot), meetings booked (Call Booked transitions in window), proposals sent, deals won, pipeline value (sum of `deal_value` over `Call Booked` + `Proposal Sent`; `not set` when the field is absent or empty on every lead), win rate.
- **Conversion (window, `/lead-pipeline` step 4 method):** Contacted to Replied, Replied to Call Booked, Call Booked to Proposal Sent, Proposal Sent to Won. When the window is under 30 days, also show each as a trailing-90-day rate so a quiet week is not just zeros. Any rate with a denominator under 3 is shown as a raw count with "small sample", not a percentage.
Flag every metric that is unavailable for this client. Never estimate a `not tracked` value.

### 4. Write the narrative
3 to 5 plain-language sentences for the client to read, no jargon:
- what moved this week (the biggest real change, up or down),
- what is working (a metric that is healthy or improving),
- the single recommended focus for next week.
Honest: real numbers only, no projection stated as a result, name anything not tracked. Voice rules apply (no em dashes, no AI filler, `clients/<client>/voice.md` register). Never imply a client result that has not happened (`clients/<client>/offer.md` > What NOT to claim yet).

### 5. Build the Google Doc
`mcp__claude_ai_Google_Drive__create_file`:
- `title`: `{business name} - Outbound Report - week of {since as "Mon D, YYYY"}`
- `textContent`: the report body below. `contentMimeType: "text/markdown"` (converts to a Google Doc).

Sections in order:
1. **Summary** - the narrative, plus a 4-number headline: emails sent, replies, meetings booked, pipeline value.
2. **Activity** - a table: metric | this week | last week | change.
3. **Pipeline** - leads by stage, then the movement metrics (new leads, meetings booked, proposals sent, deals won, pipeline value, win rate).
4. **Conversion** - the 4 rates, window value and trailing-90-day value side by side.
5. **Next week** - the one recommended focus as 1 to 3 concrete actions.

No em dashes anywhere in the Doc. Commas, periods, colons only.

### 6. Log the run
Append one line to `clients/<client>/report-log.md` (create it with a `# Report log` header if missing):
`- {until} (since {since}): sent {n}, replies {n}, meetings {n}, proposals {n}, won {n} | snapshot {Qualified n / Contacted n / Replied n / Call Booked n / Proposal Sent n / Won n / Lost n} | pipeline value {$n or "not set"} | doc: {url}`
This line is next week's prior-window baseline. **The pipeline itself is not written.**

### 7. Report back
`Weekly report for {business name}, week of {since}: {doc url}. Headline: {n} sent, {n} replies, {n} meetings, pipeline value {value}. Focus next week: {one line}.`
Then stop. Tariq shares the Doc with the client himself (he does not want drafts touched or sent for him).

## First run for a client (optional, one time)
Offer to set up the live Airtable Interface dashboard from the spec in `references/metrics.md` > Airtable Interface spec. It is a convenience for the client between weekly Docs, not required, and it is a one-time setup, not a per-run step.

## Adapter differences
- **Gmail-sending client (`airtable` + Gmail, e.g. smart-ai-workspace):** opens and clicks are **not tracked** and never estimated. Sent and follow-up counts come from `Activity Log` `email touch N SENT` lines. Late-funnel transition dates come from dated `Activity Log` lines; a transition with no line still counts in the current snapshot but is flagged "transition date unknown" and left out of the windowed counts and WoW deltas.
- **Instantly client:** opens, open rate, sent, replies, meetings booked, and closed come from campaign analytics for the exact window and are reliable. Late-funnel stage (`Proposal Sent`, `Nurture`) comes from `custom_variables.stage`; pipeline value from `custom_variables.deal_value`. LinkedIn touches are not in Instantly (email-only) and show as "not available".

## Writes
- `clients/<client>/report-log.md`: append one line.
- One Google Doc.
- **Nothing in the pipeline.** No lead stage, field, or activity log is modified. `/lead-report` is read-only on the CRM.

## Idempotency
Re-running for the same window creates a fresh Doc and appends another log line with the same numbers. It never mutates leads, so re-runs are safe. To regenerate cleanly, remove the extra `report-log.md` line by hand.

## Delegate (optional)
Deeper funnel diagnostics, forecast modelling, or deal-risk analysis for a review meeting: `sales-pipeline-analyst`.
