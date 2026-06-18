from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TeamExplanation:
    team: str
    used_pillars: tuple[str, ...]
    excluded_pillars: tuple[str, ...]
    summary: str


def build_team_explanation(
    *, team: str, used_pillars: list[str], excluded_pillars: list[str]
) -> TeamExplanation:
    summary = (
        f"{team}: {len(used_pillars)} pilares usados; "
        f"{len(excluded_pillars)} pilares excluidos por cobertura ou ausencia."
    )
    return TeamExplanation(
        team=team,
        used_pillars=tuple(used_pillars),
        excluded_pillars=tuple(excluded_pillars),
        summary=summary,
    )

