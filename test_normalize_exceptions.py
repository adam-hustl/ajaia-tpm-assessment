"""Small regression checks for the assessment normalization script.

Run: python3 -m unittest -v test_normalize_exceptions.py
"""
import csv
import tempfile
import unittest
from pathlib import Path

from normalize_exceptions import normalize_carrier, normalize_terminal, normalize_timestamp, process

HERE = Path(__file__).resolve().parent


class NormalizerTests(unittest.TestCase):
    def test_terminal_aliases(self):
        self.assertEqual(normalize_terminal("T3"), ("Terminal 3", ""))
        self.assertEqual(normalize_terminal("Terminal 3"), ("Terminal 3", ""))

    def test_carrier_case_and_missing_not_imputed(self):
        self.assertEqual(normalize_carrier("swft"), ("SWFT", ""))
        self.assertEqual(normalize_carrier("Swft"), ("SWFT", ""))
        self.assertEqual(normalize_carrier(""), ("", "missing_carrier_code"))

    def test_mixed_timestamp_formats(self):
        self.assertEqual(normalize_timestamp("08/14/2026 09:45")[0], "2026-08-14T09:45:00")
        self.assertEqual(normalize_timestamp("2026-08-14 09:12:00")[0], "2026-08-14T09:12:00")
        self.assertEqual(normalize_timestamp("2026-08-14T10:03:00Z")[0], "2026-08-14T10:03:00Z")

    def test_unknown_timezone_is_not_invented(self):
        value, status, issue = normalize_timestamp("2026-08-14 09:12:00")
        self.assertFalse(value.endswith("Z"))
        self.assertEqual(status, "source_timezone_unspecified")
        self.assertEqual(issue, "timezone_not_specified")

    def test_sample_counts_and_quality_flags(self):
        with tempfile.TemporaryDirectory() as temp:
            records, counts = process(HERE / "exceptions_input.csv", Path(temp))
            self.assertEqual(len(records), 5)
            self.assertEqual(dict(counts), {"missed_pickup": 2, "doc_mismatch": 2, "carrier_substitution": 1})
            self.assertEqual({row["terminal"] for row in records}, {"Terminal 3"})
            self.assertEqual(records[2]["carrier_code"], "SWFT")
            self.assertEqual(records[3]["carrier_code"], "")
            self.assertIn("missing_carrier_code", records[3]["quality_notes"])
            self.assertEqual(sum(r["timezone_status"] == "source_timezone_unspecified" for r in records), 4)
            with (Path(temp) / "event_summary.csv").open(newline="", encoding="utf-8") as handle:
                summary = list(csv.DictReader(handle))
            self.assertEqual(summary[-1], {"event_type": "TOTAL", "count": "5"})

    def test_bad_timestamp_is_flagged_not_guessed(self):
        self.assertEqual(normalize_timestamp("not-a-date"), ("not-a-date", "unknown", "unparseable_timestamp"))

    def test_unexpected_terminal_flagged(self):
        self.assertEqual(normalize_terminal("dock-X"), ("dock-X", "unrecognized_or_missing_terminal"))


if __name__ == "__main__":
    unittest.main()
