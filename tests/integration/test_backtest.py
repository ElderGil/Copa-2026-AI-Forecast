from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from copa_forecast.cli import backtest


class BacktestCliIntegrationTest(unittest.TestCase):
    def test_backtest_command_writes_report_and_excel_safe_csvs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "forecast.json"
            matches_path = root / "matches.json"
            output_dir = root / "public"
            config_path.write_text(
                json.dumps(
                    {
                        "run_id": "backtest-command",
                        "as_of_date": "2026-06-18",
                        "project_github_url": "https://github.com/example/copa",
                        "official_fifa": {
                            "raw_output_dir": str(root / "raw" / "fifa"),
                            "sources": [
                                {
                                    "source_id": "sample-fifa-fixtures",
                                    "url": str(
                                        Path(
                                            "tests/fixtures/fifa/sample_competition_state.json"
                                        ).resolve()
                                    ),
                                    "purpose": "fixtures",
                                }
                            ],
                        },
                        "feature_windows": {
                            "current_months": 12,
                            "max_months": 24,
                            "decay_half_life_days": 180,
                        },
                        "simulation": {"tournament_ruleset": "fifa-world-cup-2026"},
                        "site": {"output_dir": str(output_dir)},
                    }
                ),
                encoding="utf-8",
            )
            matches_path.write_text(
                json.dumps(
                    {
                        "matches": [
                            _match("m1", "2025-01-10T00:00:00Z", "Brazil", "Morocco", 2, 0),
                            _match("m2", "2025-03-10T00:00:00Z", "Brazil", "Mexico", 1, 1),
                            _match("m3", "2025-04-10T00:00:00Z", "Morocco", "Mexico", 0, 1),
                            _match("m4", "2026-01-10T00:00:00Z", "Brazil", "Morocco", 1, 0),
                        ]
                    }
                ),
                encoding="utf-8",
            )

            exit_code = backtest(
                str(config_path),
                matches_path=str(matches_path),
                evaluation_months=12,
                lookback_months=24,
                min_prior_matches=2,
                bin_count=5,
            )

            run_dir = root / "data" / "processed" / "backtests" / "backtest-command"
            report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            readme = (root / "README.md").read_text(encoding="utf-8")
            self.assertEqual(exit_code, 0)
            self.assertEqual(report["sample_count"], 1)
            self.assertEqual(report["primary_baseline_name"], "fifa_sum_style_elo_baseline")
            self.assertTrue((run_dir / "samples.csv").read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertTrue(
                (run_dir / "calibration_bins.csv").read_bytes().startswith(b"\xef\xbb\xbf")
            )
            self.assertIn("Copa 2026 AI Forecast", readme)
            self.assertIn("<sub><em>Percentual de vezes", readme)


def _match(
    match_id: str,
    match_date: str,
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
) -> dict[str, object]:
    return {
        "match_id": match_id,
        "source_id": "test",
        "source_url": "fixture",
        "match_date": match_date,
        "home_team": home_team,
        "away_team": away_team,
        "competition": "International Friendly",
        "match_importance": "friendly",
        "venue_context": "neutral",
        "status": "completed",
        "home_score": home_score,
        "away_score": away_score,
    }


if __name__ == "__main__":
    unittest.main()
