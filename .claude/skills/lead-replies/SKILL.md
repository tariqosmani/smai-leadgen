---
name: lead-replies
description: "Triage inbound replies to the active client's outreach. Reads every Contacted lead's reply thread(s) via the Gmail MCP, classifies each new reply with judgment (interested, not-now, not-interested, unsubscribe, auto-reply, referral, bounce), and routes the lead through the pipeline adapter: stage move, nurture or retry date, and the suppression list for unsubscribes. Never answers a reply. For an interested prospect who asked to book, it leaves a Gmail draft offering the client's booking link or concrete slots, for the founder to send. Read-mostly on the pipeline (stage, activity log, next action); appends unsubscribes to clients/<client>/suppress.md; writes Gmail drafts only, never a send."
bike-method-phase: 2
---

# Lead Replies

> Invoke with `/lead-replies` (or "triage the replies"). Funnel stage 2.5: the companion to stage 3 (`/lead-pipeline`) that `/lead-pipeline` step 2 sends you to when replies are waiting, and it runs before stage 4 (`/lead-proposal`). The `/lead-outreach` cadence stops on any reply; this skill reads that reply and routes it. The founder still owns every actual reply conversation (CLAUDE.md > Intern Rule).

## Client config
Resolve the active client: a `client=<slug>` invocation arg wins, else `ACTIVE_CLIENT` in `.env`. Then read:
- `clients/<client>/identity.md`: `from-email` (the address outreach was sent from, so a reply is anything not from it), `booking_url`, business + founder name
- `clients/<client>/voice.md`: register for the booking draft
- `clients/<client>/offer.md`: Pricing method §1 (what the discovery call is for) + Reference ranges (the expected `deal_value` once a call is booked)

## Read first
- `docs/pipeline-contract.md`: the operations this skill performs (`list_leads`, `set_stage`, `append_activity`, `update_lead`) and the normalized lead fields
- `docs/pipeline-adapters/<crm_target>.md`: how those operations map for this client
- `docs/outreach-playbook.md` > After a reply: the flow this skill sits in
- `references/classification.md` (this skill): the cue list per class, the gist rule, and how to tell a "wants to book" reply from a plain yes

## Config
Pipeline reads and writes go through the **pipeline adapter** for the active client's `crm_target`
(`clients/<client>/identity.md`): operations in `docs/pipeline-contract.md`, mapping in
`docs/pipeline-adapters/<crm_target>.md`. For `smart-ai-workspace` that is `airtable` (Airtable MCP
`mcp__airtable__*`, base + table from `identity.md`).
Reply threads: **Gmail MCP** `mcp__claude_ai_Gmail__get_thread` (`messageFormat: PLAIN_TEXT`).
Booking drafts: `mcp__claude_ai_Gmail__create_draft` with `replyToMessageId` = the prospect's latest
message id. **This skill never calls `send_message`, `reply`, or any send.**
For `crm_target: instantly` the campaign auto-pauses a lead on reply and marks it replied; still run
this skill to classify and route (stage, suppression, nurture date), reading the reply text from the
thread or the Instantly lead. LinkedIn replies are out of scope (manual, per the Intern Rule).

## Steps

### 1. Find new replies
`list_leads` filtered to Stage `Contacted` via the adapter. For each lead:
1. Pull the Gmail thread id(s) from the `Activity Log` `... SENT (gmail thread <id>)` tokens (older lines: `gmail id <id>`). Note the date of the last logged touch.
2. `mcp__claude_ai_Gmail__get_thread(threadId, messageFormat: PLAIN_TEXT)` for each thread.
3. A **reply** is any message in the thread whose `sender` is not the client's `from-email`, dated after the last logged touch. A bounce arrives as a message from `mailer-daemon` / `postmaster` / `Mail Delivery Subsystem` (still a "reply" for routing).
4. **Idempotency gate:** if the `Activity Log` already carries a `reply received` / `unsubscribe` / `bounce` / `auto-reply, retry` line dated on or after the newest reply message, that reply is already processed. Skip it.

Leads with no new reply: nothing to do.

### 2. Classify each new reply
Claude judgment, cues in `references/classification.md`. Exactly one class per reply:
- `interested` - wants to talk, asks a question, proposes a time, "send more info"
- `not-now` - explicit "revisit in Qn / next quarter / after <event>"
- `not-interested` - a polite no, "not a fit", "we're set", no request to stop all contact
- `unsubscribe` - "remove me", "stop", "opt out", "unsubscribe", "do not contact", "this is spam"
- `auto-reply` - out-of-office, autoresponder, "<name> has left" with no replacement contact
- `referral` - "talk to <colleague>", hands you another named person / address
- `bounce` - mailer-daemon / delivery failure / mailbox full / address rejected

Write a one-line **gist**: <=12 words, the reply in plain words. No em dashes.

### 3. Route via the pipeline adapter
One combined write per lead where the adapter supports it (see the adapter doc). Every route appends a dated `Activity Log` line.

