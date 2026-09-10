# CLAUDE.md

Router for Claude Code in this **lead generation system**. Detail lives in `docs/`, `clients/`, and the skills — read the relevant file before working in that area.

## What this is

A founder-led outbound lead engine, run for one **active client** at a time. Per-client business context (identity, ICP, scoring, voice, offer) lives in `clients/<slug>/`; global funnel logic and guardrails live in the skills and `docs/`. The system sources prospects in the client's target industries, qualifies and scores them, runs multi-channel outreach in the client's voice, tracks the pipeline in that client's CRM, and drafts proposals with the client's pricing method.

Ships with one client: **smart-ai-workspace** — a founder-led B2B AI automation consultancy (Tariq Osmani), not a SaaS. See `clients/smart-ai-workspace/`.

- **Goal (this quarter):** close the first paying deal for smart-ai-workspace. Every skill serves that.
- **Business context of record for smart-ai-workspace:** `../Smart_AI_Workspace_Website` (offer, industries, pricing) and `../Tariq_Osmani_OS` (voice, connections, the Three Ms operating brain). Read only.
- **Channels:** cold email + LinkedIn (outbound) and Upwork (inbound job posts). No website-inbound work here.

## Active client

Every skill run resolves one active client:

1. A `client=<slug>` argument on the invocation (e.g. `/lead-find marketing-agencies client=acme`) wins.
2. Otherwise `ACTIVE_CLIENT` in `.env` (`.env.example` ships it set to `smart-ai-workspace`).

The skill then reads `clients/<slug>/`:

| File | Holds |
|---|---|
| `identity.md` | business name, founder name, sending identity (from-name / from-email / reply-to), primary + secondary domains, `crm_target` (+ Airtable base ID and table name for an `airtable` client, or the `.env` var names for a non-`airtable` client) |
| `icp.md` | target industries, titles/seniority, size, geos, hard exclusions, intent signals |
| `scoring.md` | the 0–100 ICP scoring rubric |
| `voice.md` | the client's voice register + writing samples (global voice rules stay in Guardrails below) |
| `offer.md` | what the client sells, service lines, portfolio proof points, the value-based pricing method |

**Onboard a new client:**

1. `cp -r clients/smart-ai-workspace clients/<new-slug>` (or create the five files by hand).
2. Edit all five files for the new business. `identity.md` first: name, founder, sending identity, `crm_target` (+ base/table if `airtable`, else the `.env` var names).
3. Set `ACTIVE_CLIENT=<new-slug>` in `.env`, or pass `client=<new-slug>` per run.
4. `python scripts/check_client.py` asserts the five files exist with their required sections, and (for a non-`airtable` target) that the adapter doc exists and the named `.env` vars are set.
5. If `crm_target: airtable`, make sure the Airtable token in `.mcp.json` can reach the new base. If not `airtable`, add the adapter's `.env` var(s) and read `docs/pipeline-adapters/<target>.md`.
6. `/inbox-setup volume=<daily send target>` stands up cold-email sending infrastructure for the client: it sizes the setup, checks sending-domain availability and price via the Hostinger MCP, buys domains only on an explicit in-session yes to a shown total, auto-creates SPF / DMARC / MX / DKIM and a redirect to the primary site, and outputs the Google Workspace + Instantly/Smartlead warmup steps. Records what was provisioned in `clients/<slug>/infrastructure.md`. Run before the first `/lead-outreach`.

Global guardrails (below) are inherited automatically. Do not copy them into the client folder. `crm_target` selects the pipeline adapter (`docs/pipeline-adapters/`): `airtable` and `instantly` are wired, `hubspot` and `gohighlevel` are stubs.

## The funnel → one skill per stage

