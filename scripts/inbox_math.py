"""Cold-email infrastructure sizing.

Input a daily send target, print how many sending domains and mailboxes it needs,
the per-mailbox daily cap once warmed, and the warmup duration. Used by the
`/inbox-setup` skill. Rules + citations:
.claude/skills/inbox-setup/references/deliverability.md

Consensus (2026): ~35 cold sends/day per warmed mailbox (safe 30-40 band for
Google Workspace / Microsoft 365), 3 mailboxes per sending domain, 3-week warmup
ramping from ~5/day.

Run:  python scripts/inbox_math.py            # self-check
      python scripts/inbox_math.py 250        # size a setup for 250 sends/day
"""
import math
import sys

SENDS_PER_MAILBOX = 35      # per day, once warmed (conservative midpoint of 30-40)
MAILBOXES_PER_DOMAIN = 3    # universal 2-3; 3 minimises domain count and cost
WARMUP_WEEKS = 3


def plan(volume: int) -> dict:
    """Size a sending setup for `volume` cold emails per day."""
    volume = int(volume)
    if volume < 1:
        raise ValueError("volume must be >= 1")
    mailboxes = math.ceil(volume / SENDS_PER_MAILBOX)
    domains = math.ceil(mailboxes / MAILBOXES_PER_DOMAIN)
    per_mailbox = math.ceil(volume / mailboxes)   # even split, always <= ceiling
    return {
        "daily_volume": volume,
        "domains": domains,
        "mailboxes": mailboxes,
        "sends_per_mailbox_per_day": per_mailbox,
        "warmup_weeks": WARMUP_WEEKS,
    }


def _selfcheck() -> None:
    assert plan(50) == {"daily_volume": 50, "domains": 1, "mailboxes": 2,
                        "sends_per_mailbox_per_day": 25, "warmup_weeks": 3}, plan(50)
    assert plan(200) == {"daily_volume": 200, "domains": 2, "mailboxes": 6,
                         "sends_per_mailbox_per_day": 34, "warmup_weeks": 3}, plan(200)
    assert plan(1)["domains"] == 1 and plan(1)["mailboxes"] == 1, plan(1)
    assert plan(35)["mailboxes"] == 1 and plan(36)["mailboxes"] == 2
    assert plan(105)["domains"] == 1 and plan(106)["domains"] == 2
    for v in (1, 7, 50, 200, 500, 1000):
        p = plan(v)
        assert p["sends_per_mailbox_per_day"] <= SENDS_PER_MAILBOX, p   # never over the safe cap
        assert p["mailboxes"] <= p["domains"] * MAILBOXES_PER_DOMAIN, p
    for bad in (0, -5):
        try:
            plan(bad)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass
    print("inbox_math.py: all checks passed")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _selfcheck()
    else:
        for key, val in plan(sys.argv[1]).items():
            print(f"{key:28} {val}")
