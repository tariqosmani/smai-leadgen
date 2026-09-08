# Outreach playbook

Channels, cadence, and the voice rules every drafted message must pass. Used by `/lead-outreach` and `/upwork-proposal`.

## Voice rules (hard, reject and rewrite if any fail)

From `references/voice.md` and the `lead-outreach` craft references
(`.claude/skills/lead-outreach/references/`):

- **No em dashes (—).** Ever. Commas or periods.
- Lead with *their* situation (the `Hook` / `Signal`), not "I'm Tariq / I help companies…".
- "You / your" should outnumber "I / we". Do not open with who you are or what Smart AI Workspace does.
- Pick a framework from `frameworks.md`, do not freewrite. Frameworks are thinking patterns, not templates.
- The personalized opener must connect to the problem. If deleting it leaves the email still making sense, it is not working, cut it and find a real one.
- No AI/templated filler: "I hope this finds you well", "I wanted to reach out", "in today's fast-paced world", "leverage synergies", "circle back", "touch base".
- Short sentences. One idea per sentence. Plain words.
- Professional but warm. No hype, no exclamation marks, no "game-changer".
- Reference one concrete thing about them (recent hire, a page on their site, a job post, their channel mix).
- One ask per email, low pressure. An interest-based question ("worth a look?") beats a calendar request. Never "hop on a quick call this week?" x3.
- Founder-led and honest: "I build these" not "my team delivers". No invented client results, no client names (see `references/portfolio.md`).
- If it reads like AI wrote it, rewrite it.

## Email cadence (channel = email)

5 touches, angle rotates every email, gap grows each time. Full data in
`.claude/skills/lead-outreach/references/follow-up-sequences.md`.

| Touch | Day | Angle | Length |
|-------|-----|-------|--------|
| 1 | 0 | Personalized hook (connected to the problem) + one specific automation idea + interest-based ask | 90–130 words |
| 2 | +3 | A different angle: a new value piece (a stat, an insight, a resource). Not "just bumping this". | 50–80 words |
| 3 | +7 | Social proof: the closest portfolio build and what it did. No client names, no invented numbers. | 50–80 words |
| 4 | +14 | A new insight or industry trend relevant to them. Shows you think about their world. | 30–50 words |
| 5 | +24 | Breakup: acknowledge the silence, one last useful line, leave the door open. | 25–40 words |

Add exactly one new value proposition per email. Stop the cadence immediately on any reply → Stage `Replied`, human takes over.
Best send days Tue to Thu, 9 to 11am or 1 to 3pm in the prospect's local time. If touch 5 goes out, honor it, no further contact.

Subject line (touch 1): 2 to 4 words, lowercase, looks like an internal note from a colleague, not a vendor. Tie it to their situation or a pain, never the product or their first name. Good: "reporting load", "onboarding ops", "quote turnaround". Bad: "AI automation for Acme", "Quick question", "Hi {{First}}". Touches 2 to 5: reply in the same thread, keep the subject. Full data in `.claude/skills/lead-outreach/references/subject-lines.md`.

## LinkedIn cadence (channel = linkedin)

The system **drafts, you send** — no automation, stay ToS-safe. `/lead-outreach` outputs paste-ready text.

| Touch | Day | Purpose |
|-------|-----|---------|
| 1 | 0 | Connection request note, ≤ 300 chars, references the hook, no pitch |
| 2 | +1 after accept | Thank + one specific observation/question about their ops. No pitch. |
| 3 | +4 | Share the automation idea or a relevant portfolio build. Soft ask for a call. |
| 4 | +10 | Breakup line. |

## Upwork (channel = upwork)

Different motion — inbound job posts, not outbound. See `/upwork-proposal`. Proposal is short (120–200 words),
answers the client's stated problem first, cites the closest portfolio build, ends with 2–3 clarifying questions
(shows you read it, starts the discovery). No pricing in the proposal — pricing follows discovery (pricing-playbook §1).

## After a reply

Out of scope for automation. `/lead-pipeline` surfaces it; Tariq runs the discovery call per `pricing-playbook.md` §1,
logs notes in col U, then `/lead-proposal` drafts the 3-option proposal.

## Logging (every send)

`/lead-outreach` updates the row: Stage → `Contacted`, Last Touch → today, Touches +1, Next Action → next touch,
Next Action Date → today + gap, and appends `YYYY-MM-DD: sent email touch N` to Notes.