| # | Stage | Skill | Does |
|---|-------|-------|------|
| 1 | Source + qualify | `/lead-find` | Explorium/Vibe Prospecting: find decision-makers by title + industry + intent → enrich email + LinkedIn → verify email (`docs/email-verification.md`, invalids never reach outreach) → dedupe → ICP score → hook → create lead records via the pipeline adapter |
| 2 | Outreach | `/lead-outreach` | send email (autonomous, signed as the client's founder) / draft LinkedIn text, follow-up cadence, log touches on the record. Sends via the adapter's campaign when the adapter owns sending. |
| 2.5 | Triage replies | `/lead-replies` | read each Contacted lead's reply thread, classify it (interested / not-now / not-interested / unsubscribe / auto-reply / referral / bounce), route via the adapter (stage, nurture or retry date, suppression list); draft a booking reply for the founder to send. Never auto-answers. Companion to stage 3. |
| 3 | Manage | `/lead-pipeline` | daily action list, stale/cold flags, stage counts + conversion rates |
| 4 | Convert | `/lead-proposal` | discovery notes → 3-option fixed-scope proposal in a Google Doc |
| 5 | Upwork | `/upwork-proposal` | job post → fit check → short tailored proposal → log as `channel=upwork` |

Typical day: `/lead-pipeline` → do what it says (usually `/lead-outreach` or `/lead-replies`, sometimes `/lead-find` to refill the top).

Three skills sit outside the funnel, in the ops-health area. `/inbox-setup` stands up cold-email sending infrastructure (domains, mailboxes, SPF/DKIM/DMARC, warmup, rotation) once per client at onboarding. `/deliverability-monitor` is the recurring companion to it: run weekly or when reply rates drop, it re-checks bounce rate, auth + DNS drift, blocklist status, and the reply-rate trend against the thresholds in `.claude/skills/inbox-setup/references/deliverability.md` and returns a GREEN / YELLOW / RED verdict. Read-only on the pipeline and DNS; appends one line to `clients/<slug>/infrastructure.md`. `/lead-report` builds a weekly client-facing scorecard (a branded Google Doc plus a one-time Airtable Interface dashboard) from the same pipeline-adapter metrics as `/lead-pipeline`. It is read-only on the pipeline and honest about untracked metrics (Gmail sends have no open or click tracking).

## Data store

Per client, set by `crm_target` in `clients/<slug>/identity.md`. The skills never call a CRM directly:
they perform the operations in [docs/pipeline-contract.md](docs/pipeline-contract.md) through the
**pipeline adapter** for the active `crm_target` (`docs/pipeline-adapters/<target>.md`). `airtable`
(default) and `instantly` are implemented; `hubspot` and `gohighlevel` are documented stubs.

For `smart-ai-workspace` the target is `airtable`: one table, **Lead Pipeline** in the **SmartAI
Listings Database** base, through the Airtable MCP (`mcp__airtable__*`). One record = one prospect,
real typed columns (Stage, ICP Score, Channel, Industry, Next Action Date, Activity Log, ...). Full
layout in [docs/pipeline-schema.md](docs/pipeline-schema.md). If `crm_target: instantly`, outbound
email also sends through the Instantly campaign instead of Gmail (see the adapter doc).

## Documentation map

| Area | Doc |
|---|---|
| Active-client model + onboarding | this file > Active client |
| Pipeline operations + lead fields (target-neutral) | [docs/pipeline-contract.md](docs/pipeline-contract.md) |
| CRM adapters (airtable, instantly, hubspot, gohighlevel) | [docs/pipeline-adapters/](docs/pipeline-adapters/) |
| Table fields, stages, dedupe rule (Airtable) | [docs/pipeline-schema.md](docs/pipeline-schema.md) |
| Channels, cadence tables, hard voice rules | [docs/outreach-playbook.md](docs/outreach-playbook.md) |
| Cold-email infra: sizing, DNS auth, warmup, deliverability thresholds | `.claude/skills/inbox-setup/references/deliverability.md` |
| Weekly client report: metric definitions + dashboard spec | `.claude/skills/lead-report/references/metrics.md` |
| Inbound reply triage: the 7 classes + routing | `.claude/skills/lead-replies/references/classification.md` |
| Who to target, exclusions, intent signals | `clients/<slug>/icp.md` |
| ICP Score 0–100 rubric | `clients/<slug>/scoring.md` |
| Client voice register | `clients/<slug>/voice.md` |
| Offer, service lines, portfolio, pricing method | `clients/<slug>/offer.md` |
| CRM target, sending identity | `clients/<slug>/identity.md` |

## Guardrails

These apply to **every** client, regardless of what `clients/<slug>/voice.md` says.

- **Voice:** never use em dashes (—) in any outreach or proposal copy. No AI filler ("I hope this finds you well", "wanted to reach out", "leverage synergies"). Lead with the prospect's situation. Full list in `docs/outreach-playbook.md` — a draft that fails it gets rewritten, not shown.
- **Honesty:** never imply client results, name clients, or cite numbers beyond what the active client's `offer.md` > Portfolio proof points explicitly authorizes. "Built and shipped X" is fine; "helped Y achieve Z" is not. For `smart-ai-workspace`: no paying-client case study exists yet.
- **Bike Method (from the Three Ms):** Phase 3 (autonomous send) — AI drafts *and sends* email outreach without per-message approval, signed as the active client's founder (`identity.md`), from that client's `from-email`. Authorized by Tariq 2026-09-03. Every send is logged to the lead's Activity Log with the Gmail thread id; the founder spot-checks the sent folder + pipeline. Guardrails still hard: voice rules, honesty, dedupe/collapse (one contact per company per week — don't cold-email a second person at a company just contacted), stop-on-reply. LinkedIn stays manual. To roll back to draft-and-review, set `bike-method-phase: 2` in the `lead-outreach` skill and restore the review step.
- **Pricing:** no price before discovery. Proposals price from the client's own value numbers, never from the reference ranges (those are a sanity check). If value < cost floor, there's no deal at that scope — say so.
- **Dedupe:** before creating any lead record, normalize the company website (`scripts/normalize.py`) and search the CRM (for Airtable: `filterByFormula` on `{Company Website}`). Never create a second record for a company already in the pipeline. Pass a prior `/lead-find` run's Explorium `dataset_id` as `exclude_key` to skip already-seen prospects.
- **Credits:** Explorium contact enrichment costs ~3 credits per lead. `/lead-find` always shows the estimate and waits for a yes before `export-to-csv`. It reports credits spent + remaining.
- **Infrastructure spend:** `/inbox-setup` is the only skill that buys anything (sending domains, via the Hostinger MCP). It never purchases without an explicit in-session yes to an itemized total, mirroring the `/lead-find` credit gate. The Hostinger account has a default payment method, so a purchase call charges immediately: the gate is hard.
- **Deliverability:** a **RED** verdict from `/deliverability-monitor` pauses campaign email sends for the affected sending domain(s) until the cause is fixed (warmup keeps running). `/lead-outreach` does not send for a client whose last recorded verdict in `clients/<slug>/infrastructure.md` is RED. YELLOW means cut volume, do not stop.
- **Intern Rule:** email outreach is drafted and sent by the system on the founder's behalf, signed as the client's founder (Phase 3, see Bike Method above). LinkedIn is ToS-sensitive: the system outputs paste-ready text and the founder sends it by hand. Every reply is human — the cadence stops on any reply and the founder takes the conversation. `/lead-replies` classifies and routes every inbound reply (stage move, suppression, nurture date) but never answers one; a reply that needs a booking link is left as a Gmail draft for the founder to send.
- **Don't edit the sibling repos** (`../Smart_AI_Workspace_Website`, `../Tariq_Osmani_OS`) from here. Read only.

