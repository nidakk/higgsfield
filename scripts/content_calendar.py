#!/usr/bin/env python3
"""Generate a posting calendar for the 5-account TikTok Shop growth network.

Reads config/accounts.yaml (accounts, niches, posting times, phase) and
produces a day-by-day queue of post slots: which account, what time,
hook_type (always "question"), a selfie location/outfit from the daily
rotation, and whether the post is problem/solution (growth) or
shop-adjacent (phase 2). The `topic` field is left for Step 2
(docs/production_pipeline.md) to fill in directly — no trend research,
no fixed pillar list, see docs/hooks_and_scripts.md.

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

# On-screen hook text is rage-bait (docs/hooks_and_scripts.md, "Hook
# patterns") — every day uses the same hook_type. Format is flexible
# (question or flat claim), the label just distinguishes this from the
# old deprecated weekday-rotated categories (mid_sentence/bold_claim/
# reverse_psychology/etc.) that this constant replaced.
HOOK_TYPE = "question"

# Anchor date for the location/outfit rotation below. Rotation index is
# computed from days-since-this-anchor, not from the loop position within
# a single invocation — the daily batch is always run as `--days 1`, so if
# the index were loop-relative it would reset to the same value every day
# (bug found and fixed 2026-07-29: two consecutive daily runs produced an
# identical location/outfit spread instead of advancing).
ROTATION_EPOCH = datetime.date(2026, 7, 28)

# Rotation pools for Step 3a selfie avatar videos (docs/production_pipeline.md).
# Deliberately different lengths so location/outfit combos don't lock into a
# repeating pattern together. Indexed by a running per-account slot counter,
# so the day's 3 posts never repeat a setting/outfit and the pool keeps
# advancing across days instead of resetting daily.
LOCATION_POOL = [
    {"id": "home_living_room", "label": "at home in a cozy living room", "ambience": "a soft-focus couch and warm indoor lighting behind her"},
    {"id": "car_parked", "label": "in the car, parked", "ambience": "the driver's seat, soft daylight through the window, blurred interior behind her"},
    {"id": "park_path", "label": "outdoors in a park", "ambience": "green trees and grass softly blurred behind her, bright natural daylight"},
    {"id": "home_kitchen", "label": "at home in the kitchen", "ambience": "a bright counter and morning light behind her"},
    {"id": "park_bench", "label": "outdoors on a park bench", "ambience": "greenery and dappled sunlight behind her"},
    {"id": "car_passenger", "label": "in the car, passenger seat", "ambience": "a seatbelt visible, daylight through the window, blurred street behind her"},
    {"id": "backyard_patio", "label": "outdoors on a backyard patio", "ambience": "outdoor furniture and natural daylight behind her"},
]

OUTFIT_POOL = [
    "a casual light cardigan over a plain top",
    "a comfortable oversized knit sweater",
    "a plain white tank top",
    "a relaxed denim jacket over a t-shirt",
    "a soft cotton hoodie",
    "a simple blouse",
    "a cropped zip-up jacket",
    "a striped long-sleeve top",
]


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
    selfie_location: str
    selfie_location_ambience: str
    selfie_outfit: str
    status: str = "planned"


def load_config(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def generate_calendar(config: dict, start: datetime.date, days: int) -> list[PostSlot]:
    accounts = config["accounts"]
    sell_ratio = config.get("phase2_sell_ratio", 0.3)
    slots: list[PostSlot] = []

    for account_index, account in enumerate(accounts):
        # Stagger each account's rotation start so the 5 accounts don't all
        # land on the same location/outfit on the same day (they're
        # different women with independent wardrobes) — stride of 3 doesn't
        # evenly divide either pool length (7, 8), so offsets decorrelate.
        account_offset = account_index * 3
        shop_debt = 0.0
        phase = account.get("phase", "growth")

        for day_offset in range(days):
            date = start + datetime.timedelta(days=day_offset)
            hook_type = HOOK_TYPE

            for slot_index, post_time in enumerate(account["posting_times"]):
                content_type = "problem_solution"
                if phase == "shop_primed":
                    shop_debt += sell_ratio
                    if shop_debt >= 1.0:
                        content_type = "shop_adjacent"
                        shop_debt -= 1.0

                days_since_epoch = (date - ROTATION_EPOCH).days
                rotation_index = (
                    account_offset
                    + days_since_epoch * len(account["posting_times"])
                    + slot_index
                )
                location = LOCATION_POOL[rotation_index % len(LOCATION_POOL)]
                outfit = OUTFIT_POOL[rotation_index % len(OUTFIT_POOL)]

                slots.append(
                    PostSlot(
                        date=date.isoformat(),
                        time=post_time,
                        account_id=account["id"],
                        niche=account["niche"],
                        phase=phase,
                        content_type=content_type,
                        topic="TBD — fill directly in Step 2, no research",
                        hook_type=hook_type,
                        selfie_location=location["label"],
                        selfie_location_ambience=location["ambience"],
                        selfie_outfit=outfit,
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
