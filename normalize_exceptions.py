#!/usr/bin/env python3
"""Normalize FreightWorks exception exports without guessing missing data.

Usage:
    python3 normalize_exceptions.py --input exceptions_input.csv --output-dir .

Creates normalized_exceptions.csv and event_summary.csv.
Requires only the Python standard library (Python 3.9+).

Important: The export has no documented source timezone. Naive timestamps are
formatted as ISO 8601 but are intentionally *not* assumed to be UTC.
"""

import argparse
import csv
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_COLUMNS = {"exception_id", "terminal", "event_type", "carrier_code", "event_ts"}
OUTPUT_COLUMNS = [
    "exception_id", "terminal", "event_type", "carrier_code",
    "event_ts_iso8601", "timezone_status", "quality_notes",
]


def normalize_terminal(raw: str) -> tuple[str, str]:
    value = (raw or "").strip()
    match = re.fullmatch(r"(?:terminal\s*|t\s*)([1-3])", value, flags=re.IGNORECASE)
    if match:
        return f"Terminal {match.group(1)}", ""
    return value, "unrecognized_or_missing_terminal"


def normalize_carrier(raw: str) -> tuple[str, str]:
    value = (raw or "").strip().upper()
    if not value:
        return "", "missing_carrier_code"
    return value, ""


def normalize_timestamp(raw: str) -> tuple[str, str, str]:
    value = (raw or "").strip()
    if not value:
        return "", "unknown", "missing_timestamp"

    try:
        if "/" in value:
            # The provided US-style dates have day values of 14/15, so MM/DD is clear.
            parsed = datetime.strptime(value, "%m/%d/%Y %H:%M")
        else:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value, "unknown", "unparseable_timestamp"

    if parsed.tzinfo is not None and parsed.utcoffset() is not None:
        # An explicit offset makes conversion to UTC safe.
        utc = parsed.astimezone(timezone.utc)
        return utc.strftime("%Y-%m-%dT%H:%M:%SZ"), "UTC_confirmed_from_source", ""

    # Standardize *format*, not *timezone*: we have no evidence to add 'Z'.
    return parsed.isoformat(timespec="seconds"), "source_timezone_unspecified", "timezone_not_specified"


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    notes = []
    terminal, terminal_note = normalize_terminal(row.get("terminal", ""))
    carrier, carrier_note = normalize_carrier(row.get("carrier_code", ""))
    timestamp, timezone_status, timestamp_note = normalize_timestamp(row.get("event_ts", ""))
    for note in (terminal_note, carrier_note, timestamp_note):
        if note:
            notes.append(note)
    event_type = (row.get("event_type") or "").strip().lower().replace(" ", "_")
    if not event_type:
        notes.append("missing_event_type")
    if not (row.get("exception_id") or "").strip():
        notes.append("missing_exception_id")

    return {
        "exception_id": (row.get("exception_id") or "").strip(),
        "terminal": terminal,
        "event_type": event_type,
        "carrier_code": carrier,
        "event_ts_iso8601": timestamp,
        "timezone_status": timezone_status,
        "quality_notes": "; ".join(notes),
    }


def process(input_path: Path, output_dir: Path) -> tuple[list[dict[str, str]], Counter]:
    with input_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Input is missing required columns: {', '.join(sorted(missing))}")
        records = [normalize_row(row) for row in reader]

    counts = Counter(record["event_type"] or "UNKNOWN" for record in records)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "normalized_exceptions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(records)
    with (output_dir / "event_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["event_type", "count"])
        for event, count in sorted(counts.items()):
            writer.writerow([event, count])
        writer.writerow(["TOTAL", len(records)])

    print(f"Records processed: {len(records)}")
    print("Exception counts by event type:")
    for event, count in sorted(counts.items()):
        print(f"  {event}: {count}")
    print(f"  TOTAL: {len(records)}")
    print("Records requiring data-quality follow-up:")
    any_issues = False
    for record in records:
        if record["quality_notes"]:
            any_issues = True
            print(f"  {record['exception_id']}: {record['quality_notes']}")
    if not any_issues:
        print("  None")
    return records, counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("exceptions_input.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    process(args.input, args.output_dir)


if __name__ == "__main__":
    main()