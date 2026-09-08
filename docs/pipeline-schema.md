# Pipeline — the data store (Airtable)

The lead pipeline lives in one Airtable table: **Lead Pipeline**
in the **SmartAI Listings Database** base. One record = one prospect (a named decision-maker at a
target company).

| | |
|---|---|
| Base | `SmartAI Listings Database` — `appMULkAmdFmneAyB` |
| Table | `Lead Pipeline` — `tblHGHp4DthpNKAU9` |
| Access | Airtable MCP (`mcp__airtable__*`) |
| Config | `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE` in `.env` |

Airtable holds real typed columns, so every lead attribute is its own field — no packed
description blob.

## Fields

| Field | Type | Notes |
|---|---|---|
| Company | Single line text | primary field |
| Contact Name | Single line text | |
| Title | Single line text | |
| Stage | Single select | the authoritative pipeline stage (values below) |
| ICP Score | Number (integer) | 0–100, from `docs/scoring.md` |
| Channel | Single select | `email + linkedin` / `email` / `linkedin` / `upwork` |
| Industry | Single select | `real-estate` `e-commerce` `manufacturing` `marketing-agencies` `logistics` `saas` `other` |
| Email | Email | |
| Email Status | Single select | `valid` / `catchall` / `unknown` |
| LinkedIn | URL | the contact's profile |
| Company Website | Single line text | bare domain, no scheme — **the dedupe key** |
| Company LinkedIn | URL | |
| Location | Single line text | |
| Signal | Long text | hiring / funding / tech-stack / intent signal, if any |
| Hook | Long text | the prospect-specific "why they need AI automation" line |
| Next Action | Long text | the next step in words |
| Next Action Date | Date (ISO `YYYY-MM-DD`) | when the next touch is due |
| Source | Single line text | e.g. `Explorium / Vibe Prospecting — <segment>, <date>` |
| Activity Log | Long text | dated lines, newest appended (see below) |
| Proposal Doc | URL | Google Doc link, set by `/lead-proposal` |
| ClickUp Task ID | Single line text | legacy — only on the 5 records migrated from ClickUp |
| ClickUp URL | URL | legacy |

### Activity Log format

One cell, dated lines oldest-first. To add a touch: read the current value, append a new line, write
the whole field back with `update_records`.

```
2026-09-02: sourced + scored 81. Gmail draft (touch 1) created - review in Gmail and send.
2026-09-05: email touch 2 drafted (gmail id 18f...)
```

## Stages (the `Stage` single-select value)

```
Qualified        → ICP Score ≥ 60, hook written, ready for outreach
Nurture          → 40–59, or good fit / bad timing
Disqualified     → < 40, or hard exclusion (keep the record so it isn't re-sourced)
Contacted (draft)→ outreach draft made, not yet sent
Contacted        → first touch sent
Replied          → prospect responded
Call Booked      → discovery call scheduled
Proposal Sent    → 3-option proposal delivered
Won              → signed
Lost             → explicit no, or 90 days cold after Contacted
```

## ICP band (derived from ICP Score — not a stored field)

Used for sort order and "what to work first", computed on read:

```
≥ 70   high
60–69  normal
40–59  Nurture band
< 40   Disqualified
```

## Dedupe rule

Before creating a record, normalize the candidate's company website (`scripts/normalize.py`) and query
the table for that domain or company name:

```
mcp__airtable__list_records  (or search_records)
  baseId:  appMULkAmdFmneAyB
  tableId: tblHGHp4DthpNKAU9
  filterByFormula:  LOWER({Company Website}) = "<normalized-domain>"
```

Match → update the existing record, never create a second one. Also collapse so no company gets more
than 2 records (keep the most senior, most complete contacts). Explorium's own dedupe (`exclude_key`)
skips already-exported prospects across `/lead-find` runs.
