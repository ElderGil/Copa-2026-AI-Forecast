from __future__ import annotations

import unittest
from datetime import date

from copa_forecast.data.contracts import OfficialMatchRecord, Team
from copa_forecast.features.recent import build_recent_team_features


class RecentFeatureTest(unittest.TestCase):
    def test_recent_features_apply_points_decay_and_importance(self) -> None:
        features = build_recent_team_features(
            teams=(
                Team(team_id="BRA", name="Brazil"),
                Team(team_id="MAR", name="Morocco"),
            ),
            matches=(
                OfficialMatchRecord(
                    match_id="m1",
                    source_id="fifa",
                    source_url="fixture",
                    match_date="2026-06-08T00:00:00Z",
                    home_team="Brazil",
                    away_team="Morocco",
                    competition="International Friendly",
                    match_importance="friendly",
                    venue_context="neutral",
                    status="completed",
                    home_score=2,
                    away_score=1,
                ),
            ),
            as_of_date=date(2026, 6, 18),
            current_window_months=12,
            max_window_months=24,
            half_life_days=10,
        )

        brazil = features["Brazil"]
        morocco = features["Morocco"]
        self.assertEqual(brazil.matches_24m, 1)
        self.assertEqual(brazil.matches_12m, 1)
        self.assertAlmostEqual(brazil.weighted_points, 1.125)
        self.assertAlmostEqual(brazil.weighted_importance, 0.375)
        self.assertGreater(brazil.weighted_goal_difference, morocco.weighted_goal_difference)
        self.assertEqual(brazil.neutral_matches, 1)


if __name__ == "__main__":
    unittest.main()
