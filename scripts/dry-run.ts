// Local check: sources 2 leads and drafts 2 emails. Sends nothing, writes nothing to Airtable.
// Spends a few free Clay credits. Run: npm run dry-run  (DRY_SOURCE=0 skips sourcing)
import { normDomain, problems, runDaily } from "../trigger/engine";

process.loadEnvFile(".env");
console.assert(normDomain("https://www.Acme.co.uk/contact?x=1") === "acme.co.uk");
console.assert(normDomain("jane@acme.com") === "acme.com" && normDomain("Acme Corp") === "");
console.assert(problems({ subject: "ap backlog", body: "It cut manual AP work by 80% — worth a look?" }).length === 3, "voice/honesty check must reject numbers, dashes, short bodies");
await runDaily({ dryRun: true, limit: 2, forceSource: Number(process.env.DRY_SOURCE ?? 2) });
