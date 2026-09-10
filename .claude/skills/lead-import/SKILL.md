---
name: lead-import
description: "Ingest a CSV of already-known contacts into the active client's pipeline, skipping cold sourcing. Primary use: a website visitor de-anonymization export (RB2B and similar, see docs/visitor-deanonymization.md); also any warm list (a conference list, a client's existing contacts). Maps common column names to the pipeline contract fields, verifies each email with scripts/verify_email.py, dedupes each row against the pipeline by normalized company domain, scores each survivor 0-100 against the client's rubric, writes a hook, sets the channel from the data present, shows the summary, and creates one lead record per new contact via the pipeline adapter on an explicit yes. No credit cost: the contacts are already resolved."
---

# Lead Import

> Invoke with `/lead-import file=<path.csv>` (or "import this list"). Feeds the funnel at stage 1 without cold sourcing: warm lists and visitor de-anon exports enter here, then run stage 2 (`/lead-outreach`) onward like any other lead.

## Client config
Resolve the active client: a `client=<slug>` invocation arg wins, else `ACTIVE_CLIENT` in `.env`. Then read:
- `clients/<client>/scoring.md`: the 0-100 rubric
- `clients/<client>/icp.md`: industries, hard exclusions (a row that hits one is Disqualified, same as `/lead-find`)
- `clients/<client>/identity.md`: business name + CRM target (for `airtable`: base ID + table name)
- `clients/<client>/offer.md`: service lines, for the hook

Args: `file=<path.csv>` (required, the list to import; `data/` holds examples). `source=<label>`
(default `imported list`, written to the lead's `source`; for a visitor de-anon export use
`visitor-deanon - <tool>`, e.g. `visitor-deanon - rb2b`, and a `source` starting `visitor-deanon`
is treated as a visitor export in step 1 and step 4). `client=<slug>`.

## Read first
- `docs/visitor-deanonymization.md`: the main source of these lists and how a resolved visitor is shaped
- `docs/pipeline-contract.md`: the operations and the normalized lead fields
- `docs/pipeline-schema.md`: field reference (Airtable layout, dedupe rule)
- `docs/email-verification.md`: the verify step and the `email_status` values
- `scripts/normalize.py`: the dedupe helper (`normalize_domain`)
- `scripts/verify_email.py`: the email checker (`verify_email(email)` -> status + reason)

## Config
Pipeline reads and writes go through the **pipeline adapter** for the active client's `crm_target`
(`clients/<client>/identity.md`): `docs/pipeline-contract.md` names the operations,
`docs/pipeline-adapters/<crm_target>.md` maps them. For `smart-ai-workspace` that is `airtable`
(Airtable MCP `mcp__airtable__*`, base + table from `identity.md`). No Explorium, no credits: the
contacts in the CSV are already resolved.

## Steps

### 1. Read the CSV
Read `file` with the Python standard-library `csv` module (`csv.DictReader`). No new script: this is a
one-off parse, describe it, do not add code to `scripts/`. Lower-case and strip each header, then map
columns to contract fields, forgiving of naming:
- `email` <- `email` / `work_email` / `email_address`
- `contact_name` <- `name` / `full_name`, else `first_name` + `last_name` joined
- `company` <- `company` / `company_name` / `organization`
- `title` <- `title` / `job_title` / `position`
- `linkedin_url` <- `linkedin` / `linkedin_url` / `li_url`
- `company_domain` <- `domain` / `website` / `company_website` / `url`, run through `normalize_domain`
- `location` <- `location` / `city` / `region`
- when `source` starts `visitor-deanon`: a `page` / `url` / `visited` / `landing_page` column becomes
  the `signal` as `visited <page> on <date>` (the row's date column, else the file's date).

A row with no `company`, no `company_domain`, and no `email`: drop it, list it in the report as unusable.

