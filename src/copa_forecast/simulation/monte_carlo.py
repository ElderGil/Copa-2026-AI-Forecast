from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from itertools import combinations

from copa_forecast.data.contracts import (
    COMPLETED_STATUSES,
    Fixture,
    OfficialCompetitionState,
)
from copa_forecast.features.leakage import parse_record_date
from copa_forecast.models.baselines import NEUTRAL_STRENGTH, three_way_baseline
from copa_forecast.simulation.rules import (
    KnockoutMatch,
    build_world_cup_2026_round_of_32_matches,
    is_world_cup_2026_group_structure,
    round_of_32_qualifiers,
)
from copa_forecast.simulation.standings import (
    TeamStanding,
    apply_match_result,
    empty_group_table,
    rank_group,
)

ADVANCEMENT_ROUNDS = (
    "round_of_32",
    "round_of_16",
    "quarterfinal",
    "semifinal",
    "final",
    "champion",
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


@dataclass(frozen=True)
class SimulatedKnockoutResult:
    match_number: int
    round_name: str
    home_team: str
    away_team: str
    winner: str
    decided_by: str


@dataclass(frozen=True)
class TournamentRunResult:
    champion: str
    group_tables: dict[str, list[TeamStanding]]
    advancement: dict[str, tuple[str, ...]]
    knockout_results: tuple[SimulatedKnockoutResult, ...]


def simulate_tournament_distribution(
    state: OfficialCompetitionState,
    *,
    strengths: dict[str, float],
    runs: int,
    seed: int,
    as_of_date: date,
    temperature: float = 1.0,
) -> dict[str, dict[str, float]]:
    if runs <= 0:
        raise ValueError("runs must be positive.")
    # Temperature scaling reduces to rescaling the rating spread: because the
    # match model divides the rating gap by T, shrinking each strength toward a
    # common center by 1/T reproduces temperature exactly (the center cancels in
    # the difference), with no plumbing through the bracket helpers.
    strengths = _temperature_scaled_strengths(strengths, temperature)
    rng = random.Random(seed)
    team_names = [team.name for team in state.teams]
    counts: dict[str, Counter[str]] = {
        team: Counter({round_name: 0 for round_name in ADVANCEMENT_ROUNDS})
        for team in team_names
    }
    for _ in range(runs):
        result = simulate_tournament_once(
            state, strengths=strengths, rng=rng, as_of_date=as_of_date
        )
        for round_name, teams in result.advancement.items():
            for team in teams:
                counts.setdefault(team, Counter())[round_name] += 1
    return {
        team: {
            round_name: counts.get(team, Counter()).get(round_name, 0) / runs
            for round_name in ADVANCEMENT_ROUNDS
        }
        for team in team_names
    }


def simulate_tournament_once(
    state: OfficialCompetitionState,
    *,
    strengths: dict[str, float],
    rng: random.Random,
    as_of_date: date,
) -> TournamentRunResult:
    group_tables = simulate_group_tables(
        state, strengths=strengths, rng=rng, as_of_date=as_of_date
    )
    initial_matches = build_initial_knockout_matches(group_tables)
    r32_teams = tuple(
        team for match in initial_matches for team in (match.home_team, match.away_team)
    )
    advancement: dict[str, tuple[str, ...]] = {"round_of_32": tuple(sorted(set(r32_teams)))}
    knockout_results: list[SimulatedKnockoutResult] = []

    if is_world_cup_2026_group_structure(group_tables):
        resolved: dict[int, str] = {}
        _play_match_list(
            initial_matches,
            round_name="round_of_32",
            strengths=strengths,
            rng=rng,
            resolved=resolved,
            knockout_results=knockout_results,
        )
        advancement["round_of_16"] = _winners_for_matches(resolved, range(73, 89))
        _play_official_round(
            ROUND_OF_16_SPECS,
            round_name="round_of_16",
            strengths=strengths,
            rng=rng,
            resolved=resolved,
            knockout_results=knockout_results,
        )
        advancement["quarterfinal"] = _winners_for_matches(resolved, range(89, 97))
        _play_official_round(
            QUARTERFINAL_SPECS,
            round_name="quarterfinal",
            strengths=strengths,
            rng=rng,
            resolved=resolved,
            knockout_results=knockout_results,
        )
        advancement["semifinal"] = _winners_for_matches(resolved, range(97, 101))
        _play_official_round(
            SEMIFINAL_SPECS,
            round_name="semifinal",
            strengths=strengths,
            rng=rng,
            resolved=resolved,
            knockout_results=knockout_results,
        )
        advancement["final"] = _winners_for_matches(resolved, range(101, 103))
        _play_official_round(
            (FINAL_SPEC,),
            round_name="final",
            strengths=strengths,
            rng=rng,
            resolved=resolved,
            knockout_results=knockout_results,
        )
        champion = resolved[104]
    else:
        champion = _play_generic_knockout(
            initial_matches,
            strengths=strengths,
            rng=rng,
            advancement=advancement,
            knockout_results=knockout_results,
        )

    advancement["champion"] = (champion,)
    return TournamentRunResult(
        champion=champion,
        group_tables=group_tables,
        advancement=advancement,
        knockout_results=tuple(knockout_results),
    )


def simulate_group_tables(
    state: OfficialCompetitionState,
    *,
    strengths: dict[str, float],
    rng: random.Random,
    as_of_date: date,
) -> dict[str, list[TeamStanding]]:
    groups = _groups_from_state(state)
    fixture_pairs = _fixtures_by_group(state, groups)
    tables: dict[str, list[TeamStanding]] = {}
    for group, teams in groups.items():
        table = empty_group_table(group, teams)
        results: list[tuple[str, str, int, int]] = []
        for fixture in fixture_pairs[group]:
            home_score, away_score = _resolve_group_fixture(
                fixture,
                strengths=strengths,
                rng=rng,
                as_of_date=as_of_date,
            )
            results.append(
                (fixture.home_team, fixture.away_team, home_score, away_score)
            )
            table = apply_match_result(
                table,
                home_team=fixture.home_team,
                away_team=fixture.away_team,
                home_score=home_score,
                away_score=away_score,
            )
        tables[group] = rank_group(list(table.values()), head_to_head_matches=results)
    return tables


def build_initial_knockout_matches(
    group_tables: dict[str, list[TeamStanding]]
) -> list[KnockoutMatch]:
    if is_world_cup_2026_group_structure(group_tables):
        return build_world_cup_2026_round_of_32_matches(group_tables)

    qualifiers = round_of_32_qualifiers(group_tables)
    if len(qualifiers) % 2 != 0:
        qualifiers = qualifiers[:-1]
    return [
        KnockoutMatch(
            match_number=index,
            home_team=qualifiers[index],
            away_team=qualifiers[-index - 1],
            home_source="seed",
            away_source="seed",
        )
        for index in range(len(qualifiers) // 2)
    ]


def _play_match_list(
    matches: list[KnockoutMatch],
    *,
    round_name: str,
    strengths: dict[str, float],
    rng: random.Random,
    resolved: dict[int, str],
    knockout_results: list[SimulatedKnockoutResult],
) -> None:
    for match in matches:
        winner, decided_by = _knockout_winner(
            match.home_team, match.away_team, strengths=strengths, rng=rng
        )
        resolved[match.match_number] = winner
        knockout_results.append(
            SimulatedKnockoutResult(
                match.match_number,
                round_name,
                match.home_team,
                match.away_team,
                winner,
                decided_by,
            )
        )


def _play_official_round(
    specs: tuple[tuple[int, int, int], ...],
    *,
    round_name: str,
    strengths: dict[str, float],
    rng: random.Random,
    resolved: dict[int, str],
    knockout_results: list[SimulatedKnockoutResult],
) -> None:
    matches = [
        KnockoutMatch(
            match_number,
            resolved[left_match],
            resolved[right_match],
            f"W{left_match}",
            f"W{right_match}",
        )
        for match_number, left_match, right_match in specs
    ]
    _play_match_list(
        matches,
        round_name=round_name,
        strengths=strengths,
        rng=rng,
        resolved=resolved,
        knockout_results=knockout_results,
    )


def _play_generic_knockout(
    matches: list[KnockoutMatch],
    *,
    strengths: dict[str, float],
    rng: random.Random,
    advancement: dict[str, tuple[str, ...]],
    knockout_results: list[SimulatedKnockoutResult],
) -> str:
    current = list(matches)
    round_names = ["round_of_32", "round_of_16", "quarterfinal", "semifinal", "final"]
    round_index = max(0, len(round_names) - _knockout_rounds_remaining(len(current) * 2))
    while current:
        resolved: dict[int, str] = {}
        round_name = round_names[min(round_index, len(round_names) - 1)]
        _play_match_list(
            current,
            round_name=round_name,
            strengths=strengths,
            rng=rng,
            resolved=resolved,
            knockout_results=knockout_results,
        )
        winners = [resolved[match.match_number] for match in current]
        if len(winners) == 1:
            return winners[0]
        next_round = _next_round_name(len(winners))
        advancement[next_round] = tuple(sorted(winners))
        current = [
            KnockoutMatch(index, winners[index], winners[-index - 1], "seed", "seed")
            for index in range(len(winners) // 2)
        ]
        round_index += 1
    raise ValueError("No knockout matches could be simulated.")


def _resolve_group_fixture(
    fixture: Fixture,
    *,
    strengths: dict[str, float],
    rng: random.Random,
    as_of_date: date,
) -> tuple[int, int]:
    if _has_known_result_before_cutoff(fixture, as_of_date=as_of_date):
        return fixture.home_score or 0, fixture.away_score or 0
    outcome = _sample_three_way(fixture.home_team, fixture.away_team, strengths, rng)
    if outcome == "draw":
        score = rng.randint(0, 2)
        return score, score
    winner_goals = rng.randint(1, 4)
    loser_goals = rng.randint(0, max(0, winner_goals - 1))
    if outcome == "home":
        return winner_goals, loser_goals
    return loser_goals, winner_goals


def _knockout_winner(
    home_team: str, away_team: str, *, strengths: dict[str, float], rng: random.Random
) -> tuple[str, str]:
    outcome = _sample_three_way(home_team, away_team, strengths, rng)
    if outcome == "home":
        return home_team, "regulation"
    if outcome == "away":
        return away_team, "regulation"
    home_strength = max(strengths.get(home_team, NEUTRAL_STRENGTH), 1.0)
    away_strength = max(strengths.get(away_team, NEUTRAL_STRENGTH), 1.0)
    home_probability = home_strength / (home_strength + away_strength)
    return (home_team if rng.random() < home_probability else away_team), "extra_time_or_penalties"


def _temperature_scaled_strengths(
    strengths: dict[str, float], temperature: float, *, center: float = NEUTRAL_STRENGTH
) -> dict[str, float]:
    if temperature in (None, 1.0) or temperature <= 0:
        return strengths
    return {
        team: center + (value - center) / temperature
        for team, value in strengths.items()
    }


def _sample_three_way(
    home_team: str, away_team: str, strengths: dict[str, float], rng: random.Random
) -> str:
    probs = three_way_baseline(
        strengths.get(home_team, NEUTRAL_STRENGTH),
        strengths.get(away_team, NEUTRAL_STRENGTH),
    )
    pick = rng.random()
    if pick < probs["win"]:
        return "home"
    if pick < probs["win"] + probs["draw"]:
        return "draw"
    return "away"


def _groups_from_state(state: OfficialCompetitionState) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    team_group = {team.name: team.group for team in state.teams if team.group}
    for team in state.teams:
        if team.group:
            groups[team.group].append(team.name)
    for fixture in state.fixtures:
        group = fixture.group or team_group.get(fixture.home_team)
        if not group:
            continue
        for team in (fixture.home_team, fixture.away_team):
            if team not in groups[group]:
                groups[group].append(team)
    return dict(sorted(groups.items()))


def _fixtures_by_group(
    state: OfficialCompetitionState, groups: dict[str, list[str]]
) -> dict[str, list[Fixture]]:
    fixtures: dict[str, list[Fixture]] = {group: [] for group in groups}
    seen: dict[str, set[frozenset[str]]] = {group: set() for group in groups}
    team_group = {
        team_name: group
        for group, team_names in groups.items()
        for team_name in team_names
    }
    for fixture in state.fixtures:
        group = fixture.group or team_group.get(fixture.home_team)
        if not group or group not in fixtures:
            continue
        pair = frozenset((fixture.home_team, fixture.away_team))
        if pair in seen[group]:
            continue
        seen[group].add(pair)
        fixtures[group].append(fixture)

    for group, team_names in groups.items():
        for home_team, away_team in combinations(team_names, 2):
            pair = frozenset((home_team, away_team))
            if pair in seen[group]:
                continue
            fixtures[group].append(
                Fixture(
                    match_id=f"generated-{group}-{home_team}-{away_team}",
                    home_team=home_team,
                    away_team=away_team,
                    group=group,
                    kickoff=None,
                    venue=None,
                    status="scheduled",
                )
            )
            seen[group].add(pair)
    return fixtures


def _has_known_result_before_cutoff(fixture: Fixture, *, as_of_date: date) -> bool:
    if fixture.status.casefold() not in COMPLETED_STATUSES:
        return False
    if fixture.home_score is None or fixture.away_score is None:
        return False
    if not fixture.kickoff:
        return True
    return parse_record_date(fixture.kickoff) < as_of_date


def _winners_for_matches(resolved: dict[int, str], match_numbers: range) -> tuple[str, ...]:
    return tuple(sorted(resolved[number] for number in match_numbers))


def _next_round_name(team_count: int) -> str:
    if team_count >= 16:
        return "round_of_16"
    if team_count >= 8:
        return "quarterfinal"
    if team_count >= 4:
        return "semifinal"
    if team_count >= 2:
        return "final"
    return "champion"


def _knockout_rounds_remaining(team_count: int) -> int:
    rounds = 0
    current = team_count
    while current > 1:
        current //= 2
        rounds += 1
    return rounds
