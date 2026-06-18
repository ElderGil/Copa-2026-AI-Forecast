from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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

    @property
    def missing_teams(self) -> int:
        return max(self.total_teams - self.available_teams, 0)


@dataclass(frozen=True)
class MissingPillarReport:
    name: str
    source: str
    available_teams: int
    total_teams: int
    missing_teams: int
    coverage: float
    minimum_coverage: float
    status: str
    reason: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source": self.source,
            "available_teams": self.available_teams,
            "total_teams": self.total_teams,
            "missing_teams": self.missing_teams,
            "coverage": self.coverage,
            "minimum_coverage": self.minimum_coverage,
            "status": self.status,
            "reason": self.reason,
        }


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


def describe_pillar_coverage(
    pillar: EvidencePillar, *, minimum_coverage: float = 0.80
) -> MissingPillarReport:
    included = is_public_model_pillar(pillar, minimum_coverage=minimum_coverage)
    status = "used" if included else "excluded_low_coverage"
    if included:
        reason = "coverage_ok"
    elif pillar.missing_teams >= 10:
        reason = "ten_or_more_teams_missing"
    else:
        reason = "below_minimum_coverage"
    return MissingPillarReport(
        name=pillar.name,
        source=pillar.source,
        available_teams=pillar.available_teams,
        total_teams=pillar.total_teams,
        missing_teams=pillar.missing_teams,
        coverage=pillar.coverage,
        minimum_coverage=minimum_coverage,
        status=status,
        reason=reason,
    )


def build_missing_pillar_report(
    pillars: list[EvidencePillar], *, minimum_coverage: float = 0.80
) -> list[MissingPillarReport]:
    return [
        describe_pillar_coverage(pillar, minimum_coverage=minimum_coverage)
        for pillar in pillars
    ]
