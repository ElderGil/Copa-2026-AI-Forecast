from __future__ import annotations

import unittest
from datetime import date

from copa_forecast.data.contracts import OfficialMatchRecord
from copa_forecast.models.evaluation import rolling_origin_backtest


class EvaluationBacktestTest(unittest.TestCase):
    def test_rolling_origin_uses_only_prior_matches(self) -> None:
        report = rolling_origin_backtest(
            matches=(
                _match("m1", "2025-01-10T00:00:00Z", "Brazil", "Morocco", 2, 0),
                _match("m2", "2025-03-10T00:00:00Z", "Brazil", "Mexico", 1, 1),
                _match("m3", "2025-04-10T00:00:00Z", "Morocco", "Mexico", 0, 1),
                _match("m4", "2026-01-10T00:00:00Z", "Brazil", "Morocco", 1, 0),
                _match("same-day", "2026-01-10T12:00:00Z", "Brazil", "Morocco", 7, 0),
            ),
            as_of_date=date(2026, 6, 18),
            evaluation_months=12,
            lookback_months=24,
            half_life_days=180,
            min_prior_matches=2,
            bin_count=5,
        )

        self.assertEqual(report["sample_count"], 2)
        self.assertEqual(report["temporal_validation"]["method"], "rolling_origin")
        first_sample = report["samples"][0]
        self.assertEqual(first_sample["match_id"], "m4")
        self.assertEqual(first_sample["prior_home_matches"], 2)
        self.assertEqual(first_sample["prior_away_matches"], 2)
        self.assertIn("brier_score", report["metrics"])
        self.assertIn("fifa_sum_style", report["baselines"])
        self.assertEqual(report["primary_baseline_name"], "fifa_sum_style_elo_baseline")
        self.assertIn("fifa_sum_home_win_probability", first_sample)
        self.assertIn("expected_calibration_error", report["calibration"])


def _match(
    match_id: str,
    match_date: str,
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
) -> OfficialMatchRecord:
    return OfficialMatchRecord(
        match_id=match_id,
        source_id="test",
        source_url="fixture",
        match_date=match_date,
        home_team=home_team,
        away_team=away_team,
        competition="International Friendly",
        match_importance="friendly",
        venue_context="neutral",
        status="completed",
        home_score=home_score,
        away_score=away_score,
    )


if __name__ == "__main__":
    unittest.main()
