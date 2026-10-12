from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_figure2 import EXPECTED, figure_counts, load_data


class Figure2Tests(unittest.TestCase):
    def test_released_counts(self):
        self.assertEqual(figure_counts(load_data()), EXPECTED)

    def test_included_rows_are_empirical_primary_focus(self):
        included = [row for row in load_data() if row["include_figure2"]]
        self.assertTrue(all(row["class"] == "A" for row in included))
        self.assertTrue(all(row["empirical_status"] == "Empirical" for row in included))
        self.assertTrue(all(row["period_decision"] for row in included))

    def test_subject_and_discipline_domains(self):
        data = load_data()
        self.assertEqual({row["subject"] for row in data}, {"Anti-Black", "Antisemitism"})
        self.assertEqual({row["discipline"] for row in data}, {"Economics", "Political Science", "Psychology", "Sociology"})


if __name__ == "__main__":
    unittest.main()
