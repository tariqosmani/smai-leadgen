# ICP — who to target

Source: `../Smart_AI_Workspace_Website/src/lib/data/industries.ts` + the qualification signals in
`references/pricing-playbook.md` §1. Keep this file in sync when the website's industry data changes.

## Firmographic profile

| Dimension | Ideal | Acceptable | Exclude |
|-----------|-------|-----------|---------|
| Type | B2B | B2B2C | Pure B2C, non-profit, government |
| Size | 10–200 employees | 200–1000 | Solo / <5, or 5000+ enterprise |
| Geography | United States, Canada | UK, Australia, Ireland | Non-English-first markets (delivery + timezone risk) |
| Revenue | $2M–$100M | up to $250M | pre-revenue |
| Buyer reachable | Founder / COO / Ops lead / RevOps named + contactable | dept head | info@ only, no name |

## Target industries (the 6 playbooks) + the pain that opens a conversation

| Industry | slug | Opening pain (what to reference in outreach) |
|----------|------|----------------------------------------------|
| Real Estate | `real-estate` | Leads lost to slow manual follow-up; duplicate entry across MLS/CRM/marketing; manual transaction-coordination chase |
| E-Commerce | `e-commerce` | Multi-channel inventory sync breaking; manual order/fulfillment steps; repetitive support tickets |
| Manufacturing | `manufacturing` | Production scheduling in spreadsheets; QC data scattered; operators rekeying numbers; interval-based (not need-based) maintenance |
| Marketing Agencies | `marketing-agencies` | Hours per week on client reporting; manual campaign setup across platforms; slow client onboarding; per-client profitability invisible |
| Logistics & Supply Chain | `logistics` | Manual dispatch/route planning; shipment status chased by phone; BOL/customs/invoice processing by hand; exceptions handled ad hoc |
| SaaS | `saas` | Churn signals caught too late; onboarding manually pieced together per logo; L1 support overwhelming the team as users grow |

"other" is allowed in the sheet for a strong B2B fit outside these six — but the underlying-work pitch is the same, so score it on signal strength, not industry.

## Qualification signals (from pricing-playbook §1) — score at `/lead-find`, confirm on the call

- **Conviction** — is this a problem they actually want solved, or a nice-to-have?
- **Urgency** — a deadline, a hiring freeze, a growth constraint, a competitor pressure making *now* the time.
- **Authority** — is there a named person who can approve budget + access?
- **Strategic fit** — does it match a service (`workflow`, `crm`, `data`, `agents`) and a portfolio proof point?

Weak signals ≠ bad prospect → it means **Nurture**, not Disqualified.

## Automation-intent signals (raise ICP Score — see `scoring.md`)

- Hiring for "operations", "RevOps", "data entry", "coordinator", "admin" roles right now
- Job posts or site copy mentioning manual processes, spreadsheets as system-of-record, "fast-growing", "scaling"
- Stack visible (BuiltWith / site) that begs integration: HubSpot + Sheets, Shopify + 3PL, QuickBooks + manual AP
- Recent funding / expansion / new-market press
- Founder active on LinkedIn talking about ops pain

## Hard exclusions (→ Disqualified immediately)

- Other AI automation agencies / n8n consultants / RPA shops (competitors)
- Companies selling "AI" as their core product (they build in-house)
- Anyone where the only contact is a generic inbox and no name can be found
- Industries with heavy regulatory delivery risk we can't service solo (healthcare PHI, defense, regulated finance)
