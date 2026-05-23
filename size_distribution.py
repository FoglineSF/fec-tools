#!/usr/bin/env python3
"""Pull contribution size distribution for one or more FEC committees.

Reveals each committee's small-dollar vs. max-out split. Useful when
comparing grassroots appeal across campaigns.

Size buckets:
    - size=0     unitemized (under $200)
    - size=200   $200-$499
    - size=500   $500-$999
    - size=1000  $1,000-$1,999
    - size=2000  $2,000 and up

The schedule_a/by_size/ endpoint is more reliable than the committee
totals endpoint for unitemized money; the latter has been observed to
report unitemized as $0 even when there is unitemized money.

Usage:
    export FEC_API_KEY="your_key_here"
    python size_distribution.py C00909283
    python size_distribution.py C00909283 C00897314 C00927558
"""

import argparse

from fec_client import fec_get

LABELS = {
    0: "$0-199 (unitemized)",
    200: "$200-499",
    500: "$500-999",
    1000: "$1,000-1,999",
    2000: "$2,000+",
}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("committee_ids", nargs="+", help="One or more FEC committee IDs")
    parser.add_argument(
        "--cycle", type=int, default=2026, help="Election cycle year (default 2026)"
    )
    args = parser.parse_args()

    for cid in args.committee_ids:
        print(f"\n=== {cid} ===")
        data = fec_get(
            "/schedules/schedule_a/by_size/",
            cycle=args.cycle,
            committee_id=cid,
        )
        results = sorted(data.get("results") or [], key=lambda x: x.get("size", 0))
        total = 0.0
        unitemized = 0.0
        for r in results:
            size = r.get("size", 0)
            amt = float(r.get("total") or 0)
            cnt = r.get("count")
            total += amt
            if size == 0:
                unitemized = amt
            count_str = f"{cnt} contribs" if cnt else "(aggregate only)"
            print(f"  {LABELS.get(size, size):<24} ${amt:>12,.2f}  {count_str}")
        small_share = (unitemized / total * 100) if total else 0
        print(f"  {'TOTAL':<24} ${total:>12,.2f}")
        print(f"  Small-dollar (<$200) share: {small_share:.1f}%")


if __name__ == "__main__":
    main()
