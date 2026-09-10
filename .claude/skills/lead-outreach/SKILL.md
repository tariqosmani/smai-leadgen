---
name: lead-outreach
description: "Draft and send first-touch + follow-up outreach for the active client's leads across email and LinkedIn. Reads Qualified / Contacted leads from the active client's pipeline (via the pipeline adapter), picks a cold-email framework (PAS, BAB, QVC, SCQ, 3C's, and others) and a personalization level per lead, drafts channel-appropriate messages in the client's voice from the lead's Hook + Signal, writes short internal-looking subject lines, sends the email via the Gmail MCP from the client's sending address (autonomous, signed as the client's founder) unless the adapter owns sending, outputs LinkedIn text for manual send (or a HeyReach-ready CSV when the client is on linkedin_mode: heyreach, see docs/linkedin-automation.md), runs a 5-touch angle-rotated cadence, and updates the lead record (stage, activity log, next action date, next action). Supersedes the OS cold-email skill."
bike-method-phase: 3
---

# Lead Outreach

> Invoke with `/lead-outreach` (batch of 10) or "run outreach". Full funnel stage 2 of 5.
> Arg `allow_unknown=false` blocks sends to `email_status: unknown` addresses (default: allowed, noted in the log). See step 4.

## Client config
Resolve the active client: a `client=<slug>` invocation arg wins, else `ACTIVE_CLIENT` in `.env`. Then read:
- `clients/<client>/voice.md`: the client's register
- `clients/<client>/offer.md`: Portfolio proof points (the only proof you may cite)
- `clients/<client>/identity.md`: business name, from-name / from-email / reply-to, CRM base + table, `linkedin_mode` (`manual` default, or `heyreach`; see `docs/linkedin-automation.md`)

## Read first
- `docs/outreach-playbook.md`: cadence table + the hard voice rules (apply to every client)
- `docs/pipeline-contract.md`: the pipeline operations this skill performs
- `docs/pipeline-schema.md`: field reference (Airtable layout)
- `docs/email-verification.md`: the `email_status` pre-send guard (step 4) and `scripts/verify_email.py`

## Writing craft (read before drafting)
The email itself is the job. Four references in this skill's `references/`:
- `frameworks.md` — 13 cold-email structures with a picker table. PAS is the default. Pick one, do not freewrite.
- `personalization.md` — the 4-level system + the research-signal stack. The opener must connect to the problem, not just grab attention. Run the "So what?" test.
- `subject-lines.md` — 2 to 4 words, lowercase, looks like an internal note. No first name, no product, no em dash.
- `follow-up-sequences.md` — the angle per touch (new value -> proof -> new insight -> breakup), the breakup email, phrases that kill reply rates.

## Config
Pipeline reads and writes go through the **pipeline adapter** for the active client's `crm_target`
(`clients/<client>/identity.md`): operations in `docs/pipeline-contract.md`, mapping in
`docs/pipeline-adapters/<crm_target>.md`. For `smart-ai-workspace` that is `airtable` (Airtable MCP
`mcp__airtable__*`, base + table from `identity.md`).
Email = **Gmail MCP** (`mcp__claude_ai_Gmail__send_message`, sends from the `from-email` in `identity.md`),
**unless the adapter owns sending** (e.g. `crm_target: instantly`): then the campaign sends the sequence
and Gmail is not used for that client (see the adapter doc). LinkedIn = text output, the founder sends by hand.

## Send mode: Phase 3 (autonomous)
Email touch 1 + follow-ups send without per-message approval, signed as the client's founder (`identity.md`) (authorized 2026-09-03, see CLAUDE.md Bike Method). Still hard: the voice checklist, honesty rules, stop-on-reply, and **one contact per company per week** — never cold-email a second person at a company already contacted in the last 7 days; queue them instead (`Next Action Date` +7). Print what was sent for the record. Roll back by setting `bike-method-phase: 2` and restoring the review step in Step 3.

## Steps

### 1. Pull the work list
**Deliverability gate (email channel):** if the last `## Deliverability checks` line in `clients/<client>/infrastructure.md` records a **RED** verdict, do not send email for this client. Report "email sends paused, last /deliverability-monitor verdict RED" and process LinkedIn drafts only. No `infrastructure.md` or no check line: proceed. (CLAUDE.md > Guardrails > Deliverability.)

`list_leads` via the pipeline adapter. Select records where `stage` is:
- `Qualified` → needs touch 1, or
- `Contacted` with `next_action_date` ≤ today and `activity_log` shows < 5 emails sent → needs the next follow-up.

Skip `Replied` / `Call Booked` / `Proposal Sent` / closed, Tariq owns those. Also skip `Qualified` leads whose company was contacted in the last 7 days (queue per Step 5). Sort by `icp_score` desc, take 10.
State the work list for the record: "10 queued: 6 first-touch, 4 follow-ups. 8 email, 2 LinkedIn." (Phase 3: continue straight to Step 2.)

**Suppression check** (localized, independent of any email-verification step): drop any lead whose
`email`, or whose company domain, is listed in `clients/<client>/suppress.md` (one entry per line: a
full `email` or an `@domain`; `#` starts a comment; case-insensitive; read the token before any inline
`#`). These are unsubscribes and hard bounces recorded by `/lead-replies`. Never email a suppressed
address, first touch or follow-up.

