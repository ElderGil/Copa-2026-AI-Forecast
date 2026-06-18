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

    def test_weighted_average_is_decay_consistent(self) -> None:
        # Two wins must average exactly 3.0 points/match: the decay weight now
        # cancels because it appears in both numerator and denominator.
        features = build_recent_team_features(
            teams=(Team(team_id="A", name="Alpha"),),
            matches=(
                _played("r", "2026-05-01T00:00:00Z", "Alpha", "Beta", 2, 0),
                _played("o", "2024-09-01T00:00:00Z", "Alpha", "Gamma", 1, 0),
            ),
            as_of_date=date(2026, 6, 18),
            current_window_months=12,
            max_window_months=24,
            half_life_days=180,
        )
        alpha = features["Alpha"]
        self.assertEqual(alpha.matches_24m, 2)
        self.assertAlmostEqual(alpha.weighted_points / alpha.weighted_importance, 3.0)

    def test_localized_name_variant_still_joins(self) -> None:
        features = build_recent_team_features(
            teams=(Team(team_id="USA", name="United States"),),
            matches=(
                _played("m", "2026-05-01T00:00:00Z", "UNITED STATES ", "Canada", 2, 0),
            ),
            as_of_date=date(2026, 6, 18),
            current_window_months=12,
            max_window_months=24,
            half_life_days=180,
        )
        self.assertEqual(features["United States"].matches_24m, 1)


def _played(
    match_id: str,
    match_date: str,
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
) -> OfficialMatchRecord:
    return OfficialMatchRecord(
        match_id=match_id,
        source_id="fifa",
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
