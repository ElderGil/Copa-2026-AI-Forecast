"""Deterministic snapshot of the *current* knockout bracket.

This builds the real bracket as it stands right now — concrete teams where the
group stage is finished and results are in, placeholders ("2A", "3º melhor",
"Vencedor J73") everywhere still to be defined. It performs no simulation and
does not touch the statistical model; it only reflects official facts so the
public page can show a live "follow along" bracket.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from copa_forecast.data.contracts import COMPLETED_STATUSES, OfficialCompetitionState
from copa_forecast.features.leakage import parse_record_date
from copa_forecast.simulation.knockout_state import (
    known_knockout_winners,
    official_round_of_32,
    team_group_map,
)
from copa_forecast.simulation.rules import (
    build_world_cup_2026_round_of_32_matches,
    is_world_cup_2026_group_structure,
)
from copa_forecast.simulation.standings import (
    apply_match_result,
    empty_group_table,
    rank_group,
)

GROUPS = "ABCDEFGHIJKL"

# Round of 32 slot template (match_number, home_source, away_source) in the same
# order as ``build_world_cup_2026_round_of_32_matches``. "3X" = an as-yet
# unassigned best-third-placed team.
ROUND_OF_32_TEMPLATE: tuple[tuple[int, str, str], ...] = (
    (73, "2A", "2B"),
    (74, "1E", "3X"),
    (75, "1F", "2C"),
    (76, "1C", "2F"),
    (77, "1I", "3X"),
    (78, "2E", "2I"),
    (79, "1A", "3X"),
    (80, "1L", "3X"),
    (81, "1D", "3X"),
    (82, "1G", "3X"),
    (83, "2K", "2L"),
    (84, "1H", "2J"),
    (85, "1B", "3X"),
    (86, "1J", "2H"),
    (87, "1K", "3X"),
    (88, "2D", "2G"),
)
ROUND_OF_16_SPECS = (
    (89, 73, 75),
    (90, 74, 77),
    (91, 76, 78),
    (92, 79, 80),
    (93, 83, 84),
    (94, 81, 82),
    (95, 86, 88),
    (96, 85, 87),
)
QUARTERFINAL_SPECS = ((97, 89, 90), (98, 93, 94), (99, 91, 92), (100, 95, 96))
SEMIFINAL_SPECS = ((101, 97, 98), (102, 99, 100))
FINAL_SPEC = (104, 101, 102)

ROUND_LABELS = {
    "round_of_32": "16-avos de final",
    "round_of_16": "Oitavas de final",
    "quarterfinal": "Quartas de final",
    "semifinal": "Semifinais",
    "final": "Final",
}


@dataclass(frozen=True)
class BracketSide:
    team: str | None
    placeholder: str


@dataclass(frozen=True)
class BracketMatch:
    match_number: int
    round_key: str
    home: BracketSide
    away: BracketSide
    winner: str | None


def build_bracket_state(
    state: OfficialCompetitionState, *, as_of_date: date
) -> tuple[list[tuple[str, list[BracketMatch]]], bool]:
    """Return ``[(round_key, [BracketMatch, ...]), ...]`` and ``groups_complete``."""

    tables, groups_complete = _actual_group_tables(state, as_of_date=as_of_date)
    known = known_knockout_winners(state, as_of_date=as_of_date)
    official = official_round_of_32(state)

    derived: dict[int, object] = {}
    if groups_complete and is_world_cup_2026_group_structure(tables):
        derived = {
            m.match_number: m for m in build_world_cup_2026_round_of_32_matches(tables)
        }

    teams_by_match: dict[int, tuple[str | None, str | None]] = {}
    placeholders: dict[int, tuple[str, str]] = {}

    # Prefer the official draw, then the derived bracket, then bare placeholders.
    for number, home_source, away_source in ROUND_OF_32_TEMPLATE:
        placeholders[number] = (_slot_label(home_source), _slot_label(away_source))
        if number in official:
            teams_by_match[number] = official[number]
        elif number in derived:
            match = derived[number]
            teams_by_match[number] = (match.home_team, match.away_team)
            placeholders[number] = (
                _slot_label(match.home_source),
                _slot_label(match.away_source),
            )
        else:
            teams_by_match[number] = (None, None)

    winners: dict[int, str | None] = {}
    rounds: list[tuple[str, list[BracketMatch]]] = []

    # Round of 32
    r32_matches: list[BracketMatch] = []
    for number, _h, _a in ROUND_OF_32_TEMPLATE:
        home, away = teams_by_match[number]
        ph_home, ph_away = placeholders[number]
        winner = _decide(home, away, known)
        winners[number] = winner
        r32_matches.append(
            BracketMatch(
                number,
                "round_of_32",
                BracketSide(home, ph_home),
                BracketSide(away, ph_away),
                winner,
            )
        )
    rounds.append(("round_of_32", r32_matches))

    # Later rounds are fed by the winners of previous matches.
    for round_key, specs in (
        ("round_of_16", ROUND_OF_16_SPECS),
        ("quarterfinal", QUARTERFINAL_SPECS),
        ("semifinal", SEMIFINAL_SPECS),
        ("final", (FINAL_SPEC,)),
    ):
        matches: list[BracketMatch] = []
        for number, left, right in specs:
            home = winners.get(left)
            away = winners.get(right)
            winner = _decide(home, away, known)
            winners[number] = winner
            matches.append(
                BracketMatch(
                    number,
                    round_key,
                    BracketSide(home, f"Vencedor J{left}"),
                    BracketSide(away, f"Vencedor J{right}"),
                    winner,
                )
            )
        rounds.append((round_key, matches))

    return rounds, groups_complete


def _decide(
    home: str | None, away: str | None, known: dict[frozenset[str], str]
) -> str | None:
    if not home or not away:
        return None
    return known.get(frozenset((home, away)))


def _actual_group_tables(
    state: OfficialCompetitionState, *, as_of_date: date
) -> tuple[dict[str, list], bool]:
    """Group tables built only from completed group fixtures before the cutoff.

    ``complete`` is True only when every group has played all six matches, so a
    partially-played group never resolves concrete knockout slots.
    """

    team_group = team_group_map(state)
    group_teams: dict[str, list[str]] = {group: [] for group in GROUPS}
    for team in state.teams:
        if team.group in group_teams:
            group_teams[team.group].append(team.name)

    played_counts: dict[str, int] = {group: 0 for group in GROUPS}
    results: dict[str, list[tuple[str, str, int, int]]] = {g: [] for g in GROUPS}
    tables = {
        group: empty_group_table(group, teams)
        for group, teams in group_teams.items()
        if teams
    }

    for fixture in state.fixtures:
        group = team_group.get(fixture.home_team)
        if not group or group != team_group.get(fixture.away_team):
            continue
        if fixture.status.casefold() not in COMPLETED_STATUSES:
            continue
        if fixture.home_score is None or fixture.away_score is None:
            continue
        if fixture.kickoff and parse_record_date(fixture.kickoff) >= as_of_date:
            continue
        if group not in tables:
            continue
        tables[group] = apply_match_result(
            tables[group],
            home_team=fixture.home_team,
            away_team=fixture.away_team,
            home_score=fixture.home_score,
            away_score=fixture.away_score,
        )
        results[group].append(
            (fixture.home_team, fixture.away_team, fixture.home_score, fixture.away_score)
        )
        played_counts[group] += 1

    ranked = {
        group: rank_group(list(table.values()), head_to_head_matches=results[group])
        for group, table in tables.items()
    }
    complete = len(ranked) == len(GROUPS) and all(
        played_counts[group] == 6 for group in GROUPS
    )
    return ranked, complete


def _slot_label(source: str) -> str:
    if source == "3X" or source.startswith("3"):
        if source == "3X":
            return "3º melhor"
        return f"3º Grupo {source[1:]}"
    if source and source[0] in "12" and len(source) >= 2:
        position = "1º" if source[0] == "1" else "2º"
        return f"{position} Grupo {source[1:]}"
    if source.startswith("W"):
        return f"Vencedor J{source[1:]}"
    return source
