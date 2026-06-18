from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from copa_forecast.cli import explain


class ExplainCliIntegrationTest(unittest.TestCase):
    def test_explain_command_writes_json_and_excel_safe_csvs(self) -> None:
        latest = json.loads(Path("tests/fixtures/latest_sample.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            latest_path = root / "latest.json"
            output_dir = root / "explain"
            latest_path.write_text(json.dumps(latest), encoding="utf-8")

            exit_code = explain(
                latest_json=str(latest_path),
                output=str(output_dir),
                team="Brazil",
            )

            payload = json.loads((output_dir / "explanations.json").read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["team_count"], 1)
            self.assertEqual(payload["teams"][0]["team"], "Brazil")
            self.assertTrue((output_dir / "explanations.csv").read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertTrue((output_dir / "pillars.csv").read_bytes().startswith(b"\xef\xbb\xbf"))


if __name__ == "__main__":
    unittest.main()
