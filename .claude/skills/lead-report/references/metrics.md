# Report metrics: definitions and derivation

Every metric `/lead-report` shows, exactly how it is computed, and which adapter can supply it. When a
metric cannot be derived for the active client, the skill prints the "not tracked" text from here. It
never estimates.

## Window and week-over-week

- **Window** `[since, until]`: default `until` = today, `since` = today minus 7. `days=N` or
  `since=YYYY-MM-DD` override.
- **Prior window**: same length, immediately before `since`. Source for its numbers, in order:
  (1) the last line of `clients/<client>/report-log.md`, (2) a fresh `report_metrics(prior_since)` or
  Instantly analytics call for the prior dates. No prior data anywhere: show current only, note
  "first report".
- **Snapshot metrics** (leads by stage, pipeline value) are current-state, not windowed. Their WoW
  delta compares to the snapshot recorded in the previous `report-log.md` line.
- **Delta display**: `+3`, `-1`, `0`, or `new`. A rate delta is shown in points
  ("reply rate 6% to 9%, +3 pts").

## Activity Log line formats (the Airtable parsing key)

Airtable stores no event history, so windowed counts are parsed from dated `Activity Log` lines. The
skills write these formats:

| Written by | Line | Counts toward |
|---|---|---|
| `/lead-find` step 6 | `YYYY-MM-DD: sourced + scored NN.` | new leads added |
| `/lead-outreach` step 5 | `YYYY-MM-DD: email touch N SENT (gmail thread <id>)` | emails sent (any N); follow-ups sent (N >= 2) |
| `/lead-proposal` step 6 | `YYYY-MM-DD: proposal sent (<url>)` | proposals sent |
| `/upwork-proposal` step 4 | `YYYY-MM-DD: Upwork proposal sent` | proposals sent (channel upwork) |

A line counts in the window when its `YYYY-MM-DD` is within `[since, until]`. For "emails sent" count
distinct lines; for rates count distinct leads.

**Transitions without a standard line** (reply received, Call Booked, Won): these depend on Tariq
adding a dated line when he moves the lead, for example `YYYY-MM-DD: replied`,
`YYYY-MM-DD: call booked`, `YYYY-MM-DD: won`. Where the line exists, use its date. Where it does not,
the lead still counts in the current snapshot, but the skill flags "transition date unknown" and
excludes it from the windowed count and the WoW delta. See "Proposed log-line convention" at the end.

## Metrics

For each: **definition**, **Airtable**, **Instantly**, **availability**.

### Activity

**Emails sent** - first-touch and follow-up emails delivered in the window.
- Airtable: `email touch N SENT` lines dated in the window, all N.
- Instantly: sum of `sent` from `analytics/daily` over the window. Fallback: `contacted_count` from
  `analytics/overview` (distinct leads emailed, slightly lower).
- Available: both.

**Follow-ups sent** - emails sent in the window that were not a first touch.
- Airtable: `email touch N SENT` lines with N >= 2, dated in the window.
- Instantly: not separable in analytics. Report `emails sent minus new leads contacted in window` and
  label "approx", or show "not separately tracked (Instantly)".
- Available: Airtable full, Instantly approximate.

**LinkedIn touches** - connection notes and LinkedIn messages sent in the window.
- Airtable: dated lines matching `linkedin` (for example `YYYY-MM-DD: linkedin touch N ...`). LinkedIn
  is sent by hand (Intern Rule), so this is only as complete as Tariq's logging. No LinkedIn lines at
  all: show "not tracked (manual send, not logged)".
- Instantly: not available (email-only platform).
- Available: Airtable if logged, Instantly never.

**Opens + open rate** - emails opened, and opens divided by emails sent.
- Airtable + Gmail: **not tracked (Gmail send)**. Never estimated, never shown as a number. Do not
  infer opens from replies.
- Instantly: `open_count` from `analytics/overview` for the window; open rate = `open_count / sent`.
  Instantly tracks opens with a pixel.
- Available: Instantly only.

**Replies + reply rate** - leads that replied in the window, and replies divided by leads emailed in
the window.
- Airtable: leads whose `Activity Log` has a reply line dated in the window, or whose `Stage` is
  `Replied` or downstream with a dated transition line in the window. Denominator: distinct leads with
  an `email touch N SENT` line in the window.
