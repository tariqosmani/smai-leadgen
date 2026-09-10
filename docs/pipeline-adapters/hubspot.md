# Pipeline adapter: hubspot (STUB)

Not yet wired. Implement when a client needs `crm_target: hubspot`.

HubSpot maps well to this contract: a lead is a **Contact** (optionally associated with a
**Company**), `stage` is a **deal stage** on an associated **Deal** in a pipeline, and the activity
log is a **Note** or **Engagement** on the contact. Auth is a private-app access token
(`Authorization: Bearer`), key from `.env` named by `crm_api_key_env:` in `identity.md`.

API area: HubSpot CRM API v3 (`https://api.hubapi.com/crm/v3/`).

| Operation | Not yet wired. When implementing, use: |
|---|---|
| `create_lead(lead)` | `POST /crm/v3/objects/contacts` (+ company + deal, with associations) |
| `find_lead_by_domain(domain)` | `POST /crm/v3/objects/contacts/search` on email domain, or companies search on `domain` |
| `list_leads(filter)` | `POST /crm/v3/objects/deals/search` by `dealstage` / properties, expand to contacts |
| `update_lead(id, fields)` | `PATCH /crm/v3/objects/contacts/{id}` (and/or the deal) |
| `set_stage(id, stage)` | `PATCH /crm/v3/objects/deals/{dealId}` set `dealstage`; map the contract vocabulary to the pipeline's stage ids |
| `append_activity(id, line)` | `POST /crm/v3/objects/notes` with an association to the contact (native append, no read-modify-write) |
| `report_metrics(since)` | deal search grouped by `dealstage`; engagements/emails via `POST /crm/v3/objects/emails/search` with a `hs_timestamp` filter |

Also decide: one pipeline per client vs shared; whether outreach still sends via Gmail (yes, HubSpot
does not own sending here) or via HubSpot Sequences.
