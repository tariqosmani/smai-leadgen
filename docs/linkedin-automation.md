# LinkedIn: manual vs automated

`/lead-outreach` produces the LinkedIn touches for a lead's cadence. How they get sent is
set per client by `linkedin_mode` in `clients/<client>/identity.md`:

| `linkedin_mode` | Who sends | Trade-off |
|---|---|---|
| `manual` (default) | the founder, by hand | fully within LinkedIn's User Agreement. No account risk. |
| `heyreach` (opt-in) | a HeyReach-class tool runs the sequence | faster and hands-off, but LinkedIn's terms prohibit automation. Managed risk, not zero risk. |

## `manual` (default)

The current behavior and the safe default. `/lead-outreach` prints a paste-ready block
per lead: the connection note (at most 300 chars, no link), then each follow-up message
with its day offset. The founder opens the profile and sends each one. The pitch to the
client is plain: we will not get your LinkedIn account restricted.

Nothing to configure. `linkedin_mode: manual`, or the line absent, means this.

## `heyreach` (opt-in)

A dedicated cloud tool (HeyReach, Expandi, and similar) runs the connection request and
the message steps on a schedule, from the client's LinkedIn account.

**The ToS caveat, stated plainly:** LinkedIn's User Agreement prohibits automated
activity. A dedicated cloud tool lowers the footprint compared to a browser extension,
but it does not remove the risk of a warning, a temporary restriction, or a ban.
Mitigations, all on the client:

- a dedicated LinkedIn account that is not the founder's primary one
- conservative limits: about 20 connection invites per day, ramped up over weeks
- account warming before the first campaign (profile complete, some organic activity)
- stop on the first warning from LinkedIn

The client accepts this trade-off in writing before the mode is switched on.

### How it wires in

- `/lead-outreach` reads `linkedin_mode: heyreach` and, instead of printing inline paste
  text for each LinkedIn lead, accumulates them into a HeyReach export batch: one CSV row
  per lead (name, profile URL, company, hook) plus the per-step message copy.
- At the end of the run it outputs that batch as a copy-paste CSV block, or writes it to
  `clients/<client>/linkedin-heyreach-<date>.csv`, with the steps to load it into a
  HeyReach campaign.
- The founder imports the CSV into their HeyReach campaign and starts it there.
- Replies still come back to a human. HeyReach pauses a lead on reply; the founder takes
  the conversation, same as the manual flow (CLAUDE.md > Intern Rule). `/lead-replies` is
  unchanged.

The cadence, the angle per touch, and the message drafting are identical to `manual`
mode. Only the delivery changes. There is no autonomous LinkedIn send from this system in
either mode.

### Setup

The wiring today is the CSV export above: the founder loads the file into a HeyReach
campaign by hand, so a managed-LinkedIn retainer needs a HeyReach subscription and a
campaign for the client. A future direct push from `/lead-outreach` into the HeyReach API
would use `HEYREACH_API_KEY`; `.env.example` carries that variable name as a commented
retainer-upgrade line. The repo ships no key (demo / no-spend).
