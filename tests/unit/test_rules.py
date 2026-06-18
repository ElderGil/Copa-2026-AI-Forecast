from __future__ import annotations

import unittest

from copa_forecast.simulation.rules import best_third_placed_teams
from copa_forecast.simulation.standings import TeamStanding, rank_group


class TournamentRulesTest(unittest.TestCase):
    def test_group_ranking_uses_points_goal_difference_and_goals(self) -> None:
        ranked = rank_group(
            [
                TeamStanding("A", points=4, goal_difference=1, goals_for=2),
                TeamStanding("B", points=4, goal_difference=2, goals_for=2),
            ]
        )
        self.assertEqual(ranked[0].team, "B")

    def test_best_thirds_returns_eight(self) -> None:
        tables = {
            f"G{i}": [
                TeamStanding(f"{i}A", 6, 3, 5),
                TeamStanding(f"{i}B", 4, 1, 3),
                TeamStanding(f"{i}C", i, i, i),
                TeamStanding(f"{i}D", 0, -4, 1),
            ]
            for i in range(12)
        }
        self.assertEqual(len(best_third_placed_teams(tables)), 8)


if __name__ == "__main__":
    unittest.main()

