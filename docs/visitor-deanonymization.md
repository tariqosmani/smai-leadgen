# Website visitor de-anonymization

A retainer add-on. Most B2B site traffic never fills in a form. Visitor de-anonymization
puts a script on the client's marketing site that resolves a share of those anonymous
visits to a real person or company, so a prospect who was already researching the client
becomes a warm outbound lead instead of a lost session.

This doc covers what the add-on is, the tools, how a resolved visitor enters this
pipeline, and how it is priced. The ingest mechanics are `/lead-import`.

## What it is

- A tracking snippet on the client's site (all pages, or a chosen set).
- The vendor matches each visit against its identity graph (cookie, IP, and third-party
  identity data) and returns either a named person (first name, last name, LinkedIn,
  sometimes a work email) or just the company.
- Person-level resolution is strongest for United States traffic. Outside the US, and
  under GDPR, most tools resolve to company only.
- Match rates are a fraction of traffic, not all of it. Treat the output as a small,
  high-intent stream, not a volume source.

## Tools

RB2B is the reference: person-level resolution for US visitors, pushes each hit to Slack
or a webhook, and has a free tier (a capped number of identifications per month).
Alternatives, by resolution type:

| Tool | Resolves | Free tier |
|---|---|---|
| RB2B | person (US), company | yes, capped monthly identifications |
| Vector | person (US), company | trial only |
| Koala | person and company, with intent scoring | yes, limited plan |
| Clearbit Reveal | company (IP to company) | bundled with a HubSpot account |
| Snitcher | company | trial only |

Pick one per client. The client owns the account and the script tag; this system only
consumes the export.

## How a resolved visitor enters the pipeline

The vendor produces a CSV export or a webhook feed (Slack, Zapier, or a raw POST). The
resolved rows are collected into a CSV and handed to `/lead-import`. On import each row
becomes a lead with:

- `source`: `visitor-deanon - <tool>` (e.g. `visitor-deanon - rb2b`).
- `channel`: set from the contact data present. Work email and LinkedIn both present:
  `email + linkedin`. Only one: that one. A company-only row with no named contact is
  not imported (nothing to reach); note it so `/lead-find` can source a decision-maker.
- `signal`: `visited <page> on <date>`, from the export's page or URL column. This is a
  real intent signal and scores as one in `clients/<client>/scoring.md`.
- No cold-sourcing credit cost. The vendor already resolved the person, so Explorium
  contact enrichment is skipped. Email verification (`scripts/verify_email.py`) still
  runs, and the ICP score and hook are still written.

The dedupe rule is unchanged. `/lead-import` normalizes each row's company domain
(`scripts/normalize.py`) and checks the pipeline (`find_lead_by_domain`) before creating
anything. A visitor who is already a lead is skipped, noted as a returning visitor so the
founder can nudge the open thread.

## Pricing

A retainer add-on, not a build line. The client pays a monthly amount covering the tool
subscription (in the client's name, per `clients/<client>/offer.md` Pricing method
section 8), the import runs, and the outreach on the resolved leads. It is sold on top of
an existing engagement, never as a standalone project. Price it from the real monthly
effort plus the tool cost, the same way maintenance is priced. No result is promised:
match rates and reply rates depend on the client's traffic and offer.
