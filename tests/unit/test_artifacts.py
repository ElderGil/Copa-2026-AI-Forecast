from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from copa_forecast.reporting.artifacts import write_excel_safe_csv, write_json


class ArtifactTest(unittest.TestCase):
    def test_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "nested" / "run.json"
            write_json(target, {"ok": True})
            self.assertTrue(target.exists())

    def test_writes_csv_with_bom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "ranking.csv"
            write_excel_safe_csv(target, [{"team": "Brasil"}], fieldnames=["team"])
            self.assertEqual(target.read_bytes()[:3], b"\xef\xbb\xbf")


if __name__ == "__main__":
    unittest.main()

