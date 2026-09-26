import csv
import tempfile
import unittest
from pathlib import Path

from analyze import analyze
from generate_data import make_rows, write_csv


class ReadmissionTests(unittest.TestCase):
    def test_generator_is_reproducible(self):
        self.assertEqual(make_rows(100, 7), make_rows(100, 7))

    def test_analysis_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "encounters.csv"
            write_csv(source, 200, 7)
            result = analyze(source, root / "report")
            self.assertEqual(result["encounters"], 200)
            self.assertTrue((root / "report/dashboard.html").exists())
            with (root / "report/department_summary.csv").open(newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 5)

    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "encounters.csv"
            write_csv(source, 20)
            lines = source.read_text().splitlines()
            source.write_text("\n".join([*lines, lines[1]]) + "\n")
            with self.assertRaises(ValueError):
                analyze(source, Path(temporary) / "report")


if __name__ == "__main__":
    unittest.main()
