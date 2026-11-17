from pathlib import Path
import csv
import hashlib
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_figure2 import (  # noqa: E402
    CHECKSUMS, DATA, DISCIPLINES, EXCLUSIONS, EXPECTED, LEDGER_FIELDS, WORKBOOK,
    build_ledger, figure_counts, load_data, read_csv,
)


class Figure2Tests(unittest.TestCase):
    def test_published_counts(self):
        counts = figure_counts(load_data())
        self.assertEqual(counts, EXPECTED)
        self.assertEqual(sum(v for (_, s), v in counts.items() if s == "Anti-Black"), 163)
        self.assertEqual(sum(v for (_, s), v in counts.items() if s == "Antisemitism"), 12)

    def test_ledger_rebuilds_from_master_census(self):
        rebuilt = build_ledger(read_csv(DATA / "master_census.csv"))
        committed = read_csv(DATA / "figure2_papers.csv")
        self.assertEqual(rebuilt, committed)
        self.assertEqual(list(committed[0]), LEDGER_FIELDS)

    def test_ledger_covers_every_empirical_primary_focus_record(self):
        data = load_data()
        self.assertEqual(len(data), 199)
        self.assertTrue(all(row["class"] == "A" and row["empirical_status"] == "Empirical" for row in data))
        self.assertTrue(all(row["period_decision"] for row in data))

    def test_every_exclusion_matches_one_ledger_row(self):
        exclusions = read_csv(EXCLUSIONS)
        self.assertEqual(len(exclusions), 24)
        excluded = {row["record_id"] for row in load_data() if not row["include_figure2"]}
        self.assertEqual({row["record_id"] for row in exclusions}, excluded)

    def test_subject_and_discipline_domains(self):
        data = load_data()
        self.assertEqual({row["subject"] for row in data}, {"Anti-Black", "Antisemitism"})
        self.assertEqual({row["discipline"] for row in data}, set(DISCIPLINES))

    def test_source_files_match_checksums(self):
        expected = json.loads(CHECKSUMS.read_text(encoding="utf-8"))
        for relative, digest in expected.items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest, relative)
        self.assertIn(WORKBOOK.relative_to(ROOT).as_posix(), expected)

    def test_counts_output_matches_ledger(self):
        with (ROOT / "outputs" / "figure_2_counts.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual({(r["Discipline"], s): int(r[s]) for r in rows for s in ("Anti-Black", "Antisemitism")}, EXPECTED)


if __name__ == "__main__":
    unittest.main()
