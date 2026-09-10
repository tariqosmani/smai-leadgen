---
name: client-intake
description: "Guided onboarding interview that produces a ready-to-use clients/<slug>/ config for a new client, replacing the manual cp -r step in CLAUDE.md. Takes a <slug>, runs a batched questionnaire grouped by output file (identity, icp, scoring, voice, offer), then writes all five markdown files with the exact section headings scripts/check_client.py asserts, runs that check for the new slug, fills any gap it flags, and prints the manual onboarding steps that remain (set ACTIVE_CLIENT, confirm CRM wiring, run /inbox-setup). Every question accepts skip or use default. Writes only the new client's five files, never an existing client's, never .env or .mcp.json. Refuses an existing slug unless overwrite=true; resume=true re-asks only the sections that currently fail the check."
---

# Client Intake

> Invoke with `/client-intake <slug>` (e.g. `/client-intake acme`). One time, when onboarding a new client. Not a funnel stage. Replaces steps 1 and 2 of CLAUDE.md > "Onboard a new client": it writes and validates `clients/<slug>/{identity,icp,scoring,voice,offer}.md` from an interview, then hands back the steps that stay manual.

## Client config
This skill *creates* a client config, it does not resolve an active one.
- `<slug>` (required, first bare arg): the new client's folder name, `clients/<slug>/`. Lowercase, hyphenated.
- `overwrite=true`: allow writing over an existing `clients/<slug>/`. Without it, an existing folder is a hard stop.
- `resume=true`: keep the existing files, re-ask only the groups whose file currently fails `python scripts/check_client.py <slug>`, rewrite just those.
- Structural template of record: `clients/smart-ai-workspace/`. Mirror its headings and section order in all five files, replace its content with the interview answers.

## Read first
- `scripts/check_client.py` > `REQUIRED`: the exact substrings each of the five files must contain (case-insensitive). The files this skill writes MUST pass it. Also `check_crm()`: a non-`airtable` `crm_target` needs `docs/pipeline-adapters/<target>.md` to exist and `identity.md` to name the credential `.env` var(s) on a `crm_*_env` line.
- `clients/smart-ai-workspace/identity.md`, `icp.md`, `scoring.md`, `voice.md`, `offer.md`: the structure to mirror.
- `docs/pipeline-contract.md` + `docs/pipeline-adapters/`: the `crm_target` options (`airtable` and `instantly` wired, `hubspot` / `gohighlevel` stubs) for the identity.md CRM question.
- `CLAUDE.md` > "Onboard a new client": the steps that stay manual after the five files exist, printed back in Step 5.
- `CLAUDE.md` > Guardrails: no em dashes, no AI filler, founder-led honesty, no invented client results. Every word written into the client folder obeys these.

## Config
No MCP. The only command is `python scripts/check_client.py <slug>`. The skill reads the template client, runs the interview in the chat, and writes five markdown files with the Write tool.

## Steps

### 1. Resolve the slug
- No `<slug>` arg: ask for it and stop.
- `clients/<slug>/` exists and neither `overwrite=true` nor `resume=true` was passed: stop with
  `clients/<slug>/ already exists. Re-run with overwrite=true to replace it, or resume=true to fill only the failing sections.`
- `resume=true`: run `python scripts/check_client.py <slug>`, note which files it flags, ask only those groups in Step 2, carry the passing files through unchanged.

### 2. Interview (batched, grouped by output file)
Ask one file's group at a time as a numbered batch. Every question accepts `skip` (writes a `TODO:` line under the right heading, so the heading check still passes and Step 4 lists it) or `use default` (take the default shown). Ask the whole group, wait for the batch of answers, then move on. Keep this full checklist in the skill so nothing is dropped.

**Group A - identity.md**
1. Business name.
2. Founder name (the person who does the work and signs outreach).
3. `from-name` for outbound email. Default: the founder name.
4. `from-email` (the connected Gmail send address).
5. `reply-to`. Default: the `from-email`.
6. Primary website domain (bare, no scheme).
7. Secondary sending domains. Default: none.
8. `crm_target`: `airtable` (default), `instantly`, `hubspot` (stub), `gohighlevel` (stub).
   - `airtable`: Airtable base id + base name, and table name + table id.
   - non-`airtable`: the `.env` var name(s) that hold the credentials, e.g. `crm_api_key_env: ACME_API_KEY` (plus `crm_campaign_id_env:` for instantly). The secret value itself never goes in the file.
9. `booking_url` for discovery calls. Default: a `https://cal.com/REPLACE-ME/discovery-call` placeholder (with the placeholder, `/lead-replies` offers concrete slots instead of a link).

