import { defineConfig } from "@trigger.dev/sdk";
import { additionalFiles, syncEnvVars } from "@trigger.dev/build/extensions/core";
import { existsSync, readFileSync } from "node:fs";
import { parseEnv } from "node:util";

// A local `npm run deploy` pushes these from .env to trigger.dev. GitHub-triggered builds have no .env,
// so they sync nothing and use the values already stored in the trigger.dev dashboard.
const dotenv = (existsSync(".env") ? parseEnv(readFileSync(".env", "utf8")) : {}) as Record<string, string>;
// Only what the daily job needs goes to trigger.dev.
const SYNC = ["ACTIVE_CLIENT", "SENDER_POSTAL_ADDRESS", "AIRTABLE_API_KEY", "APOLLO_API_KEY", "CLAY_API_KEY",
  "COMPOSIO_API_KEY", "LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "DAILY_SEND_LIMIT"];

export default defineConfig({
  project: "proj_zcbqmaphsqvtgxavtjzk", // trigger.dev project "Lead Generation"
  dirs: ["trigger"],
  maxDuration: 3600, // compute seconds; the waits between sends don't count
  build: {
    extensions: [
      // client config read at run time (suppress.md + infrastructure.md are snapshots: redeploy after /lead-replies or /deliverability-monitor)
      additionalFiles({ files: ["clients/*/identity.md", "clients/*/icp.md", "clients/*/offer.md", "clients/*/suppress.md",
        "clients/*/infrastructure.md", "docs/outreach-playbook.md"] }),
      syncEnvVars(() => SYNC.filter((k) => dotenv[k]).map((name) => ({ name, value: dotenv[name] }))),
    ],
  },
});