### 2. Draft each (touch N = emails-sent-so-far + 1)
1. **Framework** — pick from the table in `references/frameworks.md` by lead type: C-suite + brief → QVC / Mouse Trap; strong `Signal` → SCQ / PPP; services pitch on a real build → 3C's; problem-aware default → PAS.
2. **Personalization** — the highest level the data supports (`references/personalization.md`), built from `Signal` + `Hook` + one concrete detail you can verify (their site, a hire, their stack). The opener must pass the "So what?" test and connect to the problem.
3. **Body** — the framework shape, the industry pain from `clients/<client>/icp.md`, at most one portfolio proof from `clients/<client>/offer.md` ("built and shipped X", never a client name or an invented number). One ask, interest-based ("worth a look?" beats "got 15 minutes Tuesday?").
4. **Subject** (touch 1 only) — `references/subject-lines.md`: 2 to 4 words, lowercase, internal-looking, about their situation. Follow-ups reply in-thread and keep the subject.
5. **Follow-up angle** — the row for touch N in `references/follow-up-sequences.md`. One new value proposition per email. Never "just checking in".

Run every draft through the voice checklist in `outreach-playbook.md`. **Any rule fails → rewrite.** No em dash anywhere, subject included.

### 3. Self-check the batch
For each draft confirm: framework fits the lead type, opener passes the "So what?" test and ties to the problem, subject is 2 to 4 lowercase words about their situation, only real portfolio proof (no client names / invented numbers), no AI filler, no em dash. A draft that fails is rewritten, not sent. Drop any lead whose company was already contacted in the last 7 days (queue it, Step 5). Drop any lead now hitting `clients/<client>/suppress.md` (Step 1).

### 4. Send / output text
If the adapter owns sending (`crm_target: instantly`): skip Gmail. `create_lead` pushes the lead into
the campaign (if not already there) and the campaign sends the sequence, per
`docs/pipeline-adapters/instantly.md`. The bullets below are for a Gmail-sending client.
- **email verification guard (hard, email channel only):** before any Gmail send, check the lead's `email_status`. If the `Activity Log` shows no prior verification, run `scripts/verify_email.py` now and write the result. `invalid` → **do not send**: `next_action` → "find new contact" (same as a bounce), `append_activity` `YYYY-MM-DD: email skipped, address <status> (<reason>)`, Stage unchanged, drop from this batch. `unknown` → send by default (note `unknown` in the logged line); `allow_unknown=false` → skip it exactly like `invalid`. `catchall` / `valid` → send, note the status in the log. Full rules: `docs/email-verification.md`.
- **email touch 1:** `mcp__claude_ai_Gmail__send_message` (to, subject, body). Sends from the `from-email` in `clients/<client>/identity.md`. Capture the returned `threadId`.
- **email follow-up:** `mcp__claude_ai_Gmail__send_message` with `replyThreadId` = the `threadId` from the record's `Activity Log` so it threads and keeps the subject.
- **linkedin:** `linkedin_mode: manual` (default) → print the text + profile URL in a copy block. Connection note ≤ 300 chars, no link. `linkedin_mode: heyreach` → do not print inline; add the lead to the HeyReach export batch (CSV row: name, linkedin_url, company, hook; plus each touch's message copy). Still no autonomous LinkedIn send. See `docs/linkedin-automation.md`.
- **HeyReach batch (when `linkedin_mode: heyreach`):** after every lead in the run is processed, output the accumulated batch as one copy-paste CSV block (columns: name, linkedin_url, company, hook, touch_1 ... touch_4), or write it to `clients/<client>/linkedin-heyreach-<YYYY-MM-DD>.csv` (prospect PII, keep it local, do not commit it). Follow it with the steps to load the CSV into the client's HeyReach campaign. This replaces the inline LinkedIn paste blocks for the run; email sending is unchanged.

### 5. Update the lead record
Per sent message, via the pipeline adapter: `set_stage` → `Contacted`; `update_lead` with
`next_action_date` → today + cadence gap and `next_action` → the next step in words; `append_activity`
`YYYY-MM-DD: email touch N SENT (gmail thread <threadId>)`. The thread id is needed to thread the next
follow-up. On `airtable` these are one `update_records` call (see the adapter doc).
Queued (company contacted <7d ago): `stage` stays `Qualified`, `next_action_date` → +7, `next_action` → "multi-thread touch 1, primary contact emailed <date>".
Touch 5 done → clear `next_action_date`, `next_action` → "await reply / close in 90d". Bounce → note it, `next_action` → "find new contact".
Verification-skipped (the step 4 email guard): that guard already wrote `next_action` and the log line. Leave Stage as it was, do not `set_stage` → `Contacted`, do not advance `next_action_date`.

### 6. Report
`4 emails SENT (Acme Co, Beta Inc, ...) · 2 queued (company contacted <7d) · 1 skipped (email invalid, needs new contact) · 2 LinkedIn texts below · follow-ups due <date>.`
On `linkedin_mode: heyreach`, the LinkedIn part reads `· HeyReach CSV: 2 leads (load into the campaign)` instead of the inline texts.

## Idempotency
Re-running the same day re-selects only records still due. Every send is logged via `append_activity` as `... touch N SENT (gmail thread ...)`, so a re-run reads the log first and never double-sends a touch.

## Delegate (optional)
Sequence strategy / objection angles → `sales-outreach` or `sales-outbound-strategist`.
