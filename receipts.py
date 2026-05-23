#!/usr/bin/env python3
"""Pull every itemized Schedule A contribution for a committee.

This is the raw data that powers donor-level analysis (employer aggregation,
donor-network mapping, cross-candidate overlap, geography).

Usage:
    export FEC_API_KEY="your_key_here"
    python receipts.py C00909283 wiener_receipts.json
    python receipts.py --cycle 2024 --min-date 2024-01-01 C00909283 receipts.json

Handles the known gotchas:
- Memo records (memo_code == "X") are duplicates of earmarked ActBlue
  contributions and would inflate totals if counted (dropped by default).
- Cursor pagination needs both last_contribution_receipt_amount and
  last_index passed on each call.
- The date-sorted cursor can loop when many records share a placeholder
  date, so we sort by descending amount instead.
"""

import argparse
import json

from fec_client import fec_paginate


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("committee_id", help="FEC committee ID (e.g. C00909283)")
    parser.add_argument("output", help="Output JSON file path")
    parser.add_argument(
        "--cycle", type=int, default=2026, help="Election cycle year (default 2026)"
    )
    parser.add_argument("--min-date", default=None, help="Earliest contribution date (YYYY-MM-DD)")
    parser.add_argument("--max-date", default=None, help="Latest contribution date (YYYY-MM-DD)")
    parser.add_argument(
        "--keep-memo",
        action="store_true",
        help="Keep memo_code='X' records (earmark duplicates). Off by default.",
    )
    args = parser.parse_args()

    params = {
        "committee_id": args.committee_id,
        "two_year_transaction_period": args.cycle,
        "per_page": 100,
        "sort": "-contribution_receipt_amount",
    }
    if args.min_date:
        params["min_date"] = args.min_date
    if args.max_date:
        params["max_date"] = args.max_date

    records = []
    last_print = 0
    for r in fec_paginate(
        "/schedules/schedule_a/",
        dedupe_field="sub_id",
        drop_memo=not args.keep_memo,
        **params,
    ):
        records.append(r)
        if len(records) - last_print >= 100:
            print(f"  ... {len(records)} records so far")
            last_print = len(records)

    with open(args.output, "w") as f:
        json.dump(records, f, indent=2)
    print(f"\nWrote {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
