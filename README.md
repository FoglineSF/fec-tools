# fec-tools

Small, dependency-free Python scripts for pulling campaign finance data from
the [FEC OpenAPI](https://api.open.fec.gov/developers/). Built for
journalists, researchers, and anyone who wants to analyze federal political
money without depending on a heavy SDK.

Pure Python standard library. No `pip install` required.

## Setup

1. Get a free FEC API key: https://api.open.fec.gov/developers/
2. Export it as an environment variable:

   ```bash
   export FEC_API_KEY="your_key_here"
   ```

3. Python 3.8 or newer.

That's it. No virtualenv, no dependencies.

## Tools

### `totals.py` — Cycle-to-date campaign finance summary

Prints a table of receipts, individual contributions, candidate self-loans,
PAC contributions, and disbursements for one or more committees.

```bash
python totals.py C00909283
python totals.py C00909283 C00897314 C00927558
python totals.py --cycle 2024 C00909283
```

Example output:

```
Committee             Raised    From Indiv     Self-Loan        PACs         Spent
----------------------------------------------------------------------------------
C00909283     $    3,958,849$    3,880,161$            0$     62,696$    2,675,040
C00897314     $    9,236,822$      415,818$    8,820,000$          0$    8,851,942
C00927558     $      649,305$      577,155$            0$     71,000$      577,288
```

### `receipts.py` — All itemized Schedule A contributions

Paginates every itemized contribution to a committee for the cycle and
writes them to a JSON file. The raw donor-level data behind most
downstream analysis (employer aggregation, donor-network mapping,
geography, etc.).

```bash
python receipts.py C00909283 wiener_receipts.json
python receipts.py --min-date 2026-04-01 C00909283 q2_receipts.json
python receipts.py --cycle 2024 --min-date 2024-01-01 C00909283 receipts.json
```

Handles the FEC API's known gotchas: cursor pagination, memo-code deduping
(earmarked ActBlue duplicates), and the date-sorted-cursor loop bug
(we sort by amount instead).

### `geography.py` — Top donor ZIP codes and state-level totals

Pulls the FEC's pre-aggregated `by_zip` and `by_state` endpoints and writes
per-committee JSON. Useful for mapping where each campaign's money
geographically comes from.

```bash
python geography.py C00909283
python geography.py C00909283 C00897314 --output-dir ./geography
python geography.py --cycle 2024 --top-zips 50 C00909283
```

### `size_distribution.py` — Small-dollar vs. max-out breakdown

Prints contribution size buckets (under $200 / $200–499 / $500–999 /
$1,000–1,999 / $2,000+) for one or more committees. Reveals each
campaign's grassroots vs. high-dollar mix.

```bash
python size_distribution.py C00909283
python size_distribution.py C00909283 C00897314 C00927558
```

The `schedule_a/by_size/` endpoint is more reliable than the committee
totals endpoint for unitemized money; the latter has been observed to
report unitemized as $0 even when there is unitemized money.

## Module: `fec_client.py`

The shared helper used by the four scripts above. If you want to write
your own pull script, import from it:

```python
from fec_client import fec_get, fec_paginate

# Single endpoint:
data = fec_get("/committee/C00909283/totals/", cycle=2026)

# Paginated Schedule A:
for record in fec_paginate(
    "/schedules/schedule_a/",
    dedupe_field="sub_id",
    drop_memo=True,
    committee_id="C00909283",
    two_year_transaction_period=2026,
    per_page=100,
    sort="-contribution_receipt_amount",
):
    print(record["contributor_name"], record["contribution_receipt_amount"])
```

Three exports:
- `get_api_key()` — reads `FEC_API_KEY` env var, exits with help text if missing
- `fec_get(endpoint, **params)` — single GET, returns parsed JSON
- `fec_paginate(endpoint, dedupe_field=None, drop_memo=True, sleep=0.3, **params)` — generator that yields records across paginated results

## Notes on the FEC API

- **Rate limits.** The default `DEMO_KEY` is capped at 30 requests/hour;
  a registered key gives you 1,000 requests/hour. These scripts wait 0.3
  seconds between paginated calls by default; tune via the `sleep`
  argument to `fec_paginate` if needed.
- **Filing-indexing lag.** Schedule A rows from a freshly filed report may
  not appear in the searchable API for hours or days after the filing is
  accepted. If you're chasing pre-election filings, check the filing PDF
  directly at `docquery.fec.gov` and verify the API caught up later.
- **Committee IDs.** Always start with `C` and are nine characters. Look
  one up at https://www.fec.gov/data/committees/.

## License

MIT. See [LICENSE](LICENSE).

## Provenance

Extracted from the research codebase behind a 2026 FoglineSF investigation
into who's funding California State Senator Scott Wiener's bid for the
CA-11 congressional seat being vacated by Nancy Pelosi. These four scripts
are the generic, reusable extracts.

Related: [foglinesf.com](https://foglinesf.com) — the FoglineSF newsletter.

Contributions welcome. Issues and PRs especially appreciated if you spot
bugs in the cursor pagination logic, or want to add coverage for other
FEC endpoints (Schedule B disbursements, committee search, candidate
lookups, the e-filing realtime feed).
