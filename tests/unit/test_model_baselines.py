from __future__ import annotations

import unittest

from copa_forecast.data.contracts import OfficialMatchRecord
from copa_forecast.models.baselines import fifa_sum_ratings, three_way_baseline


class ModelBaselinesTest(unittest.TestCase):
    def test_fifa_sum_rating_rewards_winner_and_debits_loser(self) -> None:
        ratings = fifa_sum_ratings(
            (
                _match("m1", "2025-01-10T00:00:00Z", "Brazil", "Germany", 2, 0),
            )
        )

        self.assertGreater(ratings["Brazil"], 1500.0)
        self.assertLess(ratings["Germany"], 1500.0)

    def test_draw_can_be_most_likely_for_level_matchup(self) -> None:
        probs = three_way_baseline(1500.0, 1500.0)
        self.assertAlmostEqual(probs["win"] + probs["draw"] + probs["loss"], 1.0)
        self.assertGreaterEqual(probs["draw"], probs["win"])
        self.assertGreaterEqual(probs["draw"], probs["loss"])

    def test_draw_probability_shrinks_as_rating_gap_grows(self) -> None:
        level = three_way_baseline(1500.0, 1500.0)
        mismatch = three_way_baseline(1900.0, 1300.0)
        self.assertGreater(level["draw"], mismatch["draw"])

    def test_home_advantage_favors_the_listed_team(self) -> None:
        neutral = three_way_baseline(1500.0, 1500.0)
        home = three_way_baseline(1500.0, 1500.0, home_advantage=65.0)
        self.assertGreater(home["win"], neutral["win"])
        self.assertLess(home["loss"], neutral["loss"])


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
