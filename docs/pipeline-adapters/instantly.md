# Pipeline adapter: instantly

Maps the 7 operations in `docs/pipeline-contract.md` to the **Instantly API v2** over HTTPS. There is
no Instantly MCP in this repo, so the skill makes plain authenticated requests (curl, `requests`, or
whatever the run environment has).

Instantly is a cold-email sending platform, so a client on `crm_target: instantly` also **sends
through Instantly**, not Gmail. See "Sending consequence" at the bottom.

Docs: <https://developer.instantly.ai/> (API v2). Endpoints below were taken from that reference;
confirm shapes against the live docs before a first run, and check the workspace for custom interest
statuses.

## Connection

- **Base URL:** `https://api.instantly.ai/api/v2`
- **Auth:** `Authorization: Bearer <API_KEY>` on every request. The key is a v2 API key; it needs
  lead + campaign analytics scopes (`leads:all` or `leads:create` + `leads:read`, `analytics:read`,
  or `all:all`).
- **Config (never committed):**
  - `identity.md` names the env vars, it does not hold the values:
    - `crm_api_key_env: INSTANTLY_API_KEY`
    - `crm_campaign_id_env: INSTANTLY_CAMPAIGN_ID`
  - `.env` holds the real values (`.env` is gitignored). `scripts/check_client.py` asserts both are
    set when `crm_target: instantly`.
- One Instantly **campaign** is the pipeline for the client. Its id is `INSTANTLY_CAMPAIGN_ID`.
  Late-funnel state that Instantly cannot model lives in a `stage` custom variable on the lead (see
  `set_stage`).

## Field mapping

| Contract | Instantly | Notes |
|---|---|---|
| `company` | `company_name` | |
| `contact_name` | `first_name` + `last_name` | split on first space |
| `title` | `custom_variables.title` | |
| `stage` | `custom_variables.stage` | verbatim contract value; the late-funnel source of truth |
| `icp_score` | `custom_variables.icp_score` | number |
| `channel` | `custom_variables.channel` | Instantly is email-only; `linkedin` leads should not go here |
| `industry` | `custom_variables.industry` | |
| `email` | `email` | the lead key in Instantly |
| `email_status` | `custom_variables.email_status` | Instantly also runs its own verification |
| `linkedin_url` | `custom_variables.linkedin_url` | |
| `company_domain` | `website` | Instantly stores it as the website URL |
| `company_linkedin_url` | `custom_variables.company_linkedin_url` | |
| `location` | `custom_variables.location` | |
| `signal` | `custom_variables.signal` | usable as a merge field in the sequence |
| `hook` | `custom_variables.hook` | usable as a merge field in the sequence |
| `next_action` | `custom_variables.next_action` | Instantly's own scheduler drives real sends |
| `next_action_date` | `custom_variables.next_action_date` | advisory only under Instantly |
| `source` | `custom_variables.source` | |
| `activity_log` | `custom_variables.activity_log` | read-modify-write, same pattern as Airtable |
| `proposal_doc_url` | `custom_variables.proposal_doc_url` | |
| `deal_value` | `custom_variables.deal_value` | number; summed by `/lead-report` for pipeline value |

`custom_variables` values must be string / number / boolean / null (no nested objects or arrays).

## Stage mapping

Instantly is campaign-centric. It tracks where a lead is in a **sequence** and an **interest
status**, not a sales pipeline.

| Contract stage | Instantly | Clean? |
|---|---|---|
| `Qualified` | lead added to the campaign, no email sent yet | yes (campaign membership + `email_sent` count 0) |
| `Nurture` | not added to the sending campaign; hold in a separate list or leave uncreated | partial |
| `Disqualified` | not added; optionally add to a blocklist | partial |
| `Contacted` | Instantly has sent >= 1 email (native: sequence step >= 1, `email_sent` events) | yes (native) |
| `Replied` | native: lead replied, Instantly auto-pauses the lead | yes (native) |
| `Call Booked` | `lt_interest_status = 2` (Meeting Booked) | loose (interest status is coarse) |
| `Proposal Sent` | **no native concept** | no -> `custom_variables.stage` |
| `Won` | `lt_interest_status = 4` (Closed) | loose -> also `custom_variables.stage` |
| `Lost` | `lt_interest_status = -3` (Lost), or unsubscribe | loose -> also `custom_variables.stage` |

**Do not map cleanly:** `Nurture`, `Disqualified`, `Call Booked`, `Proposal Sent`, `Won`, `Lost`.

**Pragmatic fix:** write the contract stage verbatim into `custom_variables.stage` on every
`set_stage`, and treat that custom variable as the pipeline's source of truth. Use Instantly's native
status and analytics for the early funnel (`Contacted`, `Replied`) where they are reliable. If the
team wants a real board for the late funnel, keep a light sheet (Airtable or Google Sheet) keyed by
email alongside Instantly and update it in the same `set_stage` / `append_activity` step. `/lead-report`
should read `custom_variables.stage`, not infer stage from campaign analytics.

`lt_interest_status` values seen in the v2 schema: `[1, 2, 3, 4, 0, -1, -2, -3, -4]`. Commonly:
`1` Interested, `2` Meeting Booked, `3` Meeting Completed, `4` Closed/Won, `0`/null Lead,
`-1` Not Interested, `-2` Wrong Person, `-3` Lost, `-4` do-not-contact. Confirm against the workspace,
custom statuses are allowed.

## Operations