## Environment + connections

- `.env` (see `.env.example`) — `ACTIVE_CLIENT` plus optional Upwork keys. Per-client sending identity and CRM base/table live in `clients/<slug>/identity.md`. The Airtable token lives in `.mcp.json` (gitignored). LLM keys come from `../Tariq_Osmani_OS/.env`.
- **Explorium / Vibe Prospecting MCP** (`mcp__claude_ai_Vibe_Prospecting__*`) — sourcing + email/LinkedIn enrichment. Credit-based.
- **Airtable MCP** (`mcp__airtable__*`) — the pipeline store for `airtable` clients (the default adapter). Base ID + table from the client's `identity.md`. Runs from `.mcp.json` via `npx airtable-mcp-server`. Other `crm_target` values use their own adapter in `docs/pipeline-adapters/` (e.g. `instantly` = the Instantly API v2 over HTTPS, key in `.env`).
- **Gmail MCP** (`mcp__claude_ai_Gmail__*`) — sends outreach via `send_message` from the active client's `from-email` (`identity.md`). Follow-ups thread with `replyThreadId`.
- **Google Drive MCP** — proposal docs. The `gws` CLI (`../Tariq_Osmani_OS/cli/gws.exe`) is a fallback if authed.
- Drafting (hooks, emails, proposals) = Claude. Bulk scoring/classification = Groq / OpenRouter free tier.
- `python scripts/normalize.py` runs the dedupe self-check. `python scripts/check_client.py` checks the active client's config.

## Superseded

This repo's `/lead-find` and `/lead-outreach` replace the OS repo's `lead-generator` and `cold-email` skills. Once this is running, delete those two from `../Tariq_Osmani_OS/.claude/Skills/` (Tariq does that — not from here).

## Optional agent delegation

`sales-outbound-strategist` (sequences, signals), `sales-proposal-strategist` (proposal framing), `sales-pipeline-analyst` (funnel diagnostics), `business-strategist` (ICP). Delegate only when the task is genuinely strategy design, not routine execution.