| Class | Route |
|---|---|
| `interested`, `referral` | `set_stage` `Replied`; `update_lead` `next_action` = "Tariq: reply to <name>, book discovery call", clear `next_action_date`; `append_activity` `YYYY-MM-DD: reply received, <class>, <gist>`. Surface at the top of the report. For `referral`, put the named person + address in the gist and Next Action so Tariq adds them; do not auto-create a lead. |
| `not-now` | Stage stays `Contacted`, cadence stops: `update_lead` `next_action_date` = the date the prospect named (else today +90d), `next_action` = "nurture, prospect said revisit <when>"; `append_activity` `YYYY-MM-DD: reply received, not-now, <gist>`. |
| `not-interested` | `set_stage` `Lost`; `append_activity` `YYYY-MM-DD: reply received, not-interested, <reason or "polite no">`. |
| `unsubscribe` | `set_stage` `Lost`; `append_activity` `YYYY-MM-DD: unsubscribe, suppressed`; add to `clients/<client>/suppress.md` (Step 5). |
| `auto-reply` | No stage change; `update_lead` `next_action_date` = today +7 (retry after the OOO; use the stated return date only if it is further out); `append_activity` `YYYY-MM-DD: auto-reply, retry <date>`. |
| `bounce` | Stage unchanged; `update_lead` `next_action` = "find new contact"; `append_activity` `YYYY-MM-DD: bounce, <reason>` (reason = the daemon's text, e.g. "550 mailbox not found"). Pre-send address verification is a separate agent's job; this handles only the runtime bounce that slipped through. |

### 4. Booking sub-flow (interested + wants to book only)
Only when an `interested` reply **proposes a time or asks how to book** (see `references/classification.md` > "Wants to book"). Draft a short reply in the client's voice (`voice.md`, plus the hard voice rules in `docs/outreach-playbook.md`):
- lead with their line ("Thursday works" / "how do we set this up"), not a greeting
- offer `identity.md` `booking_url` when it is a real link; when it is still the placeholder or blank, offer 2 to 3 concrete slots (Tue to Thu, 9 to 11am or 1 to 3pm, prospect-local, next week)
- one sentence on what the call covers (`offer.md` Pricing method §1: understand the problem before any number)
- sign as the founder (`identity.md`)

`mcp__claude_ai_Gmail__create_draft(replyToMessageId = <prospect's latest message id>, body = <the draft>)`. **Do not send.** Leave it in Gmail for Tariq.
Log it: `append_activity` `YYYY-MM-DD: booking draft created, awaiting Tariq send`.

### 5. Suppression list (unsubscribe only)
Append to `clients/<client>/suppress.md`, creating it if missing with this exact header:
```
# Suppression list

Emails and domains to skip in every /lead-find and /lead-outreach run for this client.
One entry per line: a full email, or @domain for the whole domain. `#` starts a comment.
```
Then add two lines (skip either line if it is already present, case-insensitive):
```
<prospect email>          # YYYY-MM-DD unsubscribe, <company>
@<prospect email domain>  # YYYY-MM-DD unsubscribe, <company> (<prospect email> asked out)
```
Append only. Never remove a line from this file.

### 6. Report
A table, one row per reply found this run:

| Company | Contact | Class | Action taken |
|---|---|---|---|
| Acme | Jane Doe | interested | Stage -> Replied; booking draft waiting |
| Globex | Bob Lin | not-now | nurture, revisit 2026-01 |
| Initech | Sam Roe | unsubscribe | Stage -> Lost; suppressed initech.com |

Then:
- **Booking drafts waiting for Tariq** (in Gmail, not sent): company / contact / the slots or link offered.
- **One recommended next move**: usually "answer the N interested replies before the next `/lead-outreach`".

No new replies: "No new replies across N Contacted leads." then the next move from `/lead-pipeline`.

## When the call gets booked (manual follow-through, not run by this skill)
When Tariq confirms a time (himself, or by telling `/lead-pipeline` "the <company> call is booked"),
set via the adapter: `set_stage` `Call Booked`; `update_lead` `deal_value` = the expected amount
(`offer.md` Reference ranges: start at the Single production workflow midpoint, about $8,000, unless
discovery already points at a multi-workflow system), `next_action` = "run /lead-proposal after the
call", `next_action_date` = the call date; `append_activity` `YYYY-MM-DD: call booked`.
Do not build a listener for this.

## Idempotency
Every processed reply leaves a dated `Activity Log` line (`reply received, ...` / `unsubscribe, ...` /
`bounce, ...` / `auto-reply, retry ...` / `booking draft created ...`). A re-run reads the log in
Step 1 and skips any reply older than its processing line. Only `not-now` and `auto-reply` leads stay
at Stage `Contacted`, so those are the only ones re-examined; a genuine later reply on them is newer
than the processing line and gets caught. `suppress.md` writes check for the line first. The booking
draft is not recreated once `booking draft created` is logged.

## Writes
- Pipeline via the adapter: `set_stage`, `update_lead` (`next_action`, `next_action_date`, `deal_value`), `append_activity`. No `create_lead`, no delete.
- `clients/<client>/suppress.md`: append only.
- Gmail: **drafts only** (`create_draft`). Never `send_message`, never `reply`. The Intern Rule: every reply is human.

## Delegate (optional)
Reply-handling strategy, objection framing, or whether a `not-now` is really a soft no: `sales-outbound-strategist`. Deal qualification on an `interested` reply: `sales-deal-strategist`.
