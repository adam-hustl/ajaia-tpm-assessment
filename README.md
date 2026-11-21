# FreightWorks Exception Export Normalizer

A small, runnable Python solution for **Task 2 of the Ajaia Technical Project Manager Assessment**. The sample data represents five exceptions from Corrigan Peak Logistics' Terminal 3 feed.

## What it does

- Normalizes terminal aliases such as `T3` and `Terminal 3` to `Terminal 3`.
- Uppercases and trims carrier codes, while preserving an unknown/missing code as blank.
- Converts supported timestamp formats to ISO 8601, without assigning an unverified timezone. The one source timestamp ending in `Z` is UTC; the four timestamps with no timezone remain without an offset and are flagged for follow-up.
- Produces a row-level normalized export, an event-type summary, and a console report of data-quality issues.

**This is a demonstration data-cleaning utility, not a production FreightWorks integration or a fix for the live Terminal 3 field-mapping issue (DET-121).** The actual mapping must still be confirmed with Corrigan Peak IT.

## Requirements

Python 3.9 or newer. No third-party packages.

## Run

```bash
python3 normalize_exceptions.py --input exceptions_input.csv --output-dir .
```

Two output files are created in the current directory:

- `normalized_exceptions.csv` — all five records with consistent formatting and quality notes.
- `event_summary.csv` — clean counts grouped by event type, plus a total.

## Expected summary

| Event type | Count |
| --- | ---: |
| `missed_pickup` | 2 |
| `doc_mismatch` | 2 |
| `carrier_substitution` | 1 |
| **Total** | **5** |

## Data-quality findings

- `CPX-88216` has **no carrier code**. The script leaves it blank instead of guessing from another row.
- `CPX-88213`, `CPX-88214`, `CPX-88216`, and `CPX-88217` contain **no timezone indicator**. Their date and time are normalized but not converted to UTC; each receives `timezone_not_specified`.
- `CPX-88215` explicitly supplies `Z` (UTC); it remains UTC.

## Verify

```bash
python3 -m unittest -v test_normalize_exceptions.py
```

The seven automated tests cover terminal aliases, carrier casing and missing carrier values, mixed timestamp formats, unknown timezones, the five-row event totals, invalid timestamps, and unexpected terminals. The sample has been executed and all seven checks passed.

## Files

- `normalize_exceptions.py` — runnable build.
- `exceptions_input.csv` — assessment source data.
- `test_normalize_exceptions.py` — automated regression checks.
- `normalized_exceptions.csv` — sample normalized output.
- `event_summary.csv` — sample event summary.

Assessment context: [Ajaia](https://ajaia.ai).