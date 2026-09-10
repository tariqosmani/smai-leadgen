---
name: lead-proposal
description: "Draft a three-option fixed-scope proposal for the active client's lead after the discovery call. Takes discovery-call notes (pasted, or from the lead record via the pipeline adapter), applies the value-based pricing method from the client's offer.md, and produces a Google Doc with current state, desired outcome, Essential/Growth/Scale options, milestones and payment events, run-cost estimate, and measurement plan. Does not invent numbers the client hasn't given."
bike-method-phase: 2
---

# Lead Proposal

> Invoke with `/lead-proposal Acme` or "draft the proposal for Acme". Full funnel stage 4 of 5.

## Client config
Resolve the active client: a `client=<slug>` invocation arg wins, else `ACTIVE_CLIENT` in `.env`. Then read:
- `clients/<client>/offer.md`: **the whole Pricing method.** Especially §1 (discovery), §2 (value model), §3 (corridor), §4 (three options), §5 (milestones). Also its Portfolio proof points.
- `clients/<client>/voice.md`: the client's register
- `clients/<client>/identity.md`: business name (for the doc title), CRM base + table

## Config
Pipeline reads and writes go through the **pipeline adapter** for the active client's `crm_target`
(`clients/<client>/identity.md`): operations in `docs/pipeline-contract.md`, mapping in
`docs/pipeline-adapters/<crm_target>.md`. For `smart-ai-workspace` that is `airtable`.
Google Doc via `mcp__claude_ai_Google_Drive__create_file` (or the `gws docs` CLI if authed).

## Steps

### 1. Gather inputs
Find the lead's record with `find_lead_by_domain(<company name>)` via the pipeline adapter. Pull discovery
notes from the record's `activity_log` / `signal` / `hook`. If notes are thin, ask Tariq to paste the call notes.
You need, at minimum:
- the business problem in the client's words
- the current process (trigger → steps → decisions → result) and the constraint step
- their numbers: volume, time per item, people involved, frequency, cost of failure
- who owns the decision, the access, and "success"
- deadline / why now

**If the value inputs are missing, stop and list what's needed.** Do not fabricate a value model (`offer.md` Pricing method: "never by inventing value").

### 2. Build the first-year value model (`offer.md` Pricing method §2)
With the client's numbers only. Label every assumption. Apply confidence adjustment (high/med/low). No double counting — pick the most defensible primary model, rest is upside.

### 3. Price the corridor (§3)
Cost floor (delivery + risk + margin) ↔ value ceiling (confidence-adjusted first-year value). Starting price 10–20% of credible value. Run the 10X check and the margin check. If value ceiling < cost floor → **no deal at this scope**: recommend shrinking the outcome or paid discovery, don't force a number.

### 4. Three options (§4)
Essential / Growth (recommended) / Scale. Each solves a different-sized problem. Map to the service lines in `clients/<client>/offer.md`. Middle option designed to win; lower option genuinely useful; upper option a real buyer.

### 5. Write the Google Doc
Order (`offer.md` Pricing method §4 "Proposal order"): current state (their words + numbers) → desired future state + business result → why founder-led / relevant portfolio proof → the three options with scope, assumptions, exclusions → milestones + payment events (§5, pay at signing then ~every 30 days, objective milestones) → estimated monthly run cost + volume assumption (§8, client-owned credentials) → measurement plan (§9, baseline + 3–5 metrics) → commercial terms note (MSA + SoW).

Create the doc (`Google_Drive__create_file`, type Google Doc, title `{business name from identity.md} — Proposal for {Company} ({YYYY-MM-DD})`), then write the sections. Voice rules apply (no em dash, no hype). Reference ranges in `offer.md` are a **sanity check, not the quote** — the quote comes from the value model.

### 6. Update the lead record
Show Tariq the draft link. On his go, via the pipeline adapter: `set_stage` → `Proposal Sent`;
`update_lead` with `next_action_date` → today + 4 and `proposal_doc_url` → the doc link;
`append_activity` `YYYY-MM-DD: proposal sent (<doc link>)`. On `airtable` these are one `update_records` call.

## Delegate (optional)
Win-theme / competitive framing / executive summary polish → `sales-proposal-strategist` agent. Deal risk / qualification gaps → `sales-deal-strategist`.
