from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TeamStanding:
    team: str
    points: int = 0
    goal_difference: int = 0
    goals_for: int = 0
    fair_play_points: int = 0
    group: str | None = None
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_against: int = 0


def rank_group(standings: list[TeamStanding]) -> list[TeamStanding]:
    """Rank teams using core FIFA-like criteria available in the MVP."""

    return sorted(
        standings,
        key=lambda row: (
            -row.points,
            -row.goal_difference,
            -row.goals_for,
            row.fair_play_points,
            row.team.casefold(),
        ),
    )


def empty_group_table(group: str, teams: list[str]) -> dict[str, TeamStanding]:
    return {team: TeamStanding(team=team, group=group) for team in teams}


def apply_match_result(
    table: dict[str, TeamStanding],
    *,
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
) -> dict[str, TeamStanding]:
    if home_team not in table or away_team not in table:
        raise ValueError("Both match teams must exist in the group table.")

    home_points, away_points = points_for_result(home_score, away_score)
    updated = dict(table)
    updated[home_team] = _add_result(
        table[home_team],
        points=home_points,
        goals_for=home_score,
        goals_against=away_score,
    )
    updated[away_team] = _add_result(
        table[away_team],
        points=away_points,
        goals_for=away_score,
        goals_against=home_score,
    )
    return updated


def points_for_result(home_score: int, away_score: int) -> tuple[int, int]:
    if home_score > away_score:
        return 3, 0
    if home_score < away_score:
        return 0, 3
    return 1, 1


def _add_result(
    row: TeamStanding, *, points: int, goals_for: int, goals_against: int
) -> TeamStanding:
    return TeamStanding(
        team=row.team,
        points=row.points + points,
        goal_difference=row.goal_difference + goals_for - goals_against,
        goals_for=row.goals_for + goals_for,
        fair_play_points=row.fair_play_points,
        group=row.group,
        played=row.played + 1,
        wins=row.wins + (1 if points == 3 else 0),
        draws=row.draws + (1 if points == 1 else 0),
        losses=row.losses + (1 if points == 0 else 0),
        goals_against=row.goals_against + goals_against,
    )
