# Lead Generation System

Founder-led outbound lead engine, run for one **active client** at a time. Finds decision-makers in
the client's target industries, gets their email + LinkedIn, scores them, drafts outreach in the
client's voice, and tracks the pipeline in the client's CRM.

Ships with one client, **smart-ai-workspace** ([Smart AI Workspace](https://smartaiworkspace.tech),
Tariq Osmani's B2B AI automation consultancy). Per-client business context lives in `clients/<slug>/`.

Built as Claude Code skills over a handful of MCPs — human-in-the-loop, runs when invoked. No app to deploy.

| Job | Tool |
|---|---|
| Find people + email + LinkedIn | Explorium / Vibe Prospecting MCP (credit-based, ~3 credits/lead) |
| Pipeline / CRM | per client `crm_target` via a pipeline adapter (`docs/pipeline-adapters/`). smart-ai-workspace: `airtable`, the `Lead Pipeline` table. `instantly` also implemented; `hubspot` / `gohighlevel` stubbed |
| Outreach | Gmail MCP autonomous send, signed as the client's founder (or the adapter's own campaign when the adapter owns sending, e.g. `instantly`) |

## Setup

```bash
cp "../Tariq_Osmani_OS/.env" .env      # LLM keys
# then add to .env:  ACTIVE_CLIENT=smart-ai-workspace   (see .env.example)
python scripts/check_client.py          # active-client config check → "clients/<slug>/ OK"
python scripts/normalize.py             # dedupe self-check → "all checks passed"
```

A real `.env` must set `ACTIVE_CLIENT`. The per-client sending identity and CRM base/table now live in
`clients/<slug>/identity.md`, not `.env`.

The Airtable connector runs from `.mcp.json` (`npx airtable-mcp-server`) using a Personal Access Token
stored there — `.mcp.json` is gitignored. Needs Node.js. The other MCPs are connected at the Claude
level. For cold email deliverability, set the Gmail "send as" to the client's `from-email` domain
before running outreach.

## Clients

Each client is a folder of five markdown files (no YAML, no config parser):

```
clients/<slug>/
  identity.md   business name, founder, sending identity, crm_target (+ Airtable base/table)
  icp.md        target industries, titles, size, geos, exclusions, intent signals
  scoring.md    the 0-100 ICP scoring rubric
  voice.md      the client's voice register + writing samples
  offer.md      what they sell, service lines, portfolio proof, pricing method
```

**Onboard a new client:**

Fastest path: `/client-intake <slug>` runs a guided interview that writes all five files and validates them. By hand:

1. `cp -r clients/smart-ai-workspace clients/<new-slug>`
2. Edit all five files for the new business (start with `identity.md`).
3. `ACTIVE_CLIENT=<new-slug>` in `.env`, or pass `client=<new-slug>` on a single run
   (e.g. `/lead-find marketing-agencies client=<new-slug>`).
4. `python scripts/check_client.py` must print OK.
5. If `crm_target: airtable`, confirm the `.mcp.json` Airtable token can reach the new base. For any
   other target, name its `.env` var(s) in `identity.md`, set them in `.env`, and read
   `docs/pipeline-adapters/<target>.md`.
6. `/inbox-setup volume=<daily target>` to stand up sending domains, mailboxes, SPF/DKIM/DMARC, and
   warmup. Records the result in `clients/<new-slug>/infrastructure.md`.

Global guardrails (no em dashes, no AI filler, honesty, dedupe, Bike Method autonomous send) live in
[CLAUDE.md](CLAUDE.md) > Guardrails and apply to every client. Do not copy them into the client folder.

## Use

| Command | When |
|---------|------|
| `/client-intake <slug>` | Onboarding a client. Guided interview that writes and validates `clients/<slug>/`. |
| `/lead-pipeline` | Start of the workday. Tells you what to do next. |
| `/lead-find marketing-agencies` | Top of funnel is thin. Sources + enriches + scores new leads (shows credit cost first). |
| `/lead-import file=<csv>` | Ingest a warm list or a website visitor de-anonymization export instead of cold sourcing. |
| `/lead-signals` | Re-scan the existing pipeline for fresh buying signals (funding, job change, hiring, tech-stack) and re-activate leads. Shows credit cost first. |
| `/lead-outreach` | Draft + send the day's first-touches and follow-ups (batch of 10) via Gmail. |
| `/upwork-proposal` | Paste an Upwork job post → tailored proposal. |
| `/lead-proposal <company>` | After a discovery call → 3-option proposal as a Google Doc. |
| `/inbox-setup volume=50` | Onboarding a client. Stands up cold-email sending domains, mailboxes, DNS auth, warmup, rotation. Buys domains only on your explicit yes. |
| `/lead-report` | Weekly. Client-facing performance summary as a Google Doc, plus a live Airtable dashboard spec. Read-only. |

Every command runs against `ACTIVE_CLIENT`. Add `client=<slug>` to any invocation to override for one run.
Full routing and guardrails: [CLAUDE.md](CLAUDE.md).

## Layout

```
CLAUDE.md                    router + active-client model + onboarding
clients/<slug>/              per-client identity, icp, scoring, voice, offer
docs/pipeline-contract.md    target-neutral pipeline operations + lead fields
docs/pipeline-adapters/      one doc per crm_target (airtable, instantly, hubspot, gohighlevel)
docs/pipeline-schema.md      Airtable field reference
docs/outreach-playbook.md    global cadence + hard voice rules
data/seeds.csv               optional: specific companies to force into a /lead-find run
scripts/normalize.py         dedupe helper + self-check
scripts/check_client.py      active-client config check (+ CRM wiring check)
scripts/inbox_math.py        cold-email infra sizing (domains / mailboxes / warmup) + self-check
.claude/skills/              the 5 funnel skills + /inbox-setup (onboarding infra) and /lead-report (weekly client scorecard)
```

`/lead-report` appends one line per run to `clients/<slug>/report-log.md` (created on first run); `/inbox-setup` writes `clients/<slug>/infrastructure.md`. Both are per-client runtime records, not committed config.

## Status (2026-09-03)

Pipeline store moved from ClickUp to the Airtable `Lead Pipeline` table. The 5 leads from the first run
(Acme Co, Beta Inc, Gamma LLC, Delta Group, Epsilon Corp) are in Airtable;
4 have Gmail drafts ready. 150 Explorium credits left.

## Context sources (smart-ai-workspace only, read-only)

- `../Smart_AI_Workspace_Website` — the offer, 6 industries, pricing method
- `../Tariq_Osmani_OS` — voice, connections, the Three Ms operating brain

Replaces the `cold-email` and `lead-generator` skills in the OS repo.
