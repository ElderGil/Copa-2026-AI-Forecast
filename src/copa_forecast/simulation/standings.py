from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TeamStanding:
    team: str
    points: int
    goal_difference: int
    goals_for: int
    fair_play_points: int = 0


def rank_group(standings: list[TeamStanding]) -> list[TeamStanding]:
    """Rank teams using core FIFA-like criteria available in the MVP."""

    return sorted(
        standings,
        key=lambda row: (
            row.points,
            row.goal_difference,
            row.goals_for,
            -row.fair_play_points,
            row.team,
        ),
        reverse=True,
    )

