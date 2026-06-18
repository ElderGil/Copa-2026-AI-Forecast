from __future__ import annotations

import unittest

from copa_forecast.data.contracts import OfficialMatchRecord
from copa_forecast.models.baselines import fifa_sum_ratings


class ModelBaselinesTest(unittest.TestCase):
    def test_fifa_sum_rating_rewards_winner_and_debits_loser(self) -> None:
        ratings = fifa_sum_ratings(
            (
                _match("m1", "2025-01-10T00:00:00Z", "Brazil", "Germany", 2, 0),
            )
        )

        self.assertGreater(ratings["Brazil"], 1500.0)
        self.assertLess(ratings["Germany"], 1500.0)


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
