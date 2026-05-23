#!/usr/bin/env python3
"""Pull top donor ZIP codes and state-level breakdowns for FEC committees.

Output: per-committee JSON with top ZIPs (sorted by total) and all states.
Useful for "where does each campaign's money come from geographically" maps.

Usage:
    export FEC_API_KEY="your_key_here"
    python geography.py C00909283
    python geography.py C00909283 C00897314 --output-dir ./geography
    python geography.py --cycle 2024 --top-zips 50 C00909283
"""

import argparse
import json
from pathlib import Path

from fec_client import fec_get


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("committee_ids", nargs="+", help="One or more FEC committee IDs")
    parser.add_argument(
        "--cycle", type=int, default=2026, help="Election cycle year (default 2026)"
    )
    parser.add_argument(
        "--output-dir", default=".", help="Directory for output JSON files (default current dir)"
    )
    parser.add_argument(
        "--top-zips", type=int, default=25, help="Number of top ZIPs to keep (default 25)"
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for cid in args.committee_ids:
        zips = (
            fec_get(
                "/schedules/schedule_a/by_zip/",
                cycle=args.cycle,
                committee_id=cid,
                per_page=100,
            ).get("results")
            or []
        )
        states = (
            fec_get(
                "/schedules/schedule_a/by_state/",
                cycle=args.cycle,
                committee_id=cid,
            ).get("results")
            or []
        )

        zips.sort(key=lambda r: r.get("total", 0) or 0, reverse=True)
        states.sort(key=lambda r: r.get("total", 0) or 0, reverse=True)
        total_itemized = sum((r.get("total") or 0) for r in zips)

        out = {
            "committee_id": cid,
            "cycle": args.cycle,
            "top_zips": zips[: args.top_zips],
            "states": states,
            "total_itemized": total_itemized,
        }
        path = out_dir / f"{cid}_geography.json"
        path.write_text(json.dumps(out, indent=2))
        print(
            f"{cid}: {len(zips)} ZIPs, total itemized ${total_itemized:,.0f}, "
            f"written to {path}"
        )


if __name__ == "__main__":
    main()
