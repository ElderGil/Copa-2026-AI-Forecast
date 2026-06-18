from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from copa_forecast.site.static_page import render_static_page


class StaticSiteTest(unittest.TestCase):
    def test_renders_index_and_latest_json(self) -> None:
        latest = json.loads(Path("tests/fixtures/latest_sample.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            render_static_page(
                latest=latest,
                github_url="https://github.com/example/repo",
                output_dir=tmp,
            )
            index = (Path(tmp) / "index.html").read_text(encoding="utf-8")
            script = (Path(tmp) / "app.js").read_text(encoding="utf-8")
            self.assertTrue((Path(tmp) / "index.html").exists())
            self.assertTrue((Path(tmp) / "data" / "latest.json").exists())
            self.assertIn("team-panel", index)
            self.assertIn("forecast-data", index)
            self.assertIn("openPanel", script)
            self.assertNotIn("alert(", script)


if __name__ == "__main__":
    unittest.main()
