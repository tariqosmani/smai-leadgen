---
name: lead-proposal
description: "Draft a three-option fixed-scope proposal for a Smart AI Workspace lead after the discovery call. Takes discovery-call notes (pasted, or from the Airtable lead record), applies the value-based pricing method from the pricing playbook, and produces a Google Doc with current state, desired outcome, Essential/Growth/Scale options, milestones and payment events, run-cost estimate, and measurement plan. Does not invent numbers the client hasn't given."
bike-method-phase: 2
---

# Lead Proposal

> Invoke with `/lead-proposal Acme` or "draft the proposal for Acme". Full funnel stage 4 of 5.

## Read first
- `references/pricing-playbook.md` — **the whole method.** Especially §1 (discovery), §2 (value model), §3 (corridor), §4 (three options), §5 (milestones).
- `references/voice.md`, `references/portfolio.md`

## Config
`AIRTABLE_BASE_ID`, `AIRTABLE_TABLE`. Google Doc via `mcp__claude_ai_Google_Drive__create_file` (or the `gws docs` CLI if authed).

## Steps

### 1. Gather inputs
Find the lead's Airtable record (by company name via `mcp__airtable__search_records`). Pull discovery notes
from the record's `Activity Log` / `Signal` / `Hook`. If notes are thin, ask Tariq to paste the call notes.
You need, at minimum:
- the business problem in the client's words
- the current process (trigger → steps → decisions → result) and the constraint step
- their numbers: volume, time per item, people involved, frequency, cost of failure
- who owns the decision, the access, and "success"
- deadline / why now

**If the value inputs are missing, stop and list what's needed.** Do not fabricate a value model (pricing-playbook: "never by inventing value").

### 2. Build the first-year value model (pricing-playbook §2)
With the client's numbers only. Label every assumption. Apply confidence adjustment (high/med/low). No double counting — pick the most defensible primary model, rest is upside.

### 3. Price the corridor (§3)
Cost floor (delivery + risk + margin) ↔ value ceiling (confidence-adjusted first-year value). Starting price 10–20% of credible value. Run the 10X check and the margin check. If value ceiling < cost floor → **no deal at this scope**: recommend shrinking the outcome or paid discovery, don't force a number.

### 4. Three options (§4)
Essential / Growth (recommended) / Scale. Each solves a different-sized problem. Map to services (`workflow`, `crm`, `data`, `agents`). Middle option designed to win; lower option genuinely useful; upper option a real buyer.

### 5. Write the Google Doc
Order (pricing-playbook §4 "Proposal order"): current state (their words + numbers) → desired future state + business result → why founder-led / relevant portfolio proof → the three options with scope, assumptions, exclusions → milestones + payment events (§5, pay at signing then ~every 30 days, objective milestones) → estimated monthly run cost + volume assumption (§8, client-owned credentials) → measurement plan (§9, baseline + 3–5 metrics) → commercial terms note (MSA + SoW).

Create the doc (`Google_Drive__create_file`, type Google Doc, title `Smart AI Workspace — Proposal for {Company} ({YYYY-MM-DD})`), then write the sections. Voice rules apply (no em dash, no hype). Reference ranges in pricing-playbook are a **sanity check, not the quote** — the quote comes from the value model.

### 6. Update the Airtable record
Show Tariq the draft link. On his go (`mcp__airtable__update_records`): `Stage` → `Proposal Sent`,
`Next Action Date` → today + 4, `Proposal Doc` → the doc link, append `YYYY-MM-DD: proposal sent (<doc link>)`
to `Activity Log`.

## Delegate (optional)
Win-theme / competitive framing / executive summary polish → `sales-proposal-strategist` agent. Deal risk / qualification gaps → `sales-deal-strategist`.
