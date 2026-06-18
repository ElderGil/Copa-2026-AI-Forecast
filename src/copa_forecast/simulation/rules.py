from __future__ import annotations

from dataclasses import dataclass

from copa_forecast.simulation.standings import TeamStanding, rank_group

GROUP_ORDER = tuple("ABCDEFGHIJKL")
WORLD_CUP_2026_GROUP_COUNT = 12
WORLD_CUP_2026_TEAMS_PER_GROUP = 4
ROUND_OF_32_SIZE = 32


@dataclass(frozen=True)
class KnockoutMatch:
    match_number: int
    home_team: str
    away_team: str
    home_source: str
    away_source: str


@dataclass(frozen=True)
class ThirdPlaceSlot:
    match_number: int
    winner_group: str
    allowed_groups: tuple[str, ...]


ROUND_OF_32_THIRD_PLACE_SLOTS = (
    ThirdPlaceSlot(74, "E", ("A", "B", "C", "D", "F")),
    ThirdPlaceSlot(77, "I", ("C", "D", "F", "G", "H")),
    ThirdPlaceSlot(79, "A", ("C", "E", "F", "H", "I")),
    ThirdPlaceSlot(80, "L", ("E", "H", "I", "J", "K")),
    ThirdPlaceSlot(81, "D", ("B", "E", "F", "I", "J")),
    ThirdPlaceSlot(82, "G", ("A", "E", "H", "I", "J")),
    ThirdPlaceSlot(85, "B", ("E", "F", "G", "I", "J")),
    ThirdPlaceSlot(87, "K", ("D", "E", "I", "J", "L")),
)


def automatic_qualifiers(group_tables: dict[str, list[TeamStanding]]) -> list[str]:
    qualifiers: list[str] = []
    for group in _ordered_groups(group_tables):
        standings = group_tables[group]
        qualifiers.extend(row.team for row in rank_group(standings)[:2])
    return qualifiers


def best_third_placed_teams(
    group_tables: dict[str, list[TeamStanding]], *, slots: int = 8
) -> list[str]:
    third_rows = [
        _with_group(rank_group(group_tables[group])[2], group)
        for group in _ordered_groups(group_tables)
        if len(group_tables[group]) >= 3
    ]
    ranked_thirds = rank_group(third_rows)
    return [row.team for row in ranked_thirds[:slots]]


def round_of_32_qualifiers(group_tables: dict[str, list[TeamStanding]]) -> list[str]:
    return automatic_qualifiers(group_tables) + best_third_placed_teams(group_tables)


def is_world_cup_2026_group_structure(
    group_tables: dict[str, list[TeamStanding]],
) -> bool:
    if len(group_tables) != WORLD_CUP_2026_GROUP_COUNT:
        return False
    return all(
        group in group_tables and len(group_tables[group]) == WORLD_CUP_2026_TEAMS_PER_GROUP
        for group in GROUP_ORDER
    )


def build_world_cup_2026_round_of_32_matches(
    group_tables: dict[str, list[TeamStanding]]
) -> list[KnockoutMatch]:
    if not is_world_cup_2026_group_structure(group_tables):
        raise ValueError("World Cup 2026 simulation requires 12 groups of 4 teams.")

    ranked = {group: rank_group(group_tables[group]) for group in GROUP_ORDER}
    winners = {group: rows[0].team for group, rows in ranked.items()}
    runners_up = {group: rows[1].team for group, rows in ranked.items()}
    third_rows = {
        group: _with_group(rows[2], group)
        for group, rows in ranked.items()
    }
    qualified_third_groups = tuple(
        row.group or ""
        for row in rank_group(list(third_rows.values()))[:8]
    )
    third_assignments = assign_third_place_slots(qualified_third_groups)

    return [
        KnockoutMatch(73, runners_up["A"], runners_up["B"], "2A", "2B"),
        _third_place_match(74, winners["E"], "1E", third_rows, third_assignments),
        KnockoutMatch(75, winners["F"], runners_up["C"], "1F", "2C"),
        KnockoutMatch(76, winners["C"], runners_up["F"], "1C", "2F"),
        _third_place_match(77, winners["I"], "1I", third_rows, third_assignments),
        KnockoutMatch(78, runners_up["E"], runners_up["I"], "2E", "2I"),
        _third_place_match(79, winners["A"], "1A", third_rows, third_assignments),
        _third_place_match(80, winners["L"], "1L", third_rows, third_assignments),
        _third_place_match(81, winners["D"], "1D", third_rows, third_assignments),
        _third_place_match(82, winners["G"], "1G", third_rows, third_assignments),
        KnockoutMatch(83, runners_up["K"], runners_up["L"], "2K", "2L"),
        KnockoutMatch(84, winners["H"], runners_up["J"], "1H", "2J"),
        _third_place_match(85, winners["B"], "1B", third_rows, third_assignments),
        KnockoutMatch(86, winners["J"], runners_up["H"], "1J", "2H"),
        _third_place_match(87, winners["K"], "1K", third_rows, third_assignments),
        KnockoutMatch(88, runners_up["D"], runners_up["G"], "2D", "2G"),
    ]


def assign_third_place_slots(qualified_groups: tuple[str, ...]) -> dict[int, str]:
    remaining = tuple(sorted(set(qualified_groups)))
    if len(remaining) != 8:
        raise ValueError("Exactly eight third-place groups must qualify.")

    assignments: dict[int, str] = {}
    slots = sorted(
        ROUND_OF_32_THIRD_PLACE_SLOTS,
        key=lambda slot: (len(set(slot.allowed_groups) & set(remaining)), slot.match_number),
    )

    def search(index: int, available: tuple[str, ...]) -> bool:
        if index == len(slots):
            return True
        slot = slots[index]
        for group in available:
            if group not in slot.allowed_groups:
                continue
            assignments[slot.match_number] = group
            next_available = tuple(item for item in available if item != group)
            if search(index + 1, next_available):
                return True
            del assignments[slot.match_number]
        return False

    if not search(0, remaining):
        groups = ", ".join(remaining)
        raise ValueError(f"No valid third-place slot assignment for groups: {groups}.")
    return dict(sorted(assignments.items()))


def _third_place_match(
    match_number: int,
    winner_team: str,
    winner_source: str,
    third_rows: dict[str, TeamStanding],
    third_assignments: dict[int, str],
) -> KnockoutMatch:
    group = third_assignments[match_number]
    return KnockoutMatch(
        match_number,
        winner_team,
        third_rows[group].team,
        winner_source,
        f"3{group}",
    )


def _with_group(row: TeamStanding, group: str) -> TeamStanding:
    if row.group == group:
        return row
    return TeamStanding(
        team=row.team,
        points=row.points,
        goal_difference=row.goal_difference,
        goals_for=row.goals_for,
        fair_play_points=row.fair_play_points,
        group=group,
        played=row.played,
        wins=row.wins,
        draws=row.draws,
        losses=row.losses,
        goals_against=row.goals_against,
    )


def _ordered_groups(group_tables: dict[str, list[TeamStanding]]) -> list[str]:
    ordered = [group for group in GROUP_ORDER if group in group_tables]
    extras = sorted(group for group in group_tables if group not in GROUP_ORDER)
    return ordered + extras