**Group B - icp.md**
10. Target industries, and the opening pain per industry if known.
11. Titles / seniority to target.
12. Company size: employee band and revenue band (ideal / acceptable / exclude).
13. Geographies (ideal / acceptable / exclude).
14. Hard exclusions (industries or company types that are an instant Disqualified).
15. Automation-intent signals that raise priority (hiring patterns, tech stack, funding, founder activity).

**Group C - scoring.md**
16. What makes a lead score high: the dimensions that matter and their rough weights. Default: the smart-ai-workspace rubric shape, Industry match 25, Company size 20, Geography 15, Automation-intent 25, Reachability 15.
17. What caps or zeroes a lead. Default: B2C / non-profit / gov scores 0 and is set to Disqualified; a generic inbox with no name scores 0 and is set to Disqualified.
18. Score bands. Default: 60 and up Qualified, 40 to 59 Nurture, below 40 Disqualified.

**Group D - voice.md**
19. Voice register in one sentence (how the founder sounds in writing).
20. 2 to 3 real writing samples, pasted (a real email, a real piece of site or post copy). Real only, never invented.

**Group E - offer.md**
21. What they sell, one paragraph (the result, not the build).
22. Service lines: name, slug, what each one covers.
23. Portfolio proof points: real projects only, what was built and the stack. No invented metrics or client results (CLAUDE.md > Guardrails: Honesty). If none exist yet, say so and write a "What NOT to claim yet" note.
24. Value-based pricing method. Default: the smart-ai-workspace method, quantify what the problem costs the business with the client before quoting, price inside the corridor between cost floor and first-year value, present three fixed-scope options, collect payment at signing and objective milestones. Note any client-specific deviation.

### 3. Write the five files
Into `clients/<slug>/`, mirroring `clients/smart-ai-workspace/` structure. Each file MUST contain the `check_client.py` substrings (case-insensitive):

| File | Required substrings | Headings to use |
|---|---|---|
| `identity.md` | `business name`, `founder`, `from-name`, `from-email`, `reply-to`, `crm_target` | `## Business`, `## Sending identity`, `## Booking`, `## CRM target` |
| `icp.md` | `industr`, `exclusi`, `intent signal` | firmographic table, `## Target industries`, `## Automation-intent signals`, `## Hard exclusions` |
| `scoring.md` | `rubric`, `banding` | `## Rubric` (the weighted dimensions), `## Banding` (the score to stage table) |
| `voice.md` | `voice` | `# Voice Register: <business name>`, `## Voice Samples` |
| `offer.md` | `service line`, `portfolio`, `pricing` | `## Service lines`, `## Portfolio proof points`, `## Pricing method` |

- Non-`airtable` `crm_target`: drop the Airtable base/table lines from `identity.md` and write the `crm_*_env` line(s) instead, e.g. `- **crm_api_key_env:** ACME_API_KEY`.
- Voice rules apply to every line: no em dashes, commas / periods / colons only, no AI filler.
- A skipped question writes a `TODO: <what is missing>` line under the right heading. The heading still satisfies the check; Step 4 lists the TODO.

### 4. Validate
`python scripts/check_client.py <slug>`.
- Report PASS, or the exact failing lines.
- On FAIL: add the missing heading or line and re-run until it passes. The one acceptable remaining failure is unset `crm_*_env` vars for a non-`airtable` target, those are a real onboarding step, carry them to Step 5.
- List every `TODO:` line written, so the operator knows what still needs a real answer before the client is run.

### 5. Print the steps that stay manual
From CLAUDE.md > "Onboard a new client":
1. Set `ACTIVE_CLIENT=<slug>` in `.env`, or pass `client=<slug>` per run.
2. `crm_target: airtable` -> confirm the Airtable token in `.mcp.json` can reach the new base. Non-`airtable` -> set the named `.env` var(s) and read `docs/pipeline-adapters/<target>.md`.
3. `/inbox-setup volume=<daily send target>` to stand up sending infrastructure. Run before the first `/lead-outreach`.
Then stop. This skill does not set `.env`, touch `.mcp.json`, or run `/inbox-setup`.

## Writes
- `clients/<slug>/identity.md`, `icp.md`, `scoring.md`, `voice.md`, `offer.md` for the new slug only.
- Nothing else. Never another client's files, never `.env`, never `.mcp.json`, no pipeline calls.

## Idempotency
- `clients/<slug>/` already exists: refuse unless `overwrite=true` (full re-interview, replaces the five files) or `resume=true` (re-ask only the groups whose file currently fails `check_client.py`, rewrite just those).
- A clean re-run with the same answers reproduces the same five files.

## Delegate (optional)
- ICP design (industries, firmographics, intent signals) for a client in an unfamiliar market: `business-strategist`.
- The value-based pricing method when it needs real modelling rather than the default: `specialized-pricing-analyst`.
