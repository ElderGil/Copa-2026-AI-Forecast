from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Canonical set of match/fixture statuses that count as "played" across the
# pipeline. Centralized here so ingestion, forecasting, and simulation agree.
COMPLETED_STATUSES = frozenset(
    {
        "completed",
        "complete",
        "finished",
        "played",
        "full_time",
        "full-time",
        "final",
    }
)


@dataclass(frozen=True)
class FifaExtract:
    extract_id: str
    source_id: str
    source_url: str
    retrieved_at: datetime
    payload_path: Path
    payload_format: str
    checksum: str
    parser_version: str
    status: str = "retrieved"

    def to_json_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["retrieved_at"] = self.retrieved_at.isoformat()
        payload["payload_path"] = str(self.payload_path)
        return payload


@dataclass(frozen=True)
class Team:
    team_id: str
    name: str
    group: str | None = None
    flag_code: str | None = None
    confederation: str | None = None


@dataclass(frozen=True)
class Fixture:
    match_id: str
    home_team: str
    away_team: str
    group: str | None
    kickoff: str | None
    venue: str | None
    status: str
    home_score: int | None = None
    away_score: int | None = None
    fifa_match_id: str | None = None
    home_penalty_score: int | None = None
    away_penalty_score: int | None = None
    match_number: int | None = None


@dataclass(frozen=True)
class OfficialMatchRecord:
    match_id: str
    source_id: str
    source_url: str
    match_date: str
    home_team: str
    away_team: str
    competition: str
    match_importance: str
    venue_context: str
    status: str
    home_score: int | None = None
    away_score: int | None = None
    home_penalty_score: int | None = None
    away_penalty_score: int | None = None
    venue: str | None = None
    fifa_match_id: str | None = None
    home_team_id: str | None = None
    away_team_id: str | None = None

    @property
    def is_played(self) -> bool:
        return self.home_score is not None and self.away_score is not None

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OfficialCompetitionState:
    as_of_date: str
    fifa_extract_ids: tuple[str, ...]
    teams: tuple[Team, ...] = field(default_factory=tuple)
    fixtures: tuple[Fixture, ...] = field(default_factory=tuple)
    degraded: bool = False

    @property
    def is_official(self) -> bool:
        return bool(self.fifa_extract_ids) and not self.degraded
