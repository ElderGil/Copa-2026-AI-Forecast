from __future__ import annotations

import unittest

from copa_forecast.simulation.standings import (
    TeamStanding,
    apply_match_result,
    empty_group_table,
    rank_group,
)


class StandingsTest(unittest.TestCase):
    def test_apply_match_result_updates_both_teams(self) -> None:
        table = empty_group_table("A", ["Mexico", "South Africa"])

        updated = apply_match_result(
            table,
            home_team="Mexico",
            away_team="South Africa",
            home_score=2,
            away_score=1,
        )

        self.assertEqual(updated["Mexico"].points, 3)
        self.assertEqual(updated["Mexico"].goal_difference, 1)
        self.assertEqual(updated["South Africa"].losses, 1)
        self.assertEqual(updated["South Africa"].goals_against, 2)

    def test_rank_group_uses_fair_play_before_stable_name_fallback(self) -> None:
        ranked = rank_group(
            [
                TeamStanding("Beta", points=4, goal_difference=1, goals_for=3, fair_play_points=8),
                TeamStanding("Alpha", points=4, goal_difference=1, goals_for=3, fair_play_points=2),
            ]
        )

        self.assertEqual(ranked[0].team, "Alpha")


if __name__ == "__main__":
    unittest.main()
