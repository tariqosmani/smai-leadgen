# Identity: Smart AI Workspace

The business the skills act for when `ACTIVE_CLIENT=smart-ai-workspace`. Read by every
skill for the business name, the sending identity, and the CRM target.

## Business

- **Business name:** Smart AI Workspace
- **Founder name:** Tariq Osmani
- **Primary website domain:** smartaiworkspace.tech
- **Secondary sending domains:** none

## Sending identity

Used by `/lead-outreach` for the Gmail send and the signature, and by `/lead-proposal`
for the Google Doc title.

- **from-name:** Tariq Osmani
- **from-email:** info@smartaiworkspace.tech
- **reply-to:** tariq@smartaiworkspace.tech

`from-email` is the connected Gmail account's actual send identity. Outreach is signed
as the founder name above (Phase 3 autonomous send, see CLAUDE.md > Guardrails).

## Booking

Used by `/lead-replies` when a prospect who replied wants to schedule the discovery
call. Optional, and not required by `scripts/check_client.py`.

- **booking_url:** https://cal.com/REPLACE-ME/discovery-call

Placeholder, fill this in with Tariq's real scheduling link. Left as a placeholder or
blank, `/lead-replies` drafts 2 to 3 concrete time slots instead of a link.

## CRM target

Which pipeline store the skills read and write, via the adapter for this value
(`docs/pipeline-contract.md` = the operations, `docs/pipeline-adapters/<crm_target>.md` = the mapping).
`airtable` (default) and `instantly` are implemented; `hubspot` and `gohighlevel` are stubs.

- **crm_target:** airtable
- **Airtable base ID:** appMULkAmdFmneAyB  (base name: SmartAI Listings Database)
- **Airtable table name:** Lead Pipeline  (table id: tblHGHp4DthpNKAU9)

For a non-`airtable` target, drop the two Airtable lines and instead name the `.env` var(s) that
hold the credentials (the secret never goes in this file, `clients/` is committed). Example for
Instantly:

```
- **crm_target:** instantly
- **crm_api_key_env:** INSTANTLY_API_KEY
- **crm_campaign_id_env:** INSTANTLY_CAMPAIGN_ID
```

`python scripts/check_client.py` then asserts those vars are set and the adapter doc exists.
