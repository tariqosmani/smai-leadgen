# CLAUDE.md

Router for Claude Code in the Smart AI Workspace **lead generation system**. Detail lives in `docs/` and `references/` — read the relevant file before working in that area.

## What this is

A founder-led outbound lead engine for **Smart AI Workspace** (Tariq Osmani) — a B2B AI automation consultancy, not a SaaS. The system sources prospects in 6 target industries, qualifies and scores them, runs multi-channel outreach in Tariq's voice, tracks the pipeline in one Airtable table, and drafts proposals with the value-based pricing method.

- **Goal (this quarter):** close the first paying deal. Every skill serves that.
- **Business context of record:** `../Smart_AI_Workspace_Website` (offer, industries, pricing) and `../Tariq_Osmani_OS` (voice, connections, the Three Ms operating brain).
- **Channels:** cold email + LinkedIn (outbound) and Upwork (inbound job posts). No website-inbound work here — the site's contact form already routes to Resend.

## The funnel → one skill per stage

| # | Stage | Skill | Does |
|---|-------|-------|------|
| 1 | Source + qualify | `/lead-find` | Explorium/Vibe Prospecting: find decision-makers by title + industry + intent → enrich email + LinkedIn → dedupe → ICP score → hook → create Airtable records |
| 2 | Outreach | `/lead-outreach` | send email (autonomous, signed as Tariq) / draft LinkedIn text, follow-up cadence, log touches on the record |
| 3 | Manage | `/lead-pipeline` | daily action list, stale/cold flags, stage counts + conversion rates |
| 4 | Convert | `/lead-proposal` | discovery notes → 3-option fixed-scope proposal in a Google Doc |
| 5 | Upwork | `/upwork-proposal` | job post → fit check → short tailored proposal → log as `channel=upwork` |

Typical day: `/lead-pipeline` → do what it says (usually `/lead-outreach`, sometimes `/lead-find` to refill the top).

## Data store

One Airtable table: **Lead Pipeline** in the **SmartAI Listings Database** base (`AIRTABLE_BASE_ID` / `AIRTABLE_TABLE`), reached through the Airtable MCP (`mcp__airtable__*`). One record = one prospect, with real typed columns (Stage, ICP Score, Channel, Industry, Next Action Date, Activity Log, ...). Full layout in [docs/pipeline-schema.md](docs/pipeline-schema.md). The old ClickUp `🎯 Lead Pipeline` list is now empty and unused; the `Ecommerce_Leads` Google Sheet is left alone.

## Documentation map

| Area | Doc |
|---|---|
| Table fields, stages, dedupe rule | [docs/pipeline-schema.md](docs/pipeline-schema.md) |
| Who to target, exclusions, intent signals | [docs/icp.md](docs/icp.md) |
| ICP Score 0–100 rubric | [docs/scoring.md](docs/scoring.md) |
| Channels, cadence tables, voice rules | [docs/outreach-playbook.md](docs/outreach-playbook.md) |
| Tariq's voice register | [references/voice.md](references/voice.md) |
| Value-based pricing method (proposals) | [references/pricing-playbook.md](references/pricing-playbook.md) |
| Portfolio proof points (what you may cite) | [references/portfolio.md](references/portfolio.md) |

## Guardrails

- **Voice:** never use em dashes (—) in any outreach or proposal copy. No AI filler ("I hope this finds you well", "wanted to reach out", "leverage synergies"). Lead with the prospect's situation. Full list in `docs/outreach-playbook.md` — a draft that fails it gets rewritten, not shown.
- **Honesty:** no paying-client case study exists yet. Never imply past client results or name clients. "Built and shipped X" is fine; "helped Y achieve Z" is not. See `references/portfolio.md`.
- **Bike Method (from the Three Ms):** Phase 3 (autonomous send) — AI drafts *and sends* email outreach without per-message approval, signed as Tariq, from `info@smartaiworkspace.tech`. Authorized by Tariq 2026-09-03. Every send is logged to the lead's Activity Log with the Gmail thread id; Tariq spot-checks the sent folder + pipeline. Guardrails still hard: voice rules, honesty, dedupe/collapse (one contact per company per week — don't cold-email a second person at a company just contacted), stop-on-reply. LinkedIn stays manual. To roll back to draft-and-review, set `bike-method-phase: 2` in the `lead-outreach` skill and restore the review step.
- **Pricing:** no price before discovery. Proposals price from the client's own value numbers, never from the reference ranges (those are a sanity check). If value < cost floor, there's no deal at that scope — say so.
- **Dedupe:** before creating any lead record, normalize the company website (`scripts/normalize.py`) and search the Airtable table (`filterByFormula` on `{Company Website}`). Never create a second record for a company already in the pipeline. Pass a prior `/lead-find` run's Explorium `dataset_id` as `exclude_key` to skip already-seen prospects.
- **Credits:** Explorium contact enrichment costs ~3 credits per lead. `/lead-find` always shows the estimate and waits for a yes before `export-to-csv`. It reports credits spent + remaining.
- **Intern Rule:** email outreach is drafted and sent by the system on Tariq's behalf, signed as Tariq (Phase 3, see Bike Method above). LinkedIn is ToS-sensitive: the system outputs paste-ready text and Tariq sends it by hand. Every reply is human — the cadence stops on any reply and Tariq takes the conversation.
- **Don't edit the sibling repos** (`../Smart_AI_Workspace_Website`, `../Tariq_Osmani_OS`) from here. Read only.

## Environment + connections

- `.env` (see `.env.example`) — really just `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE`, `OUTREACH_FROM_*`, and optional Upwork keys. The Airtable token lives in `.mcp.json` (gitignored). LLM keys come from `../Tariq_Osmani_OS/.env`.
- **Explorium / Vibe Prospecting MCP** (`mcp__claude_ai_Vibe_Prospecting__*`) — sourcing + email/LinkedIn enrichment. Credit-based.
- **Airtable MCP** (`mcp__airtable__*`) — the pipeline store (`Lead Pipeline` table in the `SmartAI Listings Database` base). Runs from `.mcp.json` via `npx airtable-mcp-server`.
- **Gmail MCP** (`mcp__claude_ai_Gmail__*`) — sends outreach via `send_message` from `info@smartaiworkspace.tech` (the connected account's send identity; `.env` says `tariq@` but the account sends as `info@`). Follow-ups thread with `replyThreadId`.
- **Google Drive MCP** — proposal docs. The `gws` CLI (`../Tariq_Osmani_OS/cli/gws.exe`) is a fallback if authed.
- Drafting (hooks, emails, proposals) = Claude. Bulk scoring/classification = Groq / OpenRouter free tier.
- `python scripts/normalize.py` runs the dedupe self-check.

## Superseded

This repo's `/lead-find` and `/lead-outreach` replace the OS repo's `lead-generator` and `cold-email` skills. Once this is running, delete those two from `../Tariq_Osmani_OS/.claude/Skills/` (Tariq does that — not from here).

## Optional agent delegation

`sales-outbound-strategist` (sequences, signals), `sales-proposal-strategist` (proposal framing), `sales-pipeline-analyst` (funnel diagnostics), `business-strategist` (ICP). Delegate only when the task is genuinely strategy design, not routine execution.
