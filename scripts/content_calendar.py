#!/usr/bin/env python3
"""Generate a posting calendar for the 5-account TikTok Shop growth network.

Reads config/accounts.yaml (accounts, niches, posting times, phase) and
produces a day-by-day queue of post slots: which account, what time,
which hook category (per the weekly hook schedule), and whether the post
is problem/solution (growth) or shop-adjacent (phase 2). The `topic`
field is left for daily trend research to fill in
(docs/production_pipeline.md, Step 1.5) — topics are no longer drawn from
a fixed pillar list, see docs/hooks_and_scripts.md.

Usage:
    content_calendar.py
    content_calendar.py --start 2026-08-01 --days 14
    content_calendar.py --format json --output output/calendar.json
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime
import json
import sys
from pathlib import Path

import yaml

# Weekly hook schedule (docs/hooks_and_scripts.md) — Monday=0 .. Sunday=6.
HOOK_SCHEDULE = {
    0: "mid_sentence",
    1: "bold_claim",
    2: "reverse_psychology",
    3: "probing",
    4: "break",
    5: "brand_to_brand",
    6: "headline_typography",
}


@dataclasses.dataclass
class PostSlot:
    date: str
    time: str
    account_id: str
    niche: str
    phase: str
    content_type: str
    topic: str
    hook_type: str
    status: str = "planned"


def load_config(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def generate_calendar(config: dict, start: datetime.date, days: int) -> list[PostSlot]:
    accounts = config["accounts"]
    sell_ratio = config.get("phase2_sell_ratio", 0.3)
    slots: list[PostSlot] = []

    for account in accounts:
        shop_debt = 0.0
        phase = account.get("phase", "growth")

        for day_offset in range(days):
            date = start + datetime.timedelta(days=day_offset)
            hook_type = HOOK_SCHEDULE[date.weekday()]
            if hook_type == "brand_to_brand" and phase != "shop_primed":
                hook_type = "mid_sentence"  # Phase 1 fallback, see docs/hooks_and_scripts.md

            for post_time in account["posting_times"]:
                content_type = "problem_solution"
                if phase == "shop_primed":
                    shop_debt += sell_ratio
                    if shop_debt >= 1.0:
                        content_type = "shop_adjacent"
                        shop_debt -= 1.0

                slots.append(
                    PostSlot(
                        date=date.isoformat(),
                        time=post_time,
                        account_id=account["id"],
                        niche=account["niche"],
                        phase=phase,
                        content_type=content_type,
                        topic="TBD — fill from daily trend research",
                        hook_type=hook_type,
                    )
                )

    slots.sort(key=lambda s: (s.date, s.time, s.account_id))
    return slots


def write_csv(slots: list[PostSlot], path: Path) -> None:
    fieldnames = [f.name for f in dataclasses.fields(PostSlot)]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for slot in slots:
            writer.writerow(dataclasses.asdict(slot))


def write_json(slots: list[PostSlot], path: Path) -> None:
    with path.open("w") as f:
        json.dump([dataclasses.asdict(s) for s in slots], f, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="config/accounts.yaml",
        help="Path to accounts config (default: config/accounts.yaml)",
    )
    parser.add_argument(
        "--start",
        help="Start date YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days to schedule (default: 7)"
    )
    parser.add_argument(
        "--format", choices=["csv", "json"], default="csv", help="Output format"
    )
    parser.add_argument(
        "--output", help="Output file path (default: output/calendar_<start>_<days>d.<ext>)"
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.exists():
        parser.error(f"Config file not found: {config_path}")

    start = (
        datetime.date.fromisoformat(args.start)
        if args.start
        else datetime.date.today()
    )

    config = load_config(config_path)
    slots = generate_calendar(config, start, args.days)

    output_path = Path(
        args.output
        or f"output/calendar_{start.isoformat()}_{args.days}d.{args.format}"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "csv":
        write_csv(slots, output_path)
    else:
        write_json(slots, output_path)

    print(f"Wrote {len(slots)} post slots to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