- Instantly: `reply_count / contacted_count` from `analytics/overview` for the window.
- Available: both, Instantly cleaner.

**Positive replies + positive-reply rate** - replies that show genuine interest (not a no, an
out-of-office, or an unsubscribe), and positives divided by replies.
- Airtable: judgment on the reply text Tariq logged, plus any lead that moved `Replied` to
  `Call Booked` in the window. Count conservatively.
- Instantly: leads set to `lt_interest_status` 1 (Interested) or 2 (Meeting Booked) in the window, or
  the `total_opportunities` increase over the window.
- Available: both, with a judgment step on Airtable.

### Pipeline

**New leads added** - leads created in the window.
- Airtable: `sourced + scored` lines dated in the window (or record `createdTime` if the MCP returns
  it).
- Instantly: leads with `timestamp_created` in the window from `list_leads`.
- Available: both.

**Leads by stage** - current count in each `Stage` (snapshot, not windowed).
- Airtable: tally `Stage` across all `list_leads` records, which is `report_metrics.stage_counts`.
- Instantly: tally `custom_variables.stage` across the campaign's leads; native status covers
  `Contacted` and `Replied`.
- Available: both.

**Meetings booked** - transitions into `Call Booked` in the window.
- Airtable: `Stage` = `Call Booked` or downstream with a dated `call booked` line in the window, else
  flagged "transition date unknown".
- Instantly: `total_meeting_booked` increase over the window, or `lt_interest_status` set to 2 in the
  window.
- Available: both, Instantly cleaner.

**Proposals sent** - transitions into `Proposal Sent` in the window.
- Airtable: `proposal sent` and `Upwork proposal sent` lines dated in the window.
- Instantly: leads with `custom_variables.stage` = `Proposal Sent` and a dated `activity_log`
  custom-variable line in the window (no native concept).
- Available: Airtable full, Instantly from the custom variable.

**Deals won** - transitions into `Won` in the window.
- Airtable: dated `won` line in the window, else flagged.
- Instantly: `total_closed` increase over the window, or `lt_interest_status` 4 in the window.
- Available: both.

**Pipeline value** - sum of `deal_value` for leads in `Call Booked` or `Proposal Sent`.
- Airtable: sum the `Deal Value` column over those two stages. Field absent, or empty on every lead:
  **"not set"**. Report `Won` value separately (sum of `Deal Value` over `Stage` = `Won`, for wins in
  the window).
- Instantly: sum `custom_variables.deal_value` over the same two stages.
- Available: both, once the `deal_value` field exists (see "Deal Value" below). Until then: "not set".

**Win rate** - `Won / (Won + Lost)` over the window.
- Both: count `Won` and `Lost` transitions in the window. Denominator under 3: show the counts and
  "small sample", not a percent. Optionally also show trailing-90-day.
- Available: both.

### Conversion (reuse `/lead-pipeline` step 4)

Same Activity-Log-timestamp method as `/lead-pipeline` step 4, scoped to the report window instead of
60 days. Each rate = leads that reached stage B in the window divided by leads that were at stage A
and eligible to advance.

| Rate | From to To |
|---|---|
| Contacted to Replied | first `email touch` sent, then a reply |
| Replied to Call Booked | `Replied`, then `Call Booked` |
| Call Booked to Proposal Sent | `Call Booked`, then `Proposal Sent` |
| Proposal Sent to Won | `Proposal Sent`, then `Won` |

- Window under 30 days: also compute each over the trailing 90 days (the stable number the client
  should watch). Show both, for example "this week 0/2, 90-day 18%".
- Denominator under 3: show `n/N`, not a percent.
- Instantly: Contacted to Replied is `reply_count / contacted_count` from analytics; the later rates
  come from the interest-status counts (`total_meeting_booked`, `total_closed`) and
  `custom_variables.stage`.

## "Not tracked" rules (never estimate)

1. Gmail sends have no open or click data. Open rate, click rate, click-to-open: always
   "not tracked (Gmail send)". Do not infer opens from replies.
2. LinkedIn touches sent by hand and not logged: "not tracked (manual send, not logged)". Do not infer
   from connection counts.
