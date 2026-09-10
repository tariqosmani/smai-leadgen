---
name: lead-find
description: "Source and qualify B2B prospects for the active client. Uses the Explorium / Vibe Prospecting MCP to find decision-makers in the client's ICP industries (filtered by title, seniority, company size, country, hiring events, buying intent), enriches their work email + LinkedIn URL, dedupes against the active client's pipeline, scores each 0-100 against the client's ICP rubric, writes a prospect-specific hook, and creates one lead record per prospect via the pipeline adapter. Detects buying-signal events (funding, decision-maker job change, hiring spike, tech-stack adoption, buying intent) during sourcing and auto-fills the Signal field per docs/signal-catalog.md. Explorium contact enrichment costs credits (~3 per lead) - always confirm the estimate before exporting."
bike-method-phase: 2
---

# Lead Find

> Invoke with `/lead-find` or "find new leads". Full funnel stage 1 of 5.

Pipeline: **pick segment → fetch prospects → review sample (free) → enrich email+LinkedIn (credits) → export → dedupe → score → hook → create lead records via the pipeline adapter**.

## Client config
Resolve the active client: a `client=<slug>` invocation arg wins, else `ACTIVE_CLIENT` in `.env`. Then read:
- `clients/<client>/icp.md`: segments, hard exclusions, intent signals
- `clients/<client>/scoring.md`: the 0-100 rubric
- `clients/<client>/identity.md`: business name + CRM target (for an `airtable` client: the base ID + table name)

## Read first
- `docs/pipeline-contract.md`: the target-neutral operations and lead fields
- `docs/pipeline-schema.md`: field reference (Airtable layout, dedupe rule)
- `docs/signal-catalog.md`: buying-signal events, the `signals=` arg mapping, the `signal` string templates
- `docs/email-verification.md`: the verify step, the `email_status` values, free vs paid
- `scripts/normalize.py`: dedupe helper
- `scripts/verify_email.py`: email verification helper (free tier)

## Config
Pipeline reads and writes go through the **pipeline adapter** for the active client's `crm_target`
(`clients/<client>/identity.md`): `docs/pipeline-contract.md` names the operations, and
`docs/pipeline-adapters/<crm_target>.md` maps them to real calls. For `smart-ai-workspace` that is
`airtable` (base ID + table from `identity.md`, Airtable MCP `mcp__airtable__*`). Explorium runs
through the **Vibe Prospecting MCP** (`mcp__claude_ai_Vibe_Prospecting__*`), no API key here.

## Cost model (tell Tariq before spending)
- prospect fetch / base row: ~1 credit each on export
- email enrichment: ~2 credits each
- LinkedIn URL: free, included in the base record
- signal events (`signals=` runs): preview free, event columns may add a small amount to the export; it lands in the same step-3 estimate, not a second charge
- **~3 credits per fully-contactable lead.** Check `remaining_user_credits` in export responses; `/lead-find` stops and reports if a batch would exceed what's left.

## Steps

### 1. Pick the segment
Default arg: an industry from `clients/<client>/icp.md` (`/lead-find marketing-agencies`). Also accept `count=25`, `signals=<list>`, `client=<slug>`. `signals=` takes a comma list of `funding,job-change,hiring,tech-stack,intent` (`/lead-find marketing-agencies signals=funding,hiring`). Shorthands still work: `intent=true` = `signals=intent`, `hiring=<dept>` = `signals=hiring` scoped to that department.
Map the industry to `linkedin_category` values via `autocomplete` (never pass raw text). Build filters:
- `linkedin_category`: from autocomplete
- `company_country_code` **and** `prospect_country_code`: `["US","CA"]`
- `company_size`: `["11-50","51-200"]` (from `clients/<client>/icp.md`; `["51-200","201-500"]` for manufacturing/logistics)
- `job_level`: `["owner","founder","c-suite","partner"]` (add `director` + `job_department: ["operations"]` for larger targets)
- `has_contact_details`: `{"value":"email"}`
- **`max_per_company`: 2** — outbound wants 1–2 contacts per company, not a whole org chart
- for each value in `signals=`: add the Explorium filter from `docs/signal-catalog.md` > Catalog. `intent` -> `business_intent_topics` (autocomplete the offer's topics); `hiring` -> `events` `hiring_in_<dept>_department` + `increase_in_<dept>_department`, `last_occurrence: 90`; `funding` -> `events` `new_funding_round,new_investment,ipo_announcement`, `last_occurrence: 90`; `job-change` -> `current_role_months: {"lte": 6}`; `tech-stack` -> `company_tech_stack_tech` (autocomplete the tool). The `events` filter is businesses-only: fetch businesses with it first, then refine to prospects via `businesses_reference_table`. Signal-bearing leads auto-earn the timing/intent points in `clients/<client>/scoring.md`.

### 2. Fetch + review (free)
`fetch-entities` (entity_type `prospects`) → `show-sample`. Present the sample to Tariq. Confirm the segment looks right before spending anything. Bad fit → adjust filters, re-fetch (still free).

### 3. Enrich + export (costs credits)
`enrich-prospects` with `["enrich-prospects-contacts"]`, `contact_types: ["email"]` → returns the new `table_name` + a cost estimate. When `signals=` was set, also pull the matching event table now (`fetch-businesses-events` on the companies, `fetch-prospects-events` on the prospects, keys per `docs/signal-catalog.md`); the event preview is free and its columns ride the same `export-to-csv`, so its cost is already inside this one estimate. Show the estimate. On Tariq's go, `export-to-csv` (pass a prior run's `dataset_id` as `exclude_key` to skip already-seen prospects). Download `_full_download_url`. Demo / no-spend mode: this estimate + confirm is the only spend gate, event lookups included, nothing exports autonomously.

