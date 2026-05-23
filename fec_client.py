"""Minimal FEC OpenAPI client used by the fec-tools scripts.

Pure stdlib, no dependencies. Centralises the common plumbing:
- API key handling (FEC_API_KEY env var)
- Single GET requests
- Cursor pagination across multi-page result sets
- Polite rate limiting between calls

Get a free API key at: https://api.open.fec.gov/developers/
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE_URL = "https://api.open.fec.gov/v1"


def get_api_key():
    """Read FEC_API_KEY from env. Exit with help text if missing."""
    key = os.environ.get("FEC_API_KEY")
    if not key:
        sys.exit(
            "ERROR: set FEC_API_KEY environment variable.\n"
            "Get a free key at: https://api.open.fec.gov/developers/\n"
            "Then: export FEC_API_KEY=your_key_here"
        )
    return key


def fec_get(endpoint, **params):
    """Single GET to the FEC API. Returns parsed JSON.

    Args:
        endpoint: API path (e.g. "/committee/C00909283/totals/")
        **params: query string parameters
    """
    params = {"api_key": get_api_key(), **params}
    url = f"{BASE_URL}{endpoint}?{urllib.parse.urlencode(params, doseq=True)}"
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read())


def fec_paginate(endpoint, dedupe_field=None, drop_memo=True, sleep=0.3, **params):
    """Iterate every record across paginated FEC results using cursor pagination.

    The FEC API returns a pagination.last_indexes object on each page that
    must be passed back on the next request to advance the cursor. This
    helper handles that automatically and yields records one at a time.

    Args:
        endpoint: API path (e.g. "/schedules/schedule_a/")
        dedupe_field: optional record field for de-duplicating across pages
            (e.g. "sub_id" for Schedule A — guards against the cursor
            occasionally returning the same record twice)
        drop_memo: if True, skip records with memo_code == "X". Memo records
            on Schedule A are duplicates of earmarked contributions and
            inflate totals if counted.
        sleep: seconds to wait between API calls (default 0.3)
        **params: query string parameters

    Yields:
        Individual record dicts.
    """
    params = {"api_key": get_api_key(), **params}
    seen = set()
    last_indexes = {}

    while True:
        query = {**params, **last_indexes}
        url = f"{BASE_URL}{endpoint}?{urllib.parse.urlencode(query, doseq=True)}"
        with urllib.request.urlopen(url) as r:
            data = json.loads(r.read())

        results = data.get("results") or []
        if not results:
            break

        for record in results:
            if drop_memo and record.get("memo_code") == "X":
                continue
            if dedupe_field:
                key = record.get(dedupe_field)
                if key in seen:
                    continue
                seen.add(key)
            yield record

        pagination = data.get("pagination") or {}
        last = pagination.get("last_indexes") or {}
        if not last:
            break
        # pagination.last_indexes already uses the correct query param names
        # (e.g. last_contribution_receipt_amount, last_index). Pass through
        # without modification — adding a "last_" prefix double-prefixes
        # and silently breaks the cursor.
        last_indexes = dict(last)
        time.sleep(sleep)