3. A windowed transition count with no dated line: show the snapshot number and
   "transition dates incomplete". Do not back-fill from `Last Modified Time`.
4. Pipeline value with no `deal_value` data: "not set", never a guessed number.
5. Any rate with a denominator under 3: show the raw count, not a percentage.

## Deal Value

`deal_value` is an optional contract field (`docs/pipeline-contract.md`), mapped to a `Deal Value`
column on Airtable and `custom_variables.deal_value` on Instantly. When no in-play lead has a value
set, `/lead-report` shows pipeline value = **"not set"** and every other metric works normally.

Usage:
- Airtable: the `Deal Value` column (Currency, USD). Tariq sets it at `Call Booked` (expected) and
  confirms it at `Proposal Sent` and `Won`.
- Instantly: `custom_variables.deal_value` (number).
- The skill sums it over `Call Booked` + `Proposal Sent` for "pipeline value", and over `Won`
  (wins in the window) for "won value".
- Degradation: if some but not all in-play leads have a value, sum what is present and note
  "n of m deals valued".

## Airtable Interface spec (live dashboard, client sets up once)

A read-only Airtable Interface on the `Lead Pipeline` table so the client can watch the pipeline
between the weekly Docs. One interface, the elements below. Stage order everywhere:
`Qualified, Nurture, Contacted, Replied, Call Booked, Proposal Sent, Won, Lost`.

1. **Pipeline by stage** - a List (or Kanban) element grouped by `Stage` in the order above, sorted by
   `ICP Score` descending within each group. Fields shown: `Company`, `Contact Name`, `ICP Score`,
   `Next Action Date`, `Deal Value`.
2. **Stage counts** - a bar chart element: x-axis `Stage`, y-axis record count, same stage order.
3. **This week** - a filtered List element: `Next Action Date` within the last 7 days, OR `Stage` is
   any of `Replied`, `Call Booked`, `Proposal Sent`. The "what needs attention now" view.
4. **Number widgets** (dashboard number elements):
   - **Reply rate (7d)**: needs a helper. Without a formula field, show two numbers side by side,
     count of `Stage` = `Replied` with `Next Action Date` in the last 7 days, and count of leads
     contacted in the last 7 days. If a rollup or formula field is added later, show the single
     percent.
   - **Leads contacted (7d)**: count where `Stage` moved to `Contacted` in the last 7 days (or an
     `email touch ... SENT` line in the last 7 days).
   - **Meetings booked (7d)**: count `Stage` = `Call Booked` with the transition in the last 7 days.
   - **Pipeline value**: sum of `Deal Value` where `Stage` is `Call Booked` or `Proposal Sent`.
5. **Won this quarter** - a number element: count and `Deal Value` sum where `Stage` = `Won` and the
   win date is in the current quarter.

### Building it with the MCP (optional, not required)

The client can build the above by hand from this spec. To script it instead:
- `mcp__claude_ai_Airtable__create_interface({ baseId, name: "{business name} - Outbound Dashboard" })`
  returns an `interfaceId`.
- `mcp__claude_ai_Airtable__describe_page_type({ pageType: "dashboard" })` and
  `mcp__claude_ai_Airtable__describe_page_element` for the number and chart element config shapes.
  Read them at build time, the shapes change.
- `mcp__claude_ai_Airtable__create_page({ baseId, interfaceId, name: "Pipeline", pageType: "dashboard", pageConfiguration: {...} })`
  for the charts and number widgets; a second `create_page` with `pageType: "visualization"` and
  visualization `list` (grouped by `Stage`) for element 1.
- `mcp__claude_ai_Airtable__publish_interface({ interfaceId })` to go live.
Do not require this path. The spec above is the deliverable; the calls are a convenience.

## Proposed log-line convention (for the reviewer)

Windowed reply, meeting, and win counts on Airtable are only reliable if every stage move leaves a
dated line. Recommend adding to `docs/outreach-playbook.md` > Logging and to `/lead-pipeline`: "on any
manual stage change, append `YYYY-MM-DD: <stage>` to the Activity Log." Not applied here, those files
are out of scope for this change. Until it is adopted, the skill degrades per the "Not tracked" rules.
