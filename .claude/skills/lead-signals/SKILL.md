---
name: lead-signals
description: "Re-scan the active client's existing pipeline for fresh buying signals and re-activate the leads whose situation changed. Reads Qualified / Nurture / Contacted leads via the pipeline adapter, and for each one queries Explorium events (funding, decision-maker job change, hiring spike, tech-stack adoption, buying intent) on the company domain since the lead's last activity date. A new signal writes the Signal field, appends a dated Activity Log line, and for a Nurture lead or a cold Contacted lead sets a re-touch for today. The retainer differentiator: we watch your pipeline for buying signals. Companion to /lead-find, not a funnel stage. Event lookups cost Explorium credits, so it shows an estimate for the batch and waits for an explicit yes, same gate as /lead-find."
---

# Lead Signals

> Invoke with `/lead-signals` (or "re-scan the pipeline for buying signals"), weekly or after a `/lead-find` refill. Companion to `/lead-find`. Not a funnel stage: it does not source new leads, it re-reads the ones already in the pipeline and re-queues the ones a fresh event makes worth another touch.

## Client config
Resolve the active client: a `client=<slug>` invocation arg wins, else `ACTIVE_CLIENT` in `.env`. Then read:
- `clients/<client>/identity.md`: business name, `crm_target` (for an `airtable` client: the base ID + table name)
- `clients/<client>/offer.md`: the service lines and intent topics a signal ties to
- `clients/<client>/scoring.md`: the Automation-intent dimension a signal feeds

Args: `days=N` overrides the per-lead lookback (default: since the lead's last Activity Log date). `client=<slug>`.

## Read first
- `docs/signal-catalog.md`: the signal types, the Explorium event keys, the `signal` string templates, and what a fresh signal does downstream. This skill is the pipeline-rescan half of that doc.
- `docs/pipeline-contract.md`: `list_leads`, `update_lead`, `append_activity`, and the normalized fields. Skills never call a CRM directly.
- `docs/pipeline-adapters/<crm_target>.md`: how those operations map for this client.
- `docs/outreach-playbook.md` > Logging: the dated Activity Log line convention.
- `scripts/normalize.py`: the company-domain normalizer, the key events are queried on.

## Config
- **Pipeline:** the pipeline adapter for `crm_target` (`clients/<client>/identity.md`), operations `list_leads` / `update_lead` / `append_activity`. Read plus the writes in `## Writes`, nothing else.
- **Events:** the Vibe Prospecting MCP (`mcp__claude_ai_Vibe_Prospecting__*`): `match-business` to resolve the pipeline's company domains to Explorium business tables, `match-prospects` for the contacts, then `fetch-businesses-events` (funding, hiring, tech-stack change) and `fetch-prospects-events` (job change) with `timestamp_from` = the lookback date. Event keys per `docs/signal-catalog.md`.

## Steps

### 1. Pull the re-scan set
`list_leads` filtered to `stage` in `Qualified`, `Nurture`, `Contacted`. Exclude `Replied`, `Call Booked`, `Proposal Sent`, `Won`, `Lost`, `Disqualified`: a live conversation or a closed-out lead is not re-activated by a signal. Drop rows with no company domain (nothing to query).

### 2. Estimate + gate (credits)
Event lookups cost Explorium credits like any enrichment. Show the batch estimate:
```
Re-scan {N} leads for fresh signals (funding, job-change, hiring, tech-stack, intent).
Lookback: {per-lead last activity | days=N}. Est. ~{X} credits.
Proceed?
```
Wait for an explicit yes. Demo / no-spend mode: this is a hard gate, nothing queries autonomously. On no, stop.

### 3. Query events per lead
Keyed on the normalized company domain (`scripts/normalize.py`):
- `timestamp_from` = the `days=N` date if given, else the date of the lead's last Activity Log line, else today minus 90.
- `match-business` the domains (batches of 50) → `fetch-businesses-events` for `new_funding_round,new_investment,ipo_announcement`, the `hiring_in_<dept>_department` / `increase_in_<dept>_department` keys, plus an `enrich-business` technographics check for a stack change.
- `match-prospects` the contacts (email, or full name + company) → `fetch-prospects-events` for `prospect_changed_role,prospect_changed_company`.
- Take the most recent qualifying event per lead. Compose the `signal` string per `docs/signal-catalog.md` template.

### 4. Write the matches
For each lead with a new signal (see `## Idempotency` for what counts as new):
- `update_lead`: set `signal` to the composed string.
- `append_activity`: `YYYY-MM-DD: new signal detected - <string>`.
- **`Nurture` lead, or `Contacted` with no touch in the last 21 days:** also `update_lead` `next_action` = "fresh signal, re-touch" and `next_action_date` = today. This is the re-activation.
- **`Qualified` lead:** the signal and the Activity Log line only. It is already queued for outreach, do not touch its date.
- No score rewrite here. `/lead-outreach` and the next `/lead-find` re-score read the signal; this skill only records it.

### 5. Report
Leads re-scanned, signals found by type, leads re-activated (Nurture + cold Contacted) vs signal-only (Qualified), and **credits spent + remaining**. Then: "Next: `/lead-outreach` picks up the re-activated leads on their new date."

## Writes
Via the pipeline adapter, on matched leads only:
- `signal`
- `activity_log` (one appended line)
- `next_action` + `next_action_date` (Nurture leads and cold Contacted leads only)

Nothing else. No stage change, no score change, no new lead records, no DNS, no email.

## Idempotency
Re-running re-queries Explorium (the credit gate applies each time). If the composed `signal` string already equals what is on the lead, skip it: no Activity Log line, no date bump. A genuinely new event (a different round, a later hire, a newer tool) writes and re-activates as normal. Safe to re-run.

## Delegate (optional)
Turning a signal into a tailored outreach sequence, or a signal-to-play playbook: `sales-outbound-strategist`.
