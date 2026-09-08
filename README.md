# Smart AI Workspace — Lead Generation System

Founder-led outbound lead engine for [Smart AI Workspace](https://smartaiworkspace.tech), Tariq Osmani's B2B AI automation consultancy. Finds decision-makers in 6 target industries, gets their email + LinkedIn, scores them, drafts outreach in Tariq's voice, and tracks the pipeline in Airtable.

Built as Claude Code skills over a handful of MCPs — human-in-the-loop, runs when invoked. No app to deploy.

| Job | Tool |
|---|---|
| Find people + email + LinkedIn | Explorium / Vibe Prospecting MCP (credit-based, ~3 credits/lead) |
| Pipeline / CRM | Airtable MCP — `Lead Pipeline` table in the `SmartAI Listings Database` base |
| Outreach drafts | Gmail MCP — drafts you review and send |

## Setup

```bash
cp "../Tariq_Osmani_OS/.env" .env      # LLM keys
# .env already has AIRTABLE_BASE_ID, AIRTABLE_TABLE and OUTREACH_FROM_* from .env.example
python scripts/normalize.py             # dedupe self-check → "all checks passed"
```

The Airtable connector runs from `.mcp.json` (`npx airtable-mcp-server`) using a Personal Access Token
stored there — `.mcp.json` is gitignored. Needs Node.js. The other MCPs are connected at the Claude
level. For cold email deliverability, set your Gmail "send as" to a `@smartaiworkspace.tech` address
before sending drafts.

## Use

| Command | When |
|---------|------|
| `/lead-pipeline` | Start of the workday. Tells you what to do next. |
| `/lead-find marketing-agencies` | Top of funnel is thin. Sources + enriches + scores new leads (shows credit cost first). |
| `/lead-outreach` | Draft the day's first-touches and follow-ups (batch of 10) into Gmail. |
| `/upwork-proposal` | Paste an Upwork job post → tailored proposal. |
| `/lead-proposal <company>` | After a discovery call → 3-option proposal as a Google Doc. |

Full routing and guardrails: [CLAUDE.md](CLAUDE.md).

## Layout

```
CLAUDE.md              router
docs/                  pipeline schema (Airtable), ICP, scoring rubric, outreach playbook
references/            voice, pricing playbook, portfolio (from sibling repos)
data/seeds.csv         optional: specific companies to force into a /lead-find run
scripts/normalize.py   dedupe helper + self-check
.claude/skills/        the 5 funnel skills
```

## Status (2026-09-03)

Pipeline store moved from ClickUp to the Airtable `Lead Pipeline` table. The 5 leads from the first run
(Acme Co, Beta Inc, Gamma LLC, Delta Group, Epsilon Corp) are in Airtable;
4 have Gmail drafts ready. 150 Explorium credits left.

## Context sources

- `../Smart_AI_Workspace_Website` — the offer, 6 industries, pricing method
- `../Tariq_Osmani_OS` — voice, connections, the Three Ms operating brain

Replaces the `cold-email` and `lead-generator` skills in the OS repo.
