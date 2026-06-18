from __future__ import annotations

from copa_forecast.simulation.standings import TeamStanding, rank_group


def automatic_qualifiers(group_tables: dict[str, list[TeamStanding]]) -> list[str]:
    qualifiers: list[str] = []
    for standings in group_tables.values():
        qualifiers.extend(row.team for row in rank_group(standings)[:2])
    return qualifiers


def best_third_placed_teams(
    group_tables: dict[str, list[TeamStanding]], *, slots: int = 8
) -> list[str]:
    third_rows = [rank_group(standings)[2] for standings in group_tables.values()]
    ranked_thirds = rank_group(third_rows)
    return [row.team for row in ranked_thirds[:slots]]


def round_of_32_qualifiers(group_tables: dict[str, list[TeamStanding]]) -> list[str]:
    return automatic_qualifiers(group_tables) + best_third_placed_teams(group_tables)

