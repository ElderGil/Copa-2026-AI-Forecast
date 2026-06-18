from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from copa_forecast.cli import forecast


class ForecastRunIntegrationTest(unittest.TestCase):
    def test_forecast_command_writes_latest_site_and_metadata(self) -> None:
        fixture = Path("tests/fixtures/fifa/sample_competition_state.json").resolve()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "forecast.json"
            output_dir = root / "public"
            config_path.write_text(
                json.dumps(
                    {
                        "run_id": "integration-forecast",
                        "as_of_date": "2026-06-18",
                        "project_github_url": "https://github.com/example/copa",
                        "official_fifa": {
                            "raw_output_dir": str(root / "raw" / "fifa"),
                            "allow_cached_payloads": True,
                            "degraded_mode_allowed": False,
                            "sources": [
                                {
                                    "source_id": "sample-fifa-fixtures",
                                    "url": str(fixture),
                                    "purpose": "fixtures",
                                }
                            ],
                        },
                        "feature_windows": {
                            "current_months": 12,
                            "max_months": 24,
                            "decay_half_life_days": 180,
                        },
                        "simulation": {
                            "tournament_ruleset": "fifa-world-cup-2026",
                            "runs": 1000,
                            "random_seed": 20260618,
                        },
                        "site": {
                            "language": "pt-BR",
                            "output_dir": str(output_dir),
                            "top_count": 10,
                        },
                    }
                ),
                encoding="utf-8",
            )

            exit_code = forecast(str(config_path))

            latest_path = output_dir / "data" / "latest.json"
            metadata_path = root / "data" / "processed" / "forecast_runs" / "integration-forecast" / "metadata.json"
            csv_path = metadata_path.with_name("teams.csv")
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            probabilities = [team["champion_probability"] for team in latest["teams"]]
            self.assertEqual(exit_code, 0)
            self.assertTrue((output_dir / "index.html").exists())
            self.assertTrue(metadata_path.exists())
            self.assertTrue(csv_path.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertEqual(len(latest["teams"]), 4)
            self.assertAlmostEqual(sum(probabilities), 1.0)
            self.assertIn("official_competition_state", latest["teams"][0]["used_pillars"])
            self.assertIn("recent_form_window", latest["teams"][0]["excluded_pillars"])


if __name__ == "__main__":
    unittest.main()
