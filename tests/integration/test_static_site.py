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
            self.assertIn("data-panel-drivers", index)
            self.assertIn("Brasil", index)
            self.assertIn("🇧🇷", index)
            self.assertIn("flag-emoji", index)
            self.assertIn("openPanel", script)
            self.assertIn("renderDrivers", script)
            self.assertNotIn("alert(", script)
            # Open Graph image + favicon for social sharing.
            self.assertIn('property="og:image"', index)
            self.assertIn('rel="icon"', index)
            # The sample fixture is not calibrated, so the badge must warn.
            self.assertEqual(latest["calibration_status"], "not_calibrated_mvp_baseline")
            self.assertIn("não calibrado", index)
            self.assertNotIn("temperature scaling", index)

    def test_calibration_badge_reflects_temperature_scaling(self) -> None:
        latest = json.loads(Path("tests/fixtures/latest_sample.json").read_text())
        latest["calibration_status"] = "temperature_scaled_from_backtest:T=2.794"
        with tempfile.TemporaryDirectory() as tmp:
            render_static_page(
                latest=latest,
                github_url="https://github.com/example/repo",
                output_dir=tmp,
            )
            index = (Path(tmp) / "index.html").read_text(encoding="utf-8")
            self.assertIn("temperature scaling", index)
            self.assertIn("T=2.794", index)
            self.assertNotIn("não calibrado", index)


if __name__ == "__main__":
    unittest.main()
