---
name: upwork-proposal
description: "Turn an Upwork job post into a short, tailored proposal for the active client. Takes a pasted job post (or pulls recent jobs via the Upwork API if keys are set), checks it against the client's ICP and service fit, and for a good match drafts a 120-200 word proposal in the client's voice that answers the prospect's problem first, cites the closest portfolio build, and ends with 2-3 discovery questions. No pricing in the proposal. Logs the lead via the pipeline adapter with channel=upwork."
bike-method-phase: 2
---

# Upwork Proposal

> Invoke with `/upwork-proposal` then paste the job post, or `/upwork-proposal <url>`. Full funnel stage 5 of 5 (parallel channel).

## Client config
Resolve the active client: a `client=<slug>` invocation arg wins, else `ACTIVE_CLIENT` in `.env`. Then read:
- `clients/<client>/icp.md`: fit check + exclusions
- `clients/<client>/voice.md`: the client's register
- `clients/<client>/offer.md`: Portfolio proof points + Pricing method §1 (why no price yet) + service lines
- `clients/<client>/identity.md`: business name, CRM base + table

## Read first
- `docs/outreach-playbook.md` §Upwork — format rules

## Config
Pipeline reads and writes go through the **pipeline adapter** for the active client's `crm_target`
(`clients/<client>/identity.md`): operations in `docs/pipeline-contract.md`, mapping in
`docs/pipeline-adapters/<crm_target>.md`. For `smart-ai-workspace` that is `airtable`. Optionally
`UPWORK_*` keys in `.env`. Upwork leads go in the same pipeline as everything else, `channel` = `upwork`.

## Steps

### 1. Get the job(s)
- Default: Tariq pastes the job post text. Use it directly.
- If `UPWORK_*` keys are set and Tariq says "check the feed": query the Upwork GraphQL job-search API for recent posts matching `n8n`, `AI automation`, `workflow automation`, `Claude API`, `RAG`. Show titles + budgets, let Tariq pick.

### 2. Fit check (fast)
Score against `clients/<client>/icp.md`: is the prospect B2B, is the ask one of the service lines in `clients/<client>/offer.md`, is the budget/scope sane for value-based work (skip $50/hr data-entry gigs and $150 "quick fix" jobs), is it a real project not a fishing post. 
- **Poor fit** → say so in one line, suggest skip, stop.
- **Good fit** → continue.

### 3. Draft the proposal (120–200 words)
Structure (from `outreach-playbook.md` §Upwork):
1. First line answers *their* stated problem — no "I'm an expert in…". Show you read the specific post.
2. One short paragraph: how you'd approach it (concrete: the workflow shape, the tools), founder-led (you build it, no handoffs).
3. One sentence citing the closest `clients/<client>/offer.md` portfolio build.
4. 2–3 clarifying questions that start the discovery (volume, current process, which system is source of truth).
5. Sign off as the client's founder (`identity.md`). No price. No "I'm confident I can exceed your expectations."

Voice rules: no em dash, no AI filler, short sentences. Rewrite if it sounds generic.

### 4. Show + log
Print the proposal for Tariq to paste into Upwork. On his confirm ("sent"): `create_lead` via the pipeline
adapter, `company` = client/job name, `stage` `Contacted`, `channel` `upwork`, `source` `upwork`,
`next_action_date` today + 5, `hook` = the fit rationale, `signal` = the job summary, `activity_log` =
`YYYY-MM-DD: Upwork proposal sent`. If the post names a company, `find_lead_by_domain(<company name>)`
first and update that record instead of creating a duplicate.

### 5. On reply
Handled by `/lead-pipeline` → discovery call → `/lead-proposal` (the full 3-option doc, once it's a real opportunity).

## Delegate (optional)
Profile / portfolio-card copy → run `/catalog-project` in the OS repo. Proposal framing → `sales-proposal-strategist` agent.
