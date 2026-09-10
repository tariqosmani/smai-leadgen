---
name: lead-pipeline
description: "Daily driver and health check for the active client's lead pipeline. Reads all leads via the pipeline adapter and reports today's actions (leads due for a touch, replies waiting, proposals to chase), flags stale and cold leads, shows stage counts and conversion rates, and recommends the single next move. Read-only except for lapsing dead leads (with confirmation)."
bike-method-phase: 3
---

# Lead Pipeline

> Invoke with `/lead-pipeline` at the start of the workday, or "pipeline status". Full funnel stage 3 of 5.

## Client config
Resolve the active client: a `client=<slug>` invocation arg wins, else `ACTIVE_CLIENT` in `.env`. Then read:
- `clients/<client>/scoring.md`: tie-breakers
- `clients/<client>/identity.md`: CRM target + (for an `airtable` client) the base ID + table name

## Read first
- `docs/pipeline-contract.md`: the operations and lead fields
- `docs/pipeline-schema.md`: field reference (Airtable layout), stages, ICP bands

## Config
Pipeline reads and writes go through the **pipeline adapter** for the active client's `crm_target`
(`clients/<client>/identity.md`): operations in `docs/pipeline-contract.md`, mapping in
`docs/pipeline-adapters/<crm_target>.md`. For `smart-ai-workspace` that is `airtable` (Airtable MCP
`mcp__airtable__*`).

## Steps

### 1. Read the table
`list_leads` with no filter (all records) via the pipeline adapter. Read each record's `stage`, `icp_score`, `channel`, `next_action_date`, and `activity_log`.

### 2. Today's list (most valuable first)
- **New replies** — any `Contacted` lead may have an inbound reply the cadence has not caught. → "run `/lead-replies`" (it reads each reply thread and routes it: stage, suppression, nurture date, booking draft)
- **Replies waiting** — Stage `Replied` (routed there by `/lead-replies`). → book the discovery call (`clients/<client>/offer.md` Pricing method §1); a booking-link draft may already be in Gmail. Once the time is set, move the lead to `Call Booked` with an expected `deal_value` (`/lead-replies` > When the call gets booked)
- **Calls booked** — Stage `Call Booked`. → after the call, paste notes into the record, run `/lead-proposal`
- **Proposals to chase** — Stage `Proposal Sent`, `Next Action Date` ≤ today
- **Due for a touch** — Stage `Qualified`, or `Contacted` + `Next Action Date` ≤ today + <5 emails in `Activity Log`. → "run `/lead-outreach`"

### 3. Health flags
- **Stale:** `Next Action Date` > 5 days past → list them
- **Cold:** Stage `Contacted`, ≥5 touches, last `Activity Log` entry > 90 days → propose Stage `Lost`. Show list, confirm before writing.
- **Thin top of funnel:** `Qualified` + un-actioned count < 10 → "run `/lead-find`"
- **No contact:** `Qualified` record with no `Email` and no `LinkedIn` → "need a contact for X"

### 4. Numbers
Count by `stage`. Conversion over the last 60 days from `activity_log` timestamps:
`Contacted→Replied`, `Replied→Call Booked`, `Call Booked→Proposal Sent`, `Proposal Sent→Won`.
Flag if `Contacted→Replied` < 5% (message or targeting problem) or 0 leads added in 7 days.
(This is the `report_metrics` operation. Some adapters serve it natively, see `docs/pipeline-contract.md`; on `airtable` it is derived from the records already read in Step 1.)

### 5. One recommendation
The single highest-leverage next action given the state (e.g. "2 replies sitting 3 days. Answer those before any new outreach.").

## Writes
Only step 3's cold-lead lapsing (`set_stage` → `Lost` via the pipeline adapter), after Tariq confirms the list. Otherwise read-only.

## Delegate (optional)
Deeper funnel diagnostics / forecast → `sales-pipeline-analyst`.
