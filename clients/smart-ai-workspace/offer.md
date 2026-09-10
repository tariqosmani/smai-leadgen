# Offer — Smart AI Workspace

What the client sells, its service lines, the portfolio proof points outreach and
proposals may cite, and the value-based pricing method. Used by `/lead-outreach`
(proof points), `/lead-proposal` (the whole pricing method), and `/upwork-proposal`
(proof + why no price before discovery).

## What Smart AI Workspace sells

A founder-led B2B AI automation consultancy, not a SaaS. Tariq Osmani scopes and
builds the work himself. The offer: design, build, and maintain intelligent
automation systems for B2B companies, turning operational bottlenecks into
throughput. Sell the result, not the build.

## Service lines

The four services a lead's Hook ties to and a proposal's options map to (slugs used
across the skills):

| Service | slug | What it covers |
|---|---|---|
| Workflow automation | `workflow` | multi-step manual processes moved onto n8n / code with AI steps |
| CRM automation | `crm` | dedupe, enrichment, routing, reporting, stale-record chase |
| Data pipelines | `data` | scattered spreadsheets and exports unified into one reliable source |
| AI agent development | `agents` | document-grounded assistants, classifiers, autonomous task agents |

## Portfolio proof points

Condensed from `../Tariq_Osmani_OS/references/upwork-catalog/`. Full source of truth lives there —
run `/catalog-project` in the OS repo to add new builds. Cite the most relevant one; never invent metrics.

### Nexus — RAG Chatbot
- **What:** Document-grounded AI chatbot. Upload PDF / Word / Excel / PPT, ask questions, get answers cited from the files.
- **Stack:** Python, FastAPI, Supabase pgvector, OpenRouter.
- **Use in outreach when:** prospect has scattered internal knowledge, slow document lookup, support teams answering the same questions.
- **Status:** Complete.

### Invoice Processing Automation
- **What:** Raw invoice document or email in → validated, synced accounting data out.
- **Stack:** Python, FastAPI, Celery, Claude Vision, PostgreSQL, Xero, n8n.
- **Use in outreach when:** prospect does manual AP / data entry, rekeys invoices, reconciles by hand.
- **Status:** Complete.

### Credibility line (always true, use freely)
8+ years in IT/data. Anthropic-certified (Claude API, MCP, Prompt Engineering) + AWS. Founder-led — the person scoping the work is the person building it.

