"""Shared helpers for reasoning about the *actual* knockout state.

These functions read completed knockout fixtures from the official competition
state so the simulation can honour results that already happened (eliminated
teams must drop to a 0% title chance) and so the public page can render the
real bracket. They deliberately do **not** touch the statistical match model —
they only answer "which team actually advanced".
"""

from __future__ import annotations

from datetime import date

from copa_forecast.data.contracts import (
    COMPLETED_STATUSES,
    Fixture,
    OfficialCompetitionState,
)
from copa_forecast.features.leakage import parse_record_date


def team_group_map(state: OfficialCompetitionState) -> dict[str, str]:
    return {team.name: team.group for team in state.teams if team.group}


def fixture_group(fixture: Fixture, team_group: dict[str, str]) -> str | None:
    """Return the group a fixture belongs to, or ``None`` for a knockout match.

    Mirrors the group-detection used by the Monte Carlo group simulation: a
    fixture is a group match when it carries a group label or both teams share
    the same group; otherwise it is a knockout (cross-group) match.
    """

    if fixture.group:
        return fixture.group
    home_group = team_group.get(fixture.home_team)
    away_group = team_group.get(fixture.away_team)
    if home_group and home_group == away_group:
        return home_group
    return None


def is_knockout_fixture(fixture: Fixture, team_group: dict[str, str]) -> bool:
    return fixture_group(fixture, team_group) is None


def knockout_match_winner(fixture: Fixture) -> str | None:
    """Winner of a played knockout fixture, honouring penalty shootouts.

    Regulation/extra-time goals decide it; if level, the penalty score breaks
    the tie. Returns ``None`` when the result is not (yet) decisive.
    """

    if fixture.home_score is None or fixture.away_score is None:
        return None
    if fixture.home_score > fixture.away_score:
        return fixture.home_team
    if fixture.away_score > fixture.home_score:
        return fixture.away_team
    home_pens = fixture.home_penalty_score or 0
    away_pens = fixture.away_penalty_score or 0
    if home_pens > away_pens:
        return fixture.home_team
    if away_pens > home_pens:
        return fixture.away_team
    return None


def _is_completed_by_cutoff(fixture: Fixture, *, as_of_date: date) -> bool:
    """Whether a finished knockout result is known as of ``as_of_date``.

    Unlike the feature/group cutoff (strictly before the date, to avoid
    look-ahead leakage when *training* the model), a completed knockout match is
    a settled fact and must be honoured the same day it finishes — including
    matches whose UTC kickoff date equals ``as_of_date`` (e.g. a late shootout
    that ends just after midnight UTC). We therefore include results up to and
    including the cutoff date and only drop fixtures dated strictly after it.
    """

    if fixture.status.casefold() not in COMPLETED_STATUSES:
        return False
    if fixture.home_score is None or fixture.away_score is None:
        return False
    if not fixture.kickoff:
        return True
    return parse_record_date(fixture.kickoff) <= as_of_date


def known_knockout_winners(
    state: OfficialCompetitionState, *, as_of_date: date
) -> dict[frozenset[str], str]:
    """Map ``{home, away}`` team pairs to the team that actually advanced.

    Includes every completed knockout fixture known by ``as_of_date`` (see
    :func:`_is_completed_by_cutoff`); pending and future matches are skipped.
    """

    team_group = team_group_map(state)
    winners: dict[frozenset[str], str] = {}
    for fixture in state.fixtures:
        if not is_knockout_fixture(fixture, team_group):
            continue
        if not _is_completed_by_cutoff(fixture, as_of_date=as_of_date):
            continue
        winner = knockout_match_winner(fixture)
        if winner is None:
            continue
        winners[frozenset((fixture.home_team, fixture.away_team))] = winner
    return winners


ROUND_OF_32_SLOT_RANGE = range(73, 89)


def official_round_of_32(
    state: OfficialCompetitionState,
) -> dict[int, tuple[str, str]]:
    """Real round-of-32 pairings keyed by FIFA match number (73-88).

    Sourced straight from the official fixtures so the simulated and displayed
    brackets match reality exactly — in particular the best-third-placed
    assignments, which FIFA fixes by an official table rather than the
    backtracking the simulator would otherwise derive.
    """

    team_group = team_group_map(state)
    pairings: dict[int, tuple[str, str]] = {}
    for fixture in state.fixtures:
        if fixture.match_number not in ROUND_OF_32_SLOT_RANGE:
            continue
        if not is_knockout_fixture(fixture, team_group):
            continue
        if not fixture.home_team or not fixture.away_team:
            continue
        pairings[fixture.match_number] = (fixture.home_team, fixture.away_team)
    return pairings


def eliminated_knockout_teams(
    state: OfficialCompetitionState, *, as_of_date: date
) -> set[str]:
    """Teams that lost a completed knockout match (and are therefore out)."""

    team_group = team_group_map(state)
    eliminated: set[str] = set()
    for fixture in state.fixtures:
        if not is_knockout_fixture(fixture, team_group):
            continue
        if not _is_completed_by_cutoff(fixture, as_of_date=as_of_date):
            continue
        winner = knockout_match_winner(fixture)
        if winner is None:
            continue
        loser = (
            fixture.away_team if winner == fixture.home_team else fixture.home_team
        )
        eliminated.add(loser)
    return eliminated