### 3b. Verify enriched emails (free)
Scope: email verification only. Run `scripts/verify_email.py` on each enriched email
(`verify_email(email)` -> `email_status` + reason). Full behavior: `docs/email-verification.md`.
- `instantly` client: skip this, Instantly verifies on import. Read its status back into `email_status` instead.
- Sets the `email_status` contract field per row: `invalid` (bad syntax / disposable / no mail route / role inbox) or `unknown` (the normal pass). `valid` / `catchall` only come from a paid verifier.
- Keep the reason string, it goes in the seeded Activity Log line.

### 4. Dedupe
For each row: `normalize_domain(prospect_company_website)`, then `find_lead_by_domain(<domain>)` via the
pipeline adapter (pass the company name when there is no domain). Match → skip (note a suggested update);
no match → keep. Collapse rows so no company gets more than 2 records (keep the most senior, most
complete contacts).

**Suppression list check** (localized, independent of any email-verification step): if
`clients/<client>/suppress.md` exists, drop a surviving row when its prospect email matches a full
address line, or its normalized company domain matches an `@domain` line. Case-insensitive. Ignore
blank lines and lines starting with `#`; on an entry line read the token before any inline `#`
comment. These are `/lead-replies` unsubscribes and hard bounces, never re-source them.

### 5. Score + hook (Claude, per surviving row)
- **Signal:** from the event table pulled in step 3, compose the `signal` string per `docs/signal-catalog.md` template (funding / job-change / hiring / tech-stack / intent). Match businesses-events on the normalized company domain, prospects-events on the prospect. No matching event → leave `signal` empty (current behavior).
- **ICP Score:** apply `clients/<client>/scoring.md`. Any signal-bearing lead (a `signals=` pull, or an event attached above) auto-earns the timing/intent points, per `docs/signal-catalog.md` > What a signal does downstream.
- **Hard exclusion** (`clients/<client>/icp.md`: competitor, "AI" product company, former/board-only contact, generic inbox) → Stage `Disqualified`, still create the task (status complete) so it isn't re-sourced.
- **Hook:** 1–2 sentences from their title + company focus + `prospect_skills` + any signal. When a `signal` is present the hook leads with it (`docs/signal-catalog.md` > Hook angle). Ties to one service line in `clients/<client>/offer.md`. No hype, no em dash.
- **Channel:** `email + linkedin` if both present, else whichever exists.
- **Stage:** ≥60 `Qualified`, 40–59 `Nurture`, <40 `Disqualified`.
- **`email_status: invalid` override** (step 3b): the lead must not flow to outreach. If it has a personal `linkedin_url`, keep the band Stage but set `channel` to `linkedin` (drop email) and `next_action` "email failed verification, LinkedIn only". If no LinkedIn, force Stage `Nurture`, `next_action` "needs a valid contact, re-enrich or find another decision-maker". Either way still create the record (company not re-sourced).

### 6. Show before writing
```
15 rows → 6 companies → 1 dup dropped → 5 new
  Qualified 4 · Nurture 1 · Disqualified 1
  Acme Co / Jane Doe (81) · Beta Inc / John Roe (75) · ...
Create 5 records in the Airtable Lead Pipeline?
```
On yes → `create_lead` per lead via the pipeline adapter, one value per contract field
(`docs/pipeline-contract.md`), including `email_status` from step 3b. `stage` per band (or the
step 5 invalid-email override), `next_action_date` = today for Qualified, seed `activity_log`
with `YYYY-MM-DD: sourced + scored NN.` plus ` email <status> (<reason>).` when the status is not
a clean `unknown`. On no → stop.

### 7. Report
Records created by stage, companies skipped as dups, disqualified + reasons, count of leads with `email_status: invalid` (and whether they fell back to LinkedIn or Nurture), **credits spent + remaining**, and: "Next: `/lead-outreach` to draft first touches."

## Idempotency
Re-runnable. Step 4 dedupes against the pipeline; pass the previous `dataset_id` as `exclude_key` so Explorium returns fresh prospects.

## Delegate (optional)
Segment / signal design → `sales-outbound-strategist`. ICP refinement → `business-strategist`.
