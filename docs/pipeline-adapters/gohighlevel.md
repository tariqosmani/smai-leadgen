# Pipeline adapter: gohighlevel (STUB)

Not yet wired. Implement when a client needs `crm_target: gohighlevel`.

GoHighLevel (HighLevel) maps reasonably: a lead is a **Contact** in a sub-account (location),
`stage` is an **Opportunity** stage inside a **Pipeline**, and the activity log is a **Note** on the
contact. Auth is OAuth 2.0 / a location API key (`Authorization: Bearer`), key from `.env` named by
`crm_api_key_env:` in `identity.md`; a `crm_location_id_env:` is also needed.

API area: HighLevel API v2 (`https://services.leadconnectorhq.com/`), `Version` header required.

| Operation | Not yet wired. When implementing, use: |
|---|---|
| `create_lead(lead)` | `POST /contacts/` (+ `POST /opportunities/` in the client pipeline) |
| `find_lead_by_domain(domain)` | `GET /contacts/?query=<domain or company>` or `POST /contacts/search` |
| `list_leads(filter)` | `GET /opportunities/search` by `pipelineStageId` / date, expand to contacts |
| `update_lead(id, fields)` | `PUT /contacts/{id}` (custom fields for anything non-standard) |
| `set_stage(id, stage)` | `PUT /opportunities/{id}` set `pipelineStageId`; map the contract vocabulary to stage ids |
| `append_activity(id, line)` | `POST /contacts/{id}/notes` (native append) |
| `report_metrics(since)` | `GET /opportunities/search` grouped by stage; message stats via the conversations API with a date filter |

Also decide: whether outreach sends via Gmail (yes by default, GHL does not own sending here) or via
GHL campaigns / workflows.
