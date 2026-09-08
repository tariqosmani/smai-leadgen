# ICP Score — 0 to 100

Computed at `/lead-find` after enrichment. Deterministic rubric — add the points, write the number to column M.
Bulk scoring can run on a free model (Groq `llama-3.3-70b-versatile`); the hook in column N is Claude's job.

## Rubric

### Industry match — max 25
| | pts |
|---|---|
| One of the 6 ICP industries | 25 |
| Adjacent B2B service business (agency-like, consulting, prof. services) | 15 |
| Other B2B | 8 |
| B2C / non-profit / gov | 0 → also set Stage = Disqualified |

### Company size — max 20
| employees | pts |
|---|---|
| 10–200 | 20 |
| 201–1000 | 12 |
| 5–9 | 8 |
| 1001–5000 | 5 |
| <5 or >5000 | 2 |

### Geography — max 15
| | pts |
|---|---|
| US / Canada | 15 |
| UK / Australia / Ireland / NZ | 8 |
| Other English-first | 4 |
| Else | 0 |

### Automation-intent signals — max 25
Start at 0, +8 per distinct signal, cap at 25:
- lead came from an `intent=true` pull (Explorium `business_intent_topics` matched marketing/workflow/AI automation) → +8
- lead came from a `hiring=<dept>` pull, or the company shows an Explorium `events` hire/expansion in ops/marketing/eng in the last 90 days → +8
- `prospect_skills` / company tech stack shows manual-process or integration-hungry setup (Sheets as system-of-record, HubSpot + Sheets, Shopify + 3PL, QuickBooks + manual AP) → +8
- recent funding / new office / new market in Explorium `events` → +8
- founder/contact visibly posts about ops pain (manual check) → +8

A plain filter-only pull (no intent/events filter) starts this dimension at 0 unless a signal is visible in the enriched data.

### Reachability — max 15
| | pts |
|---|---|
| Named decision-maker + (email OR personal LinkedIn) | 15 |
| Named decision-maker, company contact only | 7 |
| Role/department contact, no name | 3 |
| Generic inbox only | 0 → Stage = Disqualified |

## Banding

| Score | Stage set by `/lead-find` |
|-------|---------------------------|
| ≥ 60 | `Qualified` |
| 40–59 | `Nurture` |
| < 40 | `Disqualified` (note the reason in col U) |

## Tie-breakers when capacity is limited

Work `Qualified` leads in this order: highest ICP Score → then `Channel = email` before `linkedin` (faster cycle) →
then most recent automation-intent signal (freshness beats a stale high score).
