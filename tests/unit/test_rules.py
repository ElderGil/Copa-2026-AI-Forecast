from __future__ import annotations

import unittest

from copa_forecast.simulation.rules import (
    GROUP_ORDER,
    assign_third_place_slots,
    best_third_placed_teams,
    build_world_cup_2026_round_of_32_matches,
    is_world_cup_2026_group_structure,
)
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

    def test_world_cup_2026_group_structure_requires_twelve_groups_of_four(self) -> None:
        tables = _world_cup_2026_tables()

        self.assertTrue(is_world_cup_2026_group_structure(tables))

    def test_builds_sixteen_round_of_32_matches(self) -> None:
        matches = build_world_cup_2026_round_of_32_matches(_world_cup_2026_tables())

        self.assertEqual(len(matches), 16)
        self.assertEqual(matches[0].home_source, "2A")
        self.assertEqual(matches[0].away_source, "2B")
        self.assertTrue(any(match.away_source.startswith("3") for match in matches))

    def test_assigns_third_place_groups_only_to_allowed_slots(self) -> None:
        assignments = assign_third_place_slots(("C", "D", "E", "F", "G", "H", "I", "J"))

        self.assertEqual(len(assignments), 8)
        self.assertEqual(sorted(assignments.values()), ["C", "D", "E", "F", "G", "H", "I", "J"])


def _world_cup_2026_tables() -> dict[str, list[TeamStanding]]:
    tables: dict[str, list[TeamStanding]] = {}
    for group_index, group in enumerate(GROUP_ORDER):
        tables[group] = [
            TeamStanding(f"{group}1", points=9, goal_difference=6, goals_for=8, group=group),
            TeamStanding(f"{group}2", points=6, goal_difference=2, goals_for=5, group=group),
            TeamStanding(
                f"{group}3",
                points=group_index,
                goal_difference=group_index,
                goals_for=group_index,
                group=group,
            ),
            TeamStanding(f"{group}4", points=0, goal_difference=-6, goals_for=1, group=group),
        ]
    return tables


if __name__ == "__main__":
    unittest.main()
