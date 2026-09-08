---
name: upwork-proposal
description: "Turn an Upwork job post into a short, tailored Smart AI Workspace proposal. Takes a pasted job post (or pulls recent jobs via the Upwork API if keys are set), checks it against the ICP and service fit, and for a good match drafts a 120-200 word proposal in Tariq's voice that answers the client's problem first, cites the closest portfolio build, and ends with 2-3 discovery questions. No pricing in the proposal. Logs the lead as an Airtable record with Channel=upwork."
bike-method-phase: 2
---

# Upwork Proposal

> Invoke with `/upwork-proposal` then paste the job post, or `/upwork-proposal <url>`. Full funnel stage 5 of 5 (parallel channel).

## Read first
- `docs/icp.md` — fit check + exclusions
- `docs/outreach-playbook.md` §Upwork — format rules
- `references/voice.md`, `references/portfolio.md`, `references/pricing-playbook.md` §1 (why no price yet)

## Config
`AIRTABLE_BASE_ID`, `AIRTABLE_TABLE`, and optionally `UPWORK_*` keys. Upwork leads go in the same
`Lead Pipeline` table as everything else, tagged `Channel` = `upwork`.

## Steps

### 1. Get the job(s)
- Default: Tariq pastes the job post text. Use it directly.
- If `UPWORK_*` keys are set and Tariq says "check the feed": query the Upwork GraphQL job-search API for recent posts matching `n8n`, `AI automation`, `workflow automation`, `Claude API`, `RAG`. Show titles + budgets, let Tariq pick.

### 2. Fit check (fast)
Score against `docs/icp.md`: is the client B2B, is the ask one of the 4 services, is the budget/scope sane for value-based work (skip $50/hr data-entry gigs and $150 "quick fix" jobs), is it a real project not a fishing post. 
- **Poor fit** → say so in one line, suggest skip, stop.
- **Good fit** → continue.

### 3. Draft the proposal (120–200 words)
Structure (from `outreach-playbook.md` §Upwork):
1. First line answers *their* stated problem — no "I'm an expert in…". Show you read the specific post.
2. One short paragraph: how you'd approach it (concrete: the workflow shape, the tools), founder-led (you build it, no handoffs).
3. One sentence citing the closest `references/portfolio.md` build.
4. 2–3 clarifying questions that start the discovery (volume, current process, which system is source of truth).
5. Sign off as Tariq. No price. No "I'm confident I can exceed your expectations."

Voice rules: no em dash, no AI filler, short sentences. Rewrite if it sounds generic.

### 4. Show + log
Print the proposal for Tariq to paste into Upwork. On his confirm ("sent"): `mcp__airtable__create_record`
in `Lead Pipeline` — `Company` = client/job name, `Stage` `Contacted`, `Channel` `upwork`, `Source` `upwork`,
`Next Action Date` today + 5, `Hook` = the fit rationale, `Signal` = the job summary, `Activity Log` =
`YYYY-MM-DD: Upwork proposal sent`. Dedupe on company name (`search_records`) if the post names one.

### 5. On reply
Handled by `/lead-pipeline` → discovery call → `/lead-proposal` (the full 3-option doc, once it's a real opportunity).

## Delegate (optional)
Profile / portfolio-card copy → run `/catalog-project` in the OS repo. Proposal framing → `sales-proposal-strategist` agent.
