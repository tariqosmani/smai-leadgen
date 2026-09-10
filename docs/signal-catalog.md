# Buying-signal catalog

Which real-world events count as a buying signal, how Explorium surfaces each one, and what a
signal does to scoring, hook framing, and cadence. `/lead-find` reads this to turn a `signals=`
arg into Explorium filters and to compose the `signal` string during sourcing. `/lead-signals`
reads it to re-scan the existing pipeline for fresh signals. This file is the mapping. It cites
`clients/<client>/scoring.md`, `docs/outreach-playbook.md`, and `docs/pipeline-contract.md` for
the downstream rules, it does not restate them.

## The signal field

`signal` is a normalized contract field (`docs/pipeline-contract.md`), Airtable column `Signal`
(`docs/pipeline-schema.md`). One short readable line, not raw event JSON. Auto-populated by
`/lead-find` at sourcing and by `/lead-signals` on a re-scan. Empty is normal: a plain
filter-only pull with no matching event leaves it blank, and a blank signal is always valid.

## Catalog

Event enum values below were read from the live MCP schemas of `fetch-businesses-events`,
`fetch-prospects-events`, and the `fetch-entities` `events` filter on 2026-09-10. Re-check with
a schema read before relying on a key Explorium adds or renames later.

| `signals=` value | What it is | Explorium source (sourcing filter, then event detail) | Real event / filter keys | Freshness window | `signal` string template |
|---|---|---|---|---|---|
| `funding` | raised capital or went public | `fetch-entities` `events` filter (businesses only), then `fetch-businesses-events`, or `enrich-business` `enrich-business-funding-and-acquisitions` | `new_funding_round`, `new_investment`, `ipo_announcement` | 90 days | `Funding: <round or amount if known>, <Mon YYYY>` e.g. `Funding: Series A, Mar 2026` |
| `job-change` | the decision-maker is new in seat | `fetch-entities` `current_role_months` `{lte: 6}` (prospects), then `fetch-prospects-events` on the contact | `prospect_changed_role`, `prospect_changed_company`, `prospect_job_start_anniversary` | 90 days for the event, 6 months for role tenure | `New in role: <title> since <Mon YYYY>` e.g. `New in role: VP Operations since Feb 2026` |
| `hiring` | hiring or headcount growth in a team | `fetch-entities` `events` filter (businesses only), then `fetch-businesses-events`, or `enrich-business` `enrich-business-workforce-trends` | `hiring_in_operations_department`, `hiring_in_sales_department`, `hiring_in_marketing_department`, `hiring_in_engineering_department`, `hiring_in_support_department` and the other `hiring_in_<dept>_department` keys; `increase_in_operations_department` and the other `increase_in_<dept>_department` keys; `increase_in_all_departments` | 90 days (`fetch-entities` `events` `last_occurrence` caps at 90) | `Hiring: <role or dept>, <Mon YYYY>` e.g. `Hiring: ops roles, Mar 2026` |
| `tech-stack` | adopted a tool that begs integration | `fetch-entities` `company_tech_stack_tech` filter (autocomplete the tool name), then `enrich-business` `enrich-business-technographics` / `enrich-business-webstack` / `enrich-business-website-changes` | no dedicated event type. `company_tech_stack_tech` is point-in-time; `enrich-business-website-changes` dates a recent stack change | 90 days for a dated change, else point-in-time | `Stack: runs <tool> (<paired gap>)` e.g. `Stack: runs HubSpot + Sheets` |
| `intent` | showing buying intent for the offer's topics | `fetch-entities` `business_intent_topics` filter (autocomplete the topic) | topic strings from `autocomplete` field `business_intent_topics`, e.g. `Marketing:Marketing Automation`, `Operations:Workflow Automation` | about 30 days (intent data refreshes roughly monthly) | `Intent: researching <topic>` e.g. `Intent: researching workflow automation` |

Mechanics:
- The `events` filter runs on `entity_type: businesses` only. An event-led pull fetches
  businesses with the `events` filter first, then refines to prospects with
  `businesses_reference_table` (`fetch-entities`). `intent`, `job-change`, and `tech-stack`
  filter directly on a prospects fetch.
- `fetch-entities` `events` `last_occurrence` takes 30 to 90 days. `fetch-businesses-events`
  and `fetch-prospects-events` take a `timestamp_from` date, so set it to today minus the
  freshness window.
- `/lead-signals` re-scans by domain: `match-business` on the pipeline's company domains (and
  `match-prospects` on the contacts) to get Explorium tables, then the two `*-events` tools.
- The event preview is free. The `export-to-csv` that carries the event columns is the charge,
  folded into the one `/lead-find` estimate. Never call the event tools speculatively.

## What a signal does downstream

| Signal | ICP Score | Hook angle (starting point, not a template) | Cadence urgency |
|---|---|---|---|
| `funding` | +8 in the Automation-intent dimension | new capital usually goes to headcount. The ops and back-office load is the part you automate instead of hiring for. | touch 1 within the 90-day window |
| `job-change` | +8 | the first weeks in the seat are when you set how the team runs. Cheaper to wire the workflow now than to unpick it later. | touch 1 within the 90-day window |
| `hiring` | +8 | you posted for <role>. Some of that work is repeatable enough to hand to a system, which changes how many people you need. | touch 1 within the 90-day window |
| `tech-stack` | +8 | you run <tool>. The manual glue between it and the rest of the stack is what we build. | point-in-time, no deadline, send on the next pull |
| `intent` | +8 (this is the prior `intent=true` behavior) | you have been looking at <topic>. Here is what a first build in that direction looks like for a team your size. | touch 1 while intent is warm, about 30 days |

Shared rules (cited, not restated here):
- **ICP Score:** the Automation-intent dimension is +8 per distinct signal, capped at 25, so
  three or more signals do not stack past the cap. Full rubric: `clients/<client>/scoring.md`
  > Automation-intent signals.
- **Hook:** lead with the signal, not with who the sender is, and keep the honesty rule:
  no invented client results, nothing past `clients/<client>/offer.md` > Portfolio proof
  points. Voice rules: `docs/outreach-playbook.md` > Voice rules.
- **Cadence:** the 5-touch structure in `docs/outreach-playbook.md` > Email cadence does not
  change. Only touch 1 timing and angle change. If the signal ages out of its window before a
  reply, the later touches drop the signal angle and run as the normal cadence.

## Fallbacks when Explorium does not cover it

| Gap | Fallback |
|---|---|
| hiring detail beyond department counts (specific posts, titles, dates) | Apollo `apollo_organizations_job_postings` on the company domain |
| funding not in Explorium yet | check by hand (Crunchbase, the company blog), or Apollo org enrichment |
| tech-stack recency | BuiltWith or Wappalyzer by hand, or `enrich-business-website-changes` |
| founder posting about ops pain | manual LinkedIn check, per `clients/<client>/icp.md` > Automation-intent signals |
| any signal, no MCP path | leave `signal` empty. Never guess one |
