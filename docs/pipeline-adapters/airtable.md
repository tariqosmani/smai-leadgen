# Pipeline adapter: airtable (default)

Maps the 7 operations in `docs/pipeline-contract.md` to `mcp__airtable__*` calls. This is the
**default** target and the one `smart-ai-workspace` runs on. The effect of every operation here is
identical to what the skills did when they called Airtable inline, so nothing about the live pipeline
changes.

## Connection

- Access: the **Airtable MCP** (`mcp__airtable__*`), running from `.mcp.json` (`npx airtable-mcp-server`),
  Personal Access Token in `.mcp.json` (gitignored). No `.env` var, no key in `identity.md`.
- `baseId` and `tableId`: from `clients/<client>/identity.md` > CRM target. For `smart-ai-workspace`:
  - base `appMULkAmdFmneAyB` (SmartAI Listings Database)
  - table `tblHGHp4DthpNKAU9` (`Lead Pipeline`). The table name string `Lead Pipeline` also works.
- Field layout: `docs/pipeline-schema.md`. Contract field names map to the Airtable column of the
  same label, except `company_domain` -> `Company Website`.
- Always pass `typecast: true` on writes so single-selects (`Stage`, `Channel`, `Industry`,
  `Email Status`) and the date field accept plain strings.

## Field mapping

| Contract | Airtable column |
|---|---|
| `company` | `Company` (primary field) |
| `contact_name` | `Contact Name` |
| `title` | `Title` |
| `stage` | `Stage` (single select) |
| `icp_score` | `ICP Score` (number) |
| `channel` | `Channel` (single select) |
| `industry` | `Industry` (single select) |
| `email` | `Email` |
| `email_status` | `Email Status` (single select): `valid` / `catchall` / `unknown` / `invalid` |
| `linkedin_url` | `LinkedIn` |
| `company_domain` | `Company Website` (bare domain, the dedupe key) |
| `company_linkedin_url` | `Company LinkedIn` |
| `location` | `Location` |
| `signal` | `Signal` |
| `hook` | `Hook` |
| `next_action` | `Next Action` |
| `next_action_date` | `Next Action Date` (ISO `YYYY-MM-DD`) |
| `source` | `Source` |
| `activity_log` | `Activity Log` |
| `proposal_doc_url` | `Proposal Doc` |
| `deal_value` | `Deal Value` (currency, USD) |

Stage values are stored verbatim (`Qualified`, `Nurture`, `Disqualified`, `Contacted`, `Replied`,
`Call Booked`, `Proposal Sent`, `Won`, `Lost`). The legacy `Contacted (draft)` select option is left
in the base but never written under Bike Method Phase 3.

`Email Status` values are stored verbatim too (`valid` / `catchall` / `unknown` / `invalid`). With
`typecast: true` the first `create_record` / `update_records` that writes `invalid` adds the select
option; if the token lacks schema-write permission, add the option once by hand. `/lead-find` sets
this field, `/lead-outreach` reads it as a pre-send guard (`docs/email-verification.md`).

## Operations

### 1. `create_lead(lead)`
`mcp__airtable__create_record`
- `baseId`, `tableId` from `identity.md`
- `fields`: one key per known contract field, mapped to its Airtable column above
- `typecast: true`
- Seed `Activity Log` with the single dated line the skill provides (e.g.
  `2026-09-02: sourced + scored 81.`).
- For a `Qualified` lead, set `Next Action Date` to today.
- Returns the new `record.id`.

### 2. `find_lead_by_domain(domain)`
`mcp__airtable__list_records` (or `mcp__airtable__search_records`)
- **Domain given:** `filterByFormula: LOWER({Company Website}) = "<normalized-domain>"`
- **Company name only:** `mcp__airtable__search_records` for the name against the `Company` field
  (or `filterByFormula: LOWER({Company}) = "<lower-name>"`)
- Return the matched record(s) with all fields. Zero rows -> nothing. This is the dedupe gate in
  `/lead-find` step 4 and the record lookup in `/lead-proposal` step 1 and `/upwork-proposal` step 4.

### 3. `list_leads(filter)`
`mcp__airtable__list_records`
- `baseId`, `tableId` from `identity.md`
- No filter (the `/lead-pipeline` case): fetch all records, paging if needed.
- `stage` filter: `filterByFormula: {Stage} = "Qualified"`, or an `OR(...)` across several values.
- Due-for-touch (`/lead-outreach`): `filterByFormula: AND(OR({Stage}="Qualified",{Stage}="Contacted"), IS_BEFORE({Next Action Date}, DATEADD(TODAY(),1,'days')))`
  then in the skill drop `Contacted` rows whose `Activity Log` already shows 5 sent emails.
- Optional `sort`: `[{field: "ICP Score", direction: "desc"}]`.
- Return each record with `id` + fields.

### 4. `update_lead(id, fields)`
`mcp__airtable__update_records`
- `records: [{ id, fields: { <mapped columns> } }]`, `typecast: true`.

### 5. `set_stage(id, stage)`
`mcp__airtable__update_records` with `fields: { "Stage": "<stage>" }`, `typecast: true`.

### 6. `append_activity(id, line)`
Read then write the whole field (Airtable has no append):
1. Read the record's current `Activity Log` (from the `list_leads` result you already hold, or
   `mcp__airtable__get_record`).
2. New value = old value + `"\n"` + `line` (skip the newline if the field was empty).
3. `mcp__airtable__update_records` with `fields: { "Activity Log": "<whole new value>" }`.

### 7. `report_metrics(since)`
No server-side aggregation. `mcp__airtable__list_records` (all), then in the skill:
- `stage_counts`: tally `Stage` across the records.
- `touches_since` / `replies_since`: scan each `Activity Log` for dated lines on or after `since`
  (`... touch N SENT` lines; `Replied` transitions).
- conversion counts: from the same `Activity Log` timestamps.
This is exactly what `/lead-pipeline` step 4 does now.

## Combining calls (what the skills do today)

When a skill step performs `set_stage` + `update_lead` + `append_activity` on the same record at
the same time (every send in `/lead-outreach` step 5, the proposal update in `/lead-proposal` step 6),
do it as **one** `mcp__airtable__update_records` call: `fields` carries `Stage`, `Next Action Date`,
`Next Action`, and the rebuilt `Activity Log` string together. Same result, one write, unchanged from
current behavior.

## Regression checklist

A reviewer comparing to pre-abstraction behavior should confirm:

1. `create_lead` still calls `mcp__airtable__create_record` with `typecast: true` and one field per
   `docs/pipeline-schema.md` column.
2. Dedupe still runs `filterByFormula: LOWER({Company Website}) = "<normalized-domain>"` on the
   normalized domain from `scripts/normalize.py`, with a company-name fallback.
3. `Activity Log` is still read-modify-write of the whole field, oldest line first, newest appended.
4. Stage is still written as the exact single-select strings, `typecast: true`, and
   `Contacted (draft)` is still never written.
5. `/lead-outreach` still writes `Stage` + `Next Action Date` + `Next Action` + `Activity Log` in one
   `update_records` per sent message, with the Gmail `threadId` in the logged line.
6. `/lead-pipeline` is still read-only except the confirmed cold-lead lapse to `Stage = Lost`.
7. `baseId` / `tableId` still come from `clients/smart-ai-workspace/identity.md`
   (`appMULkAmdFmneAyB` / `Lead Pipeline`).
8. Gmail still sends the outreach (Airtable does not own sending).