### 1. `create_lead(lead)`
`POST /api/v2/leads`
```
{
  "campaign": "<INSTANTLY_CAMPAIGN_ID>",
  "email": "<email>",                     // required when campaign is set
  "first_name": "...", "last_name": "...",
  "company_name": "<company>",
  "website": "<company_domain>",
  "personalization": "<optional per-lead opener>",
  "lt_interest_status": 0,
  "skip_if_in_campaign": true,            // dedupe safety net
  "skip_if_in_workspace": true,
  "custom_variables": { "stage": "Qualified", "icp_score": 81, "hook": "...", "signal": "...", "activity_log": "2026-09-02: sourced + scored 81.", ... }
}
```
Adding the lead to the campaign is what starts outreach. Returns the lead object with its `id`. For a
batch, `POST /api/v2/leads/list` supports a bulk add payload.

### 2. `find_lead_by_domain(domain)`
`POST /api/v2/leads/list` with a filter:
- domain given: `{ "search": "<domain>" }` (matches on email domain / website), then filter the
  results to `website` or email domain == `<domain>` in the skill.
- company name only: `{ "search": "<company name>" }`.
- To check a specific address: `{ "search": "<email>" }` or `GET /api/v2/leads/{id}` if the id is known.
Zero results -> nothing.

### 3. `list_leads(filter)`
`POST /api/v2/leads/list`
- body: `{ "campaign": "<INSTANTLY_CAMPAIGN_ID>", "limit": 100 }`, plus optional
  `"lt_interest_status": <n>` or `"filter"` for Instantly's own lead states.
- pagination: cursor via `starting_after` = the `id` of the last lead in the previous page
  (`limit` per page).
- **Partial:** Instantly filters on its own lead status (`active`, `completed`, `replied`,
  `bounced`, `unsubscribed`), not on the contract `Stage` and not on `next_action_date`. To get the
  `/lead-outreach` "due for a touch" queue, list the campaign's `active` leads and let Instantly's
  scheduler decide sends. To get the `/lead-pipeline` "everything" view, page the full campaign and
  read `custom_variables.stage` per lead.

### 4. `update_lead(id, fields)`
`PATCH /api/v2/leads/{id}` with the mapped fields. Plain fields go top-level
(`first_name`, `company_name`, `website`); everything else goes inside `custom_variables` (send the
full custom_variables object you want the lead to end up with).

### 5. `set_stage(id, stage)`
1. Always: `PATCH /api/v2/leads/{id}` with `custom_variables.stage = "<stage>"`.
2. If the stage has a native analogue, also set it:
   - `Call Booked` -> `POST /api/v2/leads/update-interest-status` `{ "lead_email": "<email>", "interest_value": 2 }`
   - `Won` -> `interest_value: 4`
   - `Lost` -> `interest_value: -3`
   - `Replied` is set by Instantly automatically, do not write it.
3. `Disqualified` / `Nurture`: also remove the lead from the sending campaign
   (`POST /api/v2/leads/move` to a holding list, or pause) so no more emails go out.

### 6. `append_activity(id, line)`
No log field. Read-modify-write the custom variable:
1. `GET /api/v2/leads/{id}` -> read `custom_variables.activity_log`.
2. New value = old + `"\n"` + `line`.
3. `PATCH /api/v2/leads/{id}` with `custom_variables.activity_log = "<whole value>"`.
If a light sheet is kept alongside (see Stage mapping), append there too.

### 7. `report_metrics(since)`
`GET /api/v2/campaigns/analytics/overview?id=<INSTANTLY_CAMPAIGN_ID>&start_date=<since>&end_date=<today>`
- Gives `contacted_count`, `open_count`, `reply_count`, `bounced_count`, and interest totals
  (`total_opportunities`, `total_meeting_booked`, `total_closed`, ...). Good for
  `touches_since` (~ emails sent in window, also `GET /api/v2/campaigns/analytics/daily`) and
  `replies_since` (`reply_count`).
- **Partial:** `stage_counts` for the late funnel (`Proposal Sent`, `Won`, `Lost`, `Nurture`) is not
  in analytics. Derive it by paging `list_leads` and tallying `custom_variables.stage`, or from the
  light sheet. Return `null` for any count that cannot be derived and let the skill fall back.

## Sending consequence (for `/lead-outreach`)

When `crm_target: instantly`, the adapter owns sending. `/lead-outreach` must **not** call the Gmail
MCP for that client. Instead:

1. The skill still does its drafting work (pick framework, personalization level, voice check) but
   the output is the **campaign sequence** copy, authored once in Instantly with `{{hook}}`,
   `{{signal}}`, `{{first_name}}` merge fields, or a per-lead `personalization` string passed on
   `create_lead`.
2. First touch + all 5 follow-ups are sent by Instantly's sequence on its own schedule. The
   `docs/outreach-playbook.md` cadence (Day 0 / +3 / +7 / +14 / +24) is configured as the campaign's
   sequence steps and sending window, not driven per-run by the skill.
3. Stop-on-reply is automatic in Instantly (the lead pauses on reply).
4. `/lead-outreach` per run becomes: pull `Qualified` leads, `create_lead` each into the campaign
   (which begins outreach), `set_stage` -> `Contacted` is then driven by Instantly's `email_sent`
   event (read back via `list_leads` / webhooks), `append_activity` a line noting the lead entered
   the campaign.
5. LinkedIn leads are unaffected: Instantly is email-only, the skill still outputs LinkedIn text for
   manual send and tracks those leads via the light sheet or a non-sending Instantly list.
