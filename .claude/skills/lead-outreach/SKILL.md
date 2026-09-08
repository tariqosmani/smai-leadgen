---
name: lead-outreach
description: "Draft and send first-touch + follow-up outreach for Smart AI Workspace leads across email and LinkedIn. Reads Qualified / Contacted records from the Airtable Lead Pipeline, picks a cold-email framework (PAS, BAB, QVC, SCQ, 3C's, and others) and a personalization level per lead, drafts channel-appropriate messages in Tariq's voice from the lead's Hook + Signal, writes short internal-looking subject lines, sends the email via the Gmail MCP from info@smartaiworkspace.tech (autonomous, signed as Tariq), outputs LinkedIn text for manual send, runs a 5-touch angle-rotated cadence, and updates the Airtable record (Stage, Activity Log, Next Action Date, Next Action). Supersedes the OS cold-email skill."
bike-method-phase: 3
---

# Lead Outreach

> Invoke with `/lead-outreach` (batch of 10) or "run outreach". Full funnel stage 2 of 5.

## Read first
- `docs/outreach-playbook.md` — cadence table + the hard voice rules
- `references/voice.md`, `references/portfolio.md` (the only proof points you may cite)
- `docs/pipeline-schema.md`

## Writing craft (read before drafting)
The email itself is the job. Four references in this skill's `references/`:
- `frameworks.md` — 13 cold-email structures with a picker table. PAS is the default. Pick one, do not freewrite.
- `personalization.md` — the 4-level system + the research-signal stack. The opener must connect to the problem, not just grab attention. Run the "So what?" test.
- `subject-lines.md` — 2 to 4 words, lowercase, looks like an internal note. No first name, no product, no em dash.
- `follow-up-sequences.md` — the angle per touch (new value -> proof -> new insight -> breakup), the breakup email, phrases that kill reply rates.

## Config
`AIRTABLE_BASE_ID`, `AIRTABLE_TABLE`. Pipeline = **Airtable MCP** (`mcp__airtable__*`). Email = **Gmail MCP** (`mcp__claude_ai_Gmail__send_message`, sends from `info@smartaiworkspace.tech`). LinkedIn = text output, Tariq sends by hand.

## Send mode: Phase 3 (autonomous)
Email touch 1 + follow-ups send without per-message approval, signed as Tariq (authorized 2026-09-03, see CLAUDE.md Bike Method). Still hard: the voice checklist, honesty rules, stop-on-reply, and **one contact per company per week** — never cold-email a second person at a company already contacted in the last 7 days; queue them instead (`Next Action Date` +7). Print what was sent for the record. Roll back by setting `bike-method-phase: 2` and restoring the review step in Step 3.

## Steps

### 1. Pull the work list
`mcp__airtable__list_records` on the `Lead Pipeline` table. Select records where `Stage` is:
- `Qualified` → needs touch 1, or
- `Contacted` with `Next Action Date` ≤ today and `Activity Log` shows < 5 emails sent → needs the next follow-up.

Skip `Replied` / `Call Booked` / `Proposal Sent` / closed — Tariq owns those. Also skip `Qualified` leads whose company was contacted in the last 7 days (queue per Step 5). Sort by `ICP Score` desc, take 10.
State the work list for the record: "10 queued: 6 first-touch, 4 follow-ups. 8 email, 2 LinkedIn." (Phase 3: continue straight to Step 2.)

### 2. Draft each (touch N = emails-sent-so-far + 1)
1. **Framework** — pick from the table in `references/frameworks.md` by lead type: C-suite + brief → QVC / Mouse Trap; strong `Signal` → SCQ / PPP; services pitch on a real build → 3C's; problem-aware default → PAS.
2. **Personalization** — the highest level the data supports (`references/personalization.md`), built from `Signal` + `Hook` + one concrete detail you can verify (their site, a hire, their stack). The opener must pass the "So what?" test and connect to the problem.
3. **Body** — the framework shape, the industry pain from `icp.md`, at most one portfolio proof from `references/portfolio.md` ("built and shipped X", never a client name or an invented number). One ask, interest-based ("worth a look?" beats "got 15 minutes Tuesday?").
4. **Subject** (touch 1 only) — `references/subject-lines.md`: 2 to 4 words, lowercase, internal-looking, about their situation. Follow-ups reply in-thread and keep the subject.
5. **Follow-up angle** — the row for touch N in `references/follow-up-sequences.md`. One new value proposition per email. Never "just checking in".

Run every draft through the voice checklist in `outreach-playbook.md`. **Any rule fails → rewrite.** No em dash anywhere, subject included.

### 3. Self-check the batch
For each draft confirm: framework fits the lead type, opener passes the "So what?" test and ties to the problem, subject is 2 to 4 lowercase words about their situation, only real portfolio proof (no client names / invented numbers), no AI filler, no em dash. A draft that fails is rewritten, not sent. Drop any lead whose company was already contacted in the last 7 days (queue it, Step 5).

### 4. Send / output text
- **email touch 1:** `mcp__claude_ai_Gmail__send_message` (to, subject, body). Sends from `info@smartaiworkspace.tech`. Capture the returned `threadId`.
- **email follow-up:** `mcp__claude_ai_Gmail__send_message` with `replyThreadId` = the `threadId` from the record's `Activity Log` so it threads and keeps the subject.
- **linkedin:** print the text + profile URL in a copy block. Connection note ≤ 300 chars, no link.

### 5. Update the Airtable record
`mcp__airtable__update_records` per sent message: `Stage` → `Contacted`,
`Next Action Date` → today + cadence gap, `Next Action` → the next step in words, and append a line to
`Activity Log` (read it, add the line, write the whole field back):
`YYYY-MM-DD: email touch N SENT (gmail thread <threadId>)` — the thread id is needed to thread the next follow-up.
Queued (company contacted <7d ago): `Stage` stays `Qualified`, `Next Action Date` → +7, `Next Action` → "multi-thread touch 1, primary contact emailed <date>".
Touch 5 done → clear `Next Action Date`, `Next Action` → "await reply / close in 90d". Bounce → note it, `Next Action` → "find new contact".

### 6. Report
`4 emails SENT (Acme Co, Beta Inc, ...) · 2 queued (company contacted <7d) · 2 LinkedIn texts below · follow-ups due <date>.`

## Idempotency
Re-running the same day re-selects only records still due. Every send is logged to `Activity Log` as `... touch N SENT (gmail thread ...)`, so a re-run reads the log first and never double-sends a touch.

## Delegate (optional)
Sequence strategy / objection angles → `sales-outreach` or `sales-outbound-strategist`.
