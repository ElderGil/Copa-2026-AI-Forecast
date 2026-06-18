from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidencePillar:
    name: str
    available_teams: int
    total_teams: int
    source: str

    @property
    def coverage(self) -> float:
        if self.total_teams <= 0:
            return 0.0
        return self.available_teams / self.total_teams


def is_public_model_pillar(
    pillar: EvidencePillar, *, minimum_coverage: float = 0.80
) -> bool:
    """Return True when a pillar has enough team coverage for public modeling."""

    return pillar.coverage >= minimum_coverage


def split_pillars_by_coverage(
    pillars: list[EvidencePillar], *, minimum_coverage: float = 0.80
) -> tuple[list[EvidencePillar], list[EvidencePillar]]:
    included: list[EvidencePillar] = []
    excluded: list[EvidencePillar] = []
    for pillar in pillars:
        if is_public_model_pillar(pillar, minimum_coverage=minimum_coverage):
            included.append(pillar)
        else:
            excluded.append(pillar)
    return included, excluded

