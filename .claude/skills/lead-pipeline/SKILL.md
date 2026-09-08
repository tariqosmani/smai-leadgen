---
name: lead-pipeline
description: "Daily driver and health check for the Smart AI Workspace lead pipeline in Airtable. Reads the Lead Pipeline table and reports today's actions (leads due for a touch, replies waiting, proposals to chase), flags stale and cold leads, shows stage counts and conversion rates, and recommends the single next move. Read-only except for lapsing dead leads (with confirmation)."
bike-method-phase: 3
---

# Lead Pipeline

> Invoke with `/lead-pipeline` at the start of the workday, or "pipeline status". Full funnel stage 3 of 5.

## Read first
`docs/pipeline-schema.md` (fields, stages, ICP bands), `docs/scoring.md` (tie-breakers).

## Config
`AIRTABLE_BASE_ID`, `AIRTABLE_TABLE`. Pipeline = **Airtable MCP** (`mcp__airtable__*`).

## Steps

### 1. Read the table
`mcp__airtable__list_records` on the `Lead Pipeline` table (all records). Read each record's `Stage`, `ICP Score`, `Channel`, `Next Action Date`, and `Activity Log`.

### 2. Today's list (most valuable first)
- **Replies waiting** — Stage `Replied`. → "book the discovery call (pricing-playbook §1)"
- **Calls booked** — Stage `Call Booked`. → after the call, paste notes into the record, run `/lead-proposal`
- **Proposals to chase** — Stage `Proposal Sent`, `Next Action Date` ≤ today
- **Due for a touch** — Stage `Qualified`, or `Contacted` + `Next Action Date` ≤ today + <5 emails in `Activity Log`. → "run `/lead-outreach`"

### 3. Health flags
- **Stale:** `Next Action Date` > 5 days past → list them
- **Cold:** Stage `Contacted`, ≥5 touches, last `Activity Log` entry > 90 days → propose Stage `Lost`. Show list, confirm before writing.
- **Thin top of funnel:** `Qualified` + un-actioned count < 10 → "run `/lead-find`"
- **No contact:** `Qualified` record with no `Email` and no `LinkedIn` → "need a contact for X"

### 4. Numbers
Count by Stage. Conversion over the last 60 days from `Activity Log` timestamps:
`Contacted→Replied`, `Replied→Call Booked`, `Call Booked→Proposal Sent`, `Proposal Sent→Won`.
Flag if `Contacted→Replied` < 5% (message or targeting problem) or 0 leads added in 7 days.

### 5. One recommendation
The single highest-leverage next action given the state (e.g. "2 replies sitting 3 days. Answer those before any new outreach.").

## Writes
Only step 3's cold-lead lapsing (`update_records` → `Stage` = `Lost`), after Tariq confirms the list. Otherwise read-only.

## Delegate (optional)
Deeper funnel diagnostics / forecast → `sales-pipeline-analyst`.
