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


def rank_group(
    standings: list[TeamStanding],
    *,
    head_to_head_matches: list[tuple[str, str, int, int]] | None = None,
) -> list[TeamStanding]:
    """Rank teams using core FIFA-like criteria.

    Order: points, goal difference, goals for. When ``head_to_head_matches`` is
    provided (a group's ``(home, away, home_score, away_score)`` results), teams
    still tied on those three are separated by their mutual results (points, then
    goal difference, then goals scored among the tied set) before the
    fair-play / name fallbacks. Fair-play points and drawing of lots are not
    modeled.
    """

    if not head_to_head_matches:
        return sorted(standings, key=_overall_sort_key)

    primary = sorted(standings, key=_overall_sort_key)
    ordered: list[TeamStanding] = []
    index = 0
    while index < len(primary):
        end = index
        tie_key = _tie_key(primary[index])
        while end < len(primary) and _tie_key(primary[end]) == tie_key:
            end += 1
        run = primary[index:end]
        if len(run) > 1:
            ordered.extend(_order_by_head_to_head(run, head_to_head_matches))
        else:
            ordered.extend(run)
        index = end
    return ordered


def _overall_sort_key(row: TeamStanding) -> tuple:
    return (
        -row.points,
        -row.goal_difference,
        -row.goals_for,
        row.fair_play_points,
        row.team.casefold(),
    )


def _tie_key(row: TeamStanding) -> tuple[int, int, int]:
    return (row.points, row.goal_difference, row.goals_for)


def _order_by_head_to_head(
    tied: list[TeamStanding], matches: list[tuple[str, str, int, int]]
) -> list[TeamStanding]:
    names = {row.team for row in tied}
    mini: dict[str, list[int]] = {name: [0, 0, 0] for name in names}
    for home, away, home_score, away_score in matches:
        if home not in names or away not in names:
            continue
        home_points, away_points = points_for_result(home_score, away_score)
        mini[home][0] += home_points
        mini[home][1] += home_score - away_score
        mini[home][2] += home_score
        mini[away][0] += away_points
        mini[away][1] += away_score - home_score
        mini[away][2] += away_score
    return sorted(
        tied,
        key=lambda row: (
            -mini[row.team][0],
            -mini[row.team][1],
            -mini[row.team][2],
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