### 2. Verify each email (free)
Run `scripts/verify_email.py` on every row that has an email (`verify_email(email)` -> `email_status` +
reason), same rules as `/lead-find` step 3b:
- `instantly` client: skip, Instantly verifies on import; read its status back instead.
- Set `email_status` per row: `invalid` (bad syntax / disposable / no mail route / role inbox) or
  `unknown` (the normal pass). Keep the reason string for the seeded Activity Log line.
- No email at all: leave `email_status` blank, the row is LinkedIn-only (step 4).

### 3. Dedupe against the pipeline
Per row: `normalize_domain(company_domain)` (or the email's domain, or the company name when neither),
then `find_lead_by_domain(<domain-or-name>)` via the adapter. Match -> skip the row (note "already in
pipeline"; for a visitor export note "returning visitor" so the founder can nudge the open thread). No
match -> keep. Collapse duplicate rows within the file so no company gets more than 2 new records
(keep the most senior, most complete contacts).

**Suppression check** (same as `/lead-find` step 4): if `clients/<client>/suppress.md` exists, drop a
surviving row whose email matches a full address line or whose normalized domain matches an `@domain`
line. Case-insensitive; ignore blank lines and `#` comments; read the token before any inline `#`.

### 4. Score, hook, channel (Claude, per surviving row)
- **ICP Score:** apply `clients/<client>/scoring.md`. A `visitor-deanon` row earns the intent-signal
  points (a real visit to the client's own site). A plain warm list does not, unless a signal is
  visible in the data.
- **Hard exclusion** (`clients/<client>/icp.md`: competitor, "AI" product company, generic inbox) ->
  Stage `Disqualified`, still create the record so it is not re-sourced.
- **Hook:** 1 to 2 sentences from company + title + the page they visited (visitor export) or the
  list context (warm list), tied to one service line in `clients/<client>/offer.md`. No hype, no em dash.
- **Channel:** `email + linkedin` if both present, else whichever exists.
- **Stage:** >=60 `Qualified`, 40-59 `Nurture`, <40 `Disqualified`.
- **`email_status: invalid` override** (same as `/lead-find` step 5): if the row has a personal
  `linkedin_url`, keep the band Stage, set `channel` to `linkedin` (drop email), `next_action` "email
  failed verification, LinkedIn only". No LinkedIn -> Stage `Nurture`, `next_action` "needs a valid
  contact, re-enrich or find another decision-maker".

### 5. Show before writing
```
32 rows -> 21 companies -> 4 already in pipeline -> 17 new
  Qualified 9 · Nurture 5 · Disqualified 3
  Acme / Jane Doe (78) · Globex / Sam Roe (64) · ...
Create 17 records in the Airtable Lead Pipeline?
```
On yes -> `create_lead` per lead via the adapter, one value per contract field
(`docs/pipeline-contract.md`), `source` = the `source` arg, `stage` per band (or the step 4
invalid-email override). `next_action_date` = today for Qualified. Seed `activity_log` with
`YYYY-MM-DD: imported from <source>.` plus ` email <status> (<reason>).` when the status is not a
clean `unknown`. On no -> stop.

### 6. Report
Records created by stage, rows skipped as dups (returning visitors called out), rows dropped as
unusable, disqualified + reasons, count with `email_status: invalid` (and whether they fell back to
LinkedIn or Nurture), and: "Next: `/lead-outreach` to draft first touches."

## Writes
One `create_lead` per new lead via the adapter. `activity_log` seeded with
`YYYY-MM-DD: imported from <source>.` plus the email-status reason when it is not a clean `unknown`.
Nothing else: no Explorium call, no file writes, no sends.

## Idempotency
Re-running the same file re-dedupes every row against the pipeline (step 3), so rows imported on a
prior run are skipped. Safe to re-run after fixing a source CSV.

## Delegate (optional)
How to sequence warm inbound-intent leads differently from cold outbound (a visitor who was already
researching the client needs a lighter first touch): `sales-outbound-strategist`.
