# Pipeline contract (target-neutral)

The 5 funnel skills never talk to a CRM directly. They perform **operations** from the list
below against the **pipeline adapter** for the active client's `crm_target`
(`clients/<client>/identity.md`). Each `crm_target` has one adapter doc in
`docs/pipeline-adapters/<target>.md` that maps these operations to real calls.

- `airtable` (default) and `instantly` are implemented.
- `hubspot` and `gohighlevel` are documented stubs.

This file defines the shared vocabulary: the lead fields, the Stage values, and the 7 operations.
It is prose, not code. There is no framework, class, or parser here.

## Normalized lead fields

Target-neutral names, lifted from `docs/pipeline-schema.md` (the Airtable layout). An adapter maps
each to its store's real field. `company` is the only always-required field on create; everything
else is written when known.

| Contract field | Type | Meaning |
|---|---|---|
| `company` | text | company name (the primary identifier) |
| `contact_name` | text | the decision-maker |
| `title` | text | their job title |
| `stage` | enum | pipeline stage, see the vocabulary below |
| `icp_score` | integer 0-100 | from `clients/<client>/scoring.md` |
| `channel` | enum | `email + linkedin` / `email` / `linkedin` / `upwork` |
| `industry` | slug | `real-estate` `e-commerce` `manufacturing` `marketing-agencies` `logistics` `saas` `other` |
| `email` | email | contact work email |
| `email_status` | enum | `valid` / `catchall` / `unknown` / `invalid`. Set by `/lead-find` after enrichment (`scripts/verify_email.py`) and re-checked by `/lead-outreach` before every email send. `invalid` never gets an email. See `docs/email-verification.md`. |
| `linkedin_url` | url | the contact's profile |
| `company_domain` | text | bare domain, no scheme. **The dedupe key.** (Airtable field name: `Company Website`) |
| `company_linkedin_url` | url | |
| `location` | text | |
| `signal` | long text | buying-signal string, auto-filled by `/lead-find` and `/lead-signals` from `docs/signal-catalog.md` (funding / job change / hiring / tech-stack / intent). A short readable line, not raw event JSON. Empty when no event matched. |
| `hook` | long text | the prospect-specific "why they need this" line |
| `next_action` | long text | the next step in words |
| `next_action_date` | ISO date `YYYY-MM-DD` | when the next touch is due |
| `source` | text | e.g. `Explorium / Vibe Prospecting - <segment>, <date>` |
| `activity_log` | long text | dated lines, oldest first, newest appended (see `append_activity`) |
| `proposal_doc_url` | url | set by `/lead-proposal` |
| `deal_value` | number | expected or signed deal amount, client currency. Optional. Set at `Call Booked` (expected), confirmed at `Proposal Sent` / `Won`. `/lead-report` sums it for pipeline value; absent or empty on every lead means pipeline value is reported as "not set". |

Legacy Airtable-only fields (`ClickUp Task ID`, `ClickUp URL`) are not part of the contract.

## Stage vocabulary

The authoritative stage of a lead. Adapters map these to whatever their store tracks.

```
Qualified        ICP Score >= 60, hook written, ready for outreach
Nurture          40-59, or good fit / bad timing
Disqualified     < 40, or a hard exclusion (record kept so it is not re-sourced)
Contacted        first touch sent
Replied          prospect responded (cadence stops, a human takes over)
Call Booked      discovery call scheduled
Proposal Sent    3-option proposal delivered
Won              signed
Lost             explicit no, or 90 days cold after Contacted
```

Note: the Airtable single-select also carries a legacy `Contacted (draft)` option from Bike Method
Phase 2. Phase 3 (autonomous send) never writes it. It is not in the contract vocabulary.

## The 7 operations

Logical operations, not HTTP calls. An adapter may satisfy several of them in one underlying request
(the Airtable adapter combines `set_stage` + `update_lead` + `append_activity` on one record into a
single `update_records` call, which is what the skills do today).

