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

## White-label

Optional, read only by `/lead-report`. When `white_label` is `true`, the weekly report Doc is
branded for an agency reselling this outbound service: the title and header use `end_client_name`,
a "Prepared by" line uses `prepared_by` and `agency_name`, `logo_url` is placed if set, and no
mention of the tooling, the vendor, or "Smart AI Workspace" appears in the Doc. Metrics, the
"not tracked" rules, the honesty rules, and the narrative voice do not change. Absent or
`white_label: false` (the default) is exactly the current behavior. Additive and optional,
`scripts/check_client.py` does not require this section. Full swap table:
`.claude/skills/lead-report/references/metrics.md` > White-label mode.

- **white_label:** false
- **agency_name:** REPLACE-ME Agency
- **end_client_name:** REPLACE-ME Client
- **prepared_by:** REPLACE-ME (person named on the report)
- **logo_url:** (optional) https://REPLACE-ME/logo.png

## Booking

Used by `/lead-replies` when a prospect who replied wants to schedule the discovery
call. Optional, and not required by `scripts/check_client.py`.

- **booking_url:** https://cal.com/REPLACE-ME/discovery-call

Placeholder, fill this in with Tariq's real scheduling link. Left as a placeholder or
blank, `/lead-replies` drafts 2 to 3 concrete time slots instead of a link.

## LinkedIn

Read by `/lead-outreach` to decide how LinkedIn touches are delivered. Optional, and
not required by `scripts/check_client.py`.

- **linkedin_mode:** manual

`manual` (the default, and the value when this line is absent) means `/lead-outreach`
prints paste-ready LinkedIn text and Tariq sends each message by hand. It is fully within
LinkedIn's User Agreement, so the account is never at risk. `heyreach` switches delivery
to a HeyReach-class automation tool: it needs `HEYREACH_API_KEY` in `.env` and a HeyReach
campaign for the client, and it carries the account risk that LinkedIn's ban on
automation implies. See `docs/linkedin-automation.md` before switching.

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
