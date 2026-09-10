---
name: lead-find
description: "Source and qualify B2B prospects for the active client. Uses the Explorium / Vibe Prospecting MCP to find decision-makers in the client's ICP industries (filtered by title, seniority, company size, country, hiring events, buying intent), enriches their work email + LinkedIn URL, dedupes against the active client's pipeline, scores each 0-100 against the client's ICP rubric, writes a prospect-specific hook, and creates one lead record per prospect via the pipeline adapter. Explorium contact enrichment costs credits (~3 per lead) - always confirm the estimate before exporting."
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
- `scripts/normalize.py`: dedupe helper

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
- **~3 credits per fully-contactable lead.** Check `remaining_user_credits` in export responses; `/lead-find` stops and reports if a batch would exceed what's left.

## Steps

### 1. Pick the segment
Default arg: an industry from `clients/<client>/icp.md` (`/lead-find marketing-agencies`). Also accept `count=25`, `intent=true`, `hiring=ops`, `client=<slug>`.
Map the industry to `linkedin_category` values via `autocomplete` (never pass raw text). Build filters:
- `linkedin_category`: from autocomplete
- `company_country_code` **and** `prospect_country_code`: `["US","CA"]`
- `company_size`: `["11-50","51-200"]` (from `clients/<client>/icp.md`; `["51-200","201-500"]` for manufacturing/logistics)
- `job_level`: `["owner","founder","c-suite","partner"]` (add `director` + `job_department: ["operations"]` for larger targets)
- `has_contact_details`: `{"value":"email"}`
- **`max_per_company`: 2** — outbound wants 1–2 contacts per company, not a whole org chart
- when `intent=true`: add `business_intent_topics` (autocomplete "marketing automation", "workflow automation", "AI automation") — these leads get the full intent score in `clients/<client>/scoring.md`
- when `hiring=<dept>`: add `events` `["hiring_in_operations_department","increase_in_operations_department"]`, `last_occurrence: 90`

### 2. Fetch + review (free)
`fetch-entities` (entity_type `prospects`) → `show-sample`. Present the sample to Tariq. Confirm the segment looks right before spending anything. Bad fit → adjust filters, re-fetch (still free).

### 3. Enrich + export (costs credits)
`enrich-prospects` with `["enrich-prospects-contacts"]`, `contact_types: ["email"]` → returns the new `table_name` + a cost estimate. Show the estimate. On Tariq's go, `export-to-csv` (pass a prior run's `dataset_id` as `exclude_key` to skip already-seen prospects). Download `_full_download_url`.

### 4. Dedupe
For each row: `normalize_domain(prospect_company_website)`, then `find_lead_by_domain(<domain>)` via the
pipeline adapter (pass the company name when there is no domain). Match → skip (note a suggested update);
no match → keep. Collapse rows so no company gets more than 2 records (keep the most senior, most
complete contacts).

### 5. Score + hook (Claude, per surviving row)
- **ICP Score:** apply `clients/<client>/scoring.md`. Leads from an `intent`/`hiring` pull auto-earn the intent points.
- **Hard exclusion** (`clients/<client>/icp.md`: competitor, "AI" product company, former/board-only contact, generic inbox) → Stage `Disqualified`, still create the task (status complete) so it isn't re-sourced.
- **Hook:** 1–2 sentences from their title + company focus + `prospect_skills` + any signal. Ties to one service line in `clients/<client>/offer.md`. No hype, no em dash.
- **Channel:** `email + linkedin` if both present, else whichever exists.
- **Stage:** ≥60 `Qualified`, 40–59 `Nurture`, <40 `Disqualified`.

### 6. Show before writing
```
15 rows → 6 companies → 1 dup dropped → 5 new
  Qualified 4 · Nurture 1 · Disqualified 1
  Acme Co / Jane Doe (81) · Beta Inc / John Roe (75) · ...
Create 5 records in the Airtable Lead Pipeline?
```
On yes → `create_lead` per lead via the pipeline adapter, one value per contract field
(`docs/pipeline-contract.md`). `stage` per band, `next_action_date` = today for Qualified, seed
`activity_log` with `YYYY-MM-DD: sourced + scored NN.`. On no → stop.

### 7. Report
Records created by stage, companies skipped as dups, disqualified + reasons, **credits spent + remaining**, and: "Next: `/lead-outreach` to draft first touches."

## Idempotency
Re-runnable. Step 4 dedupes against the pipeline; pass the previous `dataset_id` as `exclude_key` so Explorium returns fresh prospects.

## Delegate (optional)
Segment / signal design → `sales-outbound-strategist`. ICP refinement → `business-strategist`.