### 1. `create_lead(lead)`
- **Intent:** create one prospect record. The caller has already deduped (see `find_lead_by_domain`).
- **In:** `lead` = the normalized fields above. `company` required. `stage` set per band. `activity_log`
  seeded with one dated line.
- **Out:** the new record's store-native `id` (string).

### 2. `find_lead_by_domain(domain)`
- **Intent:** the dedupe check before `create_lead`, and the single-lead lookup used by
  `/lead-proposal` and `/upwork-proposal`.
- **In:** `domain` = a normalized bare domain from `scripts/normalize.py`, **or** a company name when
  no domain exists (name-only companies, Upwork posts).
- **Out:** the matching record (`id` + current fields), or nothing. More than one match: return all,
  the caller collapses to at most 2 per company.

### 3. `list_leads(filter)`
- **Intent:** the work queue. `/lead-outreach` (due for a touch) and `/lead-pipeline` (everything).
- **In:** `filter` = any of `stage` (one value or a set), `next_action_date_on_or_before` (ISO date),
  or nothing (return all). Optional sort by `icp_score` desc.
- **Out:** list of records, each with `id` + every field the skills read: `stage`, `icp_score`,
  `channel`, `next_action_date`, `activity_log`, `email`, `linkedin_url`, `company`, `contact_name`,
  `hook`, `signal`.

### 4. `update_lead(id, fields)`
- **Intent:** write one or more plain fields on an existing record. The generic setter.
- **In:** `id`, `fields` = a partial map of normalized fields (e.g. `next_action`,
  `next_action_date`, `proposal_doc_url`, `email`, `channel`).
- **Out:** ok.
- Does not own stage moves (`set_stage`) or log lines (`append_activity`), though an adapter may
  implement all three as one call.

### 5. `set_stage(id, stage)`
- **Intent:** move a lead to a new pipeline stage. Split out because campaign-centric stores model
  stage very differently from a free field.
- **In:** `id`, `stage` = one value from the vocabulary.
- **Out:** ok.

### 6. `append_activity(id, line)`
- **Intent:** add one dated line to the lead's Activity Log without losing the existing lines. The
  canonical audit trail: every send, stage change, and proposal is logged here by the calling skill.
- **In:** `id`, `line` = one string. The caller prefixes `YYYY-MM-DD: `.
- **Out:** ok.

### 7. `report_metrics(since)`
- **Intent:** pipeline health numbers. Consumed by `/lead-pipeline` now and a future `/lead-report`.
- **In:** `since` = ISO date, the window start.
- **Out:** `{ stage_counts: {stage: n}, touches_since: n, replies_since: n }`, plus stage-to-stage
  conversion counts over the window where the target can derive them. A number the target cannot
  derive is returned as `null`, and the skill falls back to computing it from `list_leads` +
  `activity_log` text (which is exactly what `/lead-pipeline` does today).
- An adapter may additionally return any of `opens_since`, `meetings_booked_since`,
  `proposals_sent_since`, `deals_won_since`, `pipeline_value` when its store derives them cheaply
  (Instantly campaign analytics does; Airtable returns them `null` and `/lead-report` derives them
  from `list_leads` + `activity_log`). All optional.

## Coverage by target

| Operation | airtable | instantly |
|---|---|---|
| `create_lead` | full | full (adds the lead to the campaign) |
| `find_lead_by_domain` | full | full (search by email / company) |
| `list_leads` | full | partial (filters on Instantly lead status, not on Stage or Next Action Date) |
| `update_lead` | full | full (custom variables) |
| `set_stage` | full | partial (native status covers Contacted/Replied/Call Booked/Won/Lost; the rest go to a `stage` custom variable) |
| `append_activity` | full | partial (no log field; a `activity_log` custom variable, or a light sheet alongside) |
| `report_metrics` | full (derived by reading all records, no server-side aggregation, same as today) | partial (campaign analytics give sent/opens/replies well; late-funnel stage counts need the custom variable or a sheet) |

`hubspot` and `gohighlevel`: none implemented yet, see their stub docs.
