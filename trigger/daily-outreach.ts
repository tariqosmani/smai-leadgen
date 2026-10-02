import { schedules, wait } from "@trigger.dev/sdk";
import { runDaily } from "./engine";

// Mon-Fri 10:00 New York time. Sends first touches only; the claude.ai follow-up routine sends touches 2-5.
export const dailyOutreach = schedules.task({
  id: "daily-outreach",
  cron: { pattern: "0 10 * * 1-5", timezone: "America/New_York" },
  retry: { maxAttempts: 1 }, // never retry: a retry could re-send an email already sent
  run: async () => runDaily({ wait: (seconds) => wait.for({ seconds }) }),
});
