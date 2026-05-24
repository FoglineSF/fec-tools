#!/usr/bin/env python3
"""Download and parse a single FEC electronic filing (.fec file).

Useful when you need data that's been *filed* but not yet *indexed* in the
FEC's searchable API. This happens for hours-to-weeks after a filing is
submitted, which matters most for pre-election filings (12P pre-primary
reports, F6 48-hour contribution notices) where the API lag prevents you
from seeing the latest contributions.

Usage:
    python filing.py <file_number> [output.json]
    python filing.py 1978834                    # write Schedule A JSON to stdout
    python filing.py 1978834 wiener_12p.json    # write to file

Find a filing's file_number with:
    python -c "from fec_client import fec_get; \\
        import json; print(json.dumps( \\
        fec_get('/filings/', committee_id='C00909283', per_page=5, sort='-receipt_date'), \\
        indent=2))"

This script requires the `fecfile` library:
    pip install fecfile
    # or
    uv add fecfile

That's the only dependency in the entire fec-tools toolkit — everything else
is stdlib-only. The .fec format is genuinely complex (variable field layouts
by schedule subtype, version-dependent schemas) and re-implementing the
parser would be a substantial undertaking.
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path

try:
    import fecfile
except ImportError:
    sys.exit(
        "ERROR: this script requires the `fecfile` library.\n"
        "Install: pip install fecfile  (or `uv add fecfile`)"
    )

DOCQUERY_URL = "https://docquery.fec.gov/dcdev/posted/{file_number}.fec"


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "file_number",
        help="The 7-digit FEC e-filing ID (e.g. 1978834 for a specific 12P report)",
    )
    parser.add_argument(
        "output", nargs="?", default=None, help="Output JSON file path (default: stdout)"
    )
    parser.add_argument(
        "--schedule",
        default="Schedule A",
        help="Schedule to extract (default 'Schedule A'). "
        "Other options: 'Schedule B', 'Schedule C', 'Schedule D', 'Schedule E'.",
    )
    parser.add_argument(
        "--keep-fec",
        action="store_true",
        help="Keep the downloaded .fec file (default deletes after parsing)",
    )
    args = parser.parse_args()

    url = DOCQUERY_URL.format(file_number=args.file_number)
    tmp_path = Path(f"/tmp/fec_{args.file_number}.fec")

    print(f"Downloading {url}...", file=sys.stderr)
    urllib.request.urlretrieve(url, tmp_path)
    print(f"  -> {tmp_path} ({tmp_path.stat().st_size:,} bytes)", file=sys.stderr)

    parsed = fecfile.from_file(str(tmp_path))
    records = parsed.get("itemizations", {}).get(args.schedule, [])
    print(f"Parsed {len(records)} {args.schedule} records", file=sys.stderr)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(records, f, indent=2, default=str)
        print(f"Wrote to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(records, indent=2, default=str))

    if not args.keep_fec:
        tmp_path.unlink()


if __name__ == "__main__":
    main()
