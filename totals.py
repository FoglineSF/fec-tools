#!/usr/bin/env python3
"""Fetch cycle-to-date campaign finance totals for one or more FEC committees.

Prints a table of receipts, individual contributions, candidate self-loans,
PAC contributions, and disbursements per committee.

Usage:
    export FEC_API_KEY="your_key_here"
    python totals.py C00909283
    python totals.py C00909283 C00897314 C00927558
    python totals.py --cycle 2024 C00909283
"""

import argparse

from fec_client import fec_get


def fetch_totals(committee_id, cycle):
    data = fec_get(f"/committee/{committee_id}/totals/", cycle=cycle)
    return (data.get("results") or [{}])[0]


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "committee_ids", nargs="+", help="One or more FEC committee IDs (e.g. C00909283)"
    )
    parser.add_argument(
        "--cycle", type=int, default=2026, help="Election cycle year (default 2026)"
    )
    args = parser.parse_args()

    header = (
        f"{'Committee':<14}{'Raised':>14}{'From Indiv':>14}"
        f"{'Self-Loan':>14}{'PACs':>12}{'Spent':>14}"
    )
    print(header)
    print("-" * len(header))

    for cid in args.committee_ids:
        r = fetch_totals(cid, args.cycle)
        raised = r.get("receipts", 0) or 0
        indiv = r.get("individual_contributions", 0) or 0
        loans = r.get("loans_made_by_candidate", 0) or 0
        pacs = r.get("other_political_committee_contributions", 0) or 0
        spent = r.get("disbursements", 0) or 0
        print(
            f"{cid:<14}${raised:>13,.0f}${indiv:>13,.0f}"
            f"${loans:>13,.0f}${pacs:>11,.0f}${spent:>13,.0f}"
        )


if __name__ == "__main__":
    main()