### What NOT to claim yet
No paying-client case study or testimonial exists yet (that is the current #1 priority). Do not imply
past client results, named clients, or revenue figures. "Built and shipped" is honest; "helped X company achieve Y" is not.

## Pricing method

How Smart AI Workspace prices client work. Adapted from Nate Herk's *"How to
Price AI Solutions"* masterclass (`docs/reference/`). This is the internal
process — the public `/pricing` page describes the method, never the numbers.

### The one rule

Get the client to state what the problem costs the business **before** you say
any price. Use their numbers, their language, their definition of success. Your
fee then becomes a fraction of a number they already own.

Sell the result. The build is just how the result gets delivered.

### The full sequence

1. Diagnose the business problem before discussing a solution.
2. Map the current process so hidden steps and exceptions surface.
3. Quantify the credible first-year value **with** the client.
4. Confirm technical scope, delivery risk, and the cost floor.
5. Price inside the corridor between cost and value.
6. Present three options that change scope and value.
7. Collect payment at signing and at objective milestones.
8. Measure the result so this project makes the next one easier to sell.

### 1. Discovery call — before any number

**Qualify first (4 signals):**

- **Conviction** — do they genuinely want this solved?
- **Urgency** — what business pressure makes now the time?
- **Authority** — who approves budget, security, and access?
- **Strategic fit** — does the work match our skills, proof, and target market?

Weak signals don't mean a bad prospect — they mean the project isn't ready.
Don't write a proposal for a conversation with no owner, urgency, or decision
path.

**LRP:** Listen (let them explain what's been tried and where it sticks) →
Repeat (reflect the problem in their words) → Poke (how often, how many people,
what does failure cost).

**Three whys:** Why this (does the AI solution actually create the outcome) ·
Why now (deadline, competition, cost, growth constraint) · Why me (why not build
it internally, hand it to an intern, or buy software). Ask the "why me"
question out loud and let them answer — it reveals the real reason they want
outside help.

**Two lenses:**

- **Time Lens** — expensive manual work. Which team is most expensive in manual
  labour? How long does this take, how many people, how often, which systems?
- **Income Lens** — growth constraints. If leads doubled tomorrow, what breaks
  first? Where are you turning away work or adding headcount?

**Map the process (4 parts):** Trigger → Steps (who acts, which systems) →
Decisions & exceptions (what changes the path, what happens on incomplete data)
→ Result (the observable output that marks it done). Then name the exact
constraint step — its time, frequency, and consequence.

**Delay the price with confidence:** *"I want to understand the technical
landscape before I give you a number — let me ask a few more questions so I
don't misquote you."* A confident delay is professional. A random number isn't.

### 2. First-year value model

Build it with the client, label every assumption.

| Component | Formula |
|---|---|
| Annual labour capacity | volume per period × time per item × loaded labour rate × periods/year |
| Avoided error cost | incidents/month × cost per incident × 12 × expected reduction |
| Revenue capacity | extra qualified opportunities × contribution per outcome × realistic conversion |
| Hiring cost avoided | avoided loaded cost + recruiting + onboarding + management |
| Cycle-time value | quantify only the part the client can defend; present the rest as upside |

Use **loaded** labour rate (wages + payroll + benefits + overhead), not salary.
Use **contribution**, not gross revenue.

**Confidence adjustment:** give each line a level — high (direct labour, reliable
data), medium (errors with several months of records), low (future revenue
depending on sales/adoption). `confidence-adjusted value = estimate × confidence %`.

**No double counting:** if recovered staff time is used to serve more customers,
don't count it as both labour saved and new revenue. Pick the most defensible
primary model; treat the rest as a separate upside case. Client confirms the
final model in writing.

### 3. The price corridor

- **Cost floor** = delivery cost + risk reserve + required profit. Delivery cost
  = design, dev, testing, docs, training, PM, meetings, revisions, specialists,
  test model usage.
- **Value ceiling** = credible first-year value (base case, confidence-adjusted).
- **Starting price** = 10–20% of credible first-year value.
- **10X check** = value ÷ price. ≥10 easy to explain · 5–10 fine if the value is
  reliable and strategic · <5 revisit scope, price, or sequence.
- **Margin check** = `delivery cost / (1 − target gross margin)`. If delivery is
  $6k and target margin 60%, required price is $15k. If the client's value only
  supports $10k, change the project — don't accept a price that makes
  professional delivery impossible.

If credible value is below the responsible cost floor, **there is no deal at
this scope.** Fix it by shrinking the outcome, running paid discovery, or
recommending a simpler tool — never by hiding costs or inventing value.

**Complexity moves the floor:** integration count and quality, structured vs
unstructured input, data cleanup, user roles and approval paths, exception
volume, throughput/latency, security/compliance, documentation and change
management, stakeholder count. More agent autonomy → more evaluation and QA.
Add roughly $1k / $2k / $3k of testing to the build price to match the testing
burden.

### Reference ranges — sanity check, not the quote

What Smart AI Workspace's value-based numbers typically land at (2026,
small-business focus):

| | Range |
|---|---|
| Automation audit | Free |
| Single production workflow | $5,000–$12,000 |
| Multi-workflow system (3–5 connected) | $15,000–$35,000 |
| Ongoing retainer | $1,500–$6,000/month |
| Typical payback | 2–4 months |

If a value-based number lands far outside these, re-check the value model or the
scope before sending it. Enterprise-scale programs ($50k+) are not the target
market.

### 4. Three-option proposal

One price asks *whether* to work with you. Three options ask *how*. Each option
must solve a different-sized problem — every step up adds client value or
removes real risk, not just features.

| Option | Scope |
|---|---|
| **Essential** | Smallest complete outcome. One priority workflow, one team, core integrations, standard launch support, 30-day review. |
| **Growth** *(recommended)* | Multiple connected workflows, larger evaluation set and edge-case coverage, team training, 60-day optimisation window, recommended maintenance plan. |
| **Scale** | Multiple teams/units, governance and reporting, higher-volume testing, executive result dashboard, phased improvement roadmap, priority response. |

The middle option is designed to win. The lower option must be genuinely useful,
not deliberately broken. The upper option must serve a real buyer.

**Proposal order:** current state (client's words + numbers) → desired future
state and business result → why our experience fits → options with scope,
assumptions, exclusions → milestones and payment events → estimated production
run cost + volume assumption → measurement plan, support model, commercial terms.

### 5. Payments — objective milestones

Pay at signing, then roughly every 30 days. Never carry months of unpaid work
while the client debates whether a vague milestone feels done.

Example for a $9,000 project: $3,000 at signing (reserves capacity, begins
discovery) · $3,000 when the proof-of-concept milestone passes · $3,000 at
production and handoff.

**An objective milestone** is observable, testable, and hard to argue with. It
names the artifact, who can test it, the exact input, the required behaviour,
the measurable threshold, and the evidence (log, recording, report) that proves
completion — plus what's intentionally reserved for later.

- Good: *"A proof of concept is available to the owner. When they submit a
  question, the system retrieves from the agreed database and responds within
  one minute."*
- Avoid: *"The agent is working as expected."*

Contract: an MSA for stable relationship terms + a SoW per project (scope,
milestones, fees, assumptions, access deadlines, IP ownership, what happens if
the client goes unresponsive for 30 days). Attorney-reviewed.

### 6. Scope creep

New ideas are a positive signal — the client is imagining more value. Don't
punish it, don't absorb it. *"Great idea — let's put it in the version-two
backlog so we keep the current milestones moving."* Then a **change request**
documents the new functionality, affected milestones, added price, timeline
impact, and approval. Original agreement stays intact.

**"The price is too high"** → reduce scope, risk, or speed. Never discount the
same scope — that teaches the client your numbers are soft. *"It sounds like
$20k isn't in the budget now. Let's start with the highest-value piece; once
it's returning capacity, we move to the next together."*

### 7. Maintenance vs roadmap retainer

- **Maintenance** keeps the agreed system doing its agreed job — monitoring,
  repairs when an API or model changes, agreed edge cases, small config,
  routine volume/latency/cost checks. **Not** new workflows, integrations,
  business rules, reports, or roadmap work.
- **Roadmap retainer** is a different product: implementing the next approved
  improvement + maintaining what's live + spotting new opportunities. The
  client buys steady execution of a phased plan.

Price maintenance from the real monthly monitoring/repair cost + the response
window you promise + system criticality. Never call unlimited improvement
"maintenance."

### 8. Production costs in the client's name

API usage, cloud subscriptions, tokens, telephony, storage → the client's own
accounts and card. Our fee covers design, consulting, building, testing,
documentation, and support. During testing we can cover temporary usage and
fold it into the fixed fee; at production, move to client-owned credentials.
Put an estimated monthly run cost + volume assumption in the proposal, labelled
an estimate.

### 9. Proof loop

Capture the baseline **before** launch — teams forget the old pain within weeks.

**Results Tracker:** 3–5 metrics × (Baseline / Launch / 30 days / 60–90 days).
Candidates: time per item, volume completed, cycle time, error/escalation rate,
response time, completion rate, human review time, cost per completed item.

Run a success review at 30 and 60–90 days: revisit the original problem, show
before/after, translate each metric into business impact, ask if the data
matches the team's experience. Turn it into a case study (problem / solution /
results / ROI) and use it to price the next engagement with more confidence.

### When to walk away

- The client refuses enough discovery but demands a fixed quote.
- The value ceiling doesn't clear the cost floor.
- They expect guaranteed revenue we can't control.
- Required expertise is missing and can't be added responsibly.
- Security/compliance requirements are unclear.
- They want unlimited scope inside a fixed budget.
- The decision owner, access owner, or success owner is missing.
