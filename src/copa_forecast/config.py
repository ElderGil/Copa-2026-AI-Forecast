from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when a forecast config is incomplete or inconsistent."""


@dataclass(frozen=True)
class FifaSourceConfig:
    source_id: str
    url: str
    purpose: str


@dataclass(frozen=True)
class OfficialFifaConfig:
    sources: tuple[FifaSourceConfig, ...]
    raw_output_dir: Path
    allow_cached_payloads: bool
    degraded_mode_allowed: bool


@dataclass(frozen=True)
class RecentMatchSourceConfig:
    source_id: str
    authority: str
    url_template: str


@dataclass(frozen=True)
class RecentMatchesConfig:
    sources: tuple[RecentMatchSourceConfig, ...]
    raw_output_dir: Path
    processed_output_dir: Path
    declared: bool


@dataclass(frozen=True)
class FeatureWindowConfig:
    current_months: int
    max_months: int
    decay_half_life_days: int


@dataclass(frozen=True)
class SimulationConfig:
    tournament_ruleset: str
    runs: int
    random_seed: int


@dataclass(frozen=True)
class SiteConfig:
    language: str
    output_dir: Path
    top_count: int


@dataclass(frozen=True)
class ForecastConfig:
    run_id: str
    as_of_date: date
    project_github_url: str
    official_fifa: OfficialFifaConfig
    recent_matches: RecentMatchesConfig
    feature_windows: FeatureWindowConfig
    simulation: SimulationConfig
    site: SiteConfig


def load_config(path: str | Path) -> ForecastConfig:
    """Load a JSON config file for the forecast pipeline."""

    config_path = Path(path)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    return parse_config(payload)


def parse_config(payload: dict[str, Any]) -> ForecastConfig:
    required = {
        "run_id",
        "as_of_date",
        "project_github_url",
        "official_fifa",
        "feature_windows",
        "simulation",
        "site",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise ConfigError(f"Missing required config keys: {', '.join(missing)}")

    if not payload["project_github_url"].startswith(("https://", "http://")):
        raise ConfigError("project_github_url must be an absolute URL.")

    official = payload["official_fifa"]
    sources = tuple(
        FifaSourceConfig(
            source_id=str(item["source_id"]),
            url=str(item["url"]),
            purpose=str(item["purpose"]),
        )
        for item in official.get("sources", [])
    )
    if not sources:
        raise ConfigError("At least one official FIFA source is required.")

    windows = payload["feature_windows"]
    current_months = int(windows.get("current_months", 12))
    max_months = int(windows.get("max_months", 24))
    if current_months > max_months:
        raise ConfigError("current_months must be less than or equal to max_months.")

    simulation = payload["simulation"]
    site = payload["site"]

    return ForecastConfig(
        run_id=str(payload["run_id"]),
        as_of_date=date.fromisoformat(str(payload["as_of_date"])),
        project_github_url=str(payload["project_github_url"]),
        official_fifa=OfficialFifaConfig(
            sources=sources,
            raw_output_dir=Path(str(official["raw_output_dir"])),
            allow_cached_payloads=bool(official.get("allow_cached_payloads", True)),
            degraded_mode_allowed=bool(official.get("degraded_mode_allowed", False)),
        ),
        recent_matches=_parse_recent_matches(
            payload.get("recent_matches", {}), declared="recent_matches" in payload
        ),
        feature_windows=FeatureWindowConfig(
            current_months=current_months,
            max_months=max_months,
            decay_half_life_days=int(windows.get("decay_half_life_days", 180)),
        ),
        simulation=SimulationConfig(
            tournament_ruleset=str(simulation["tournament_ruleset"]),
            runs=int(simulation.get("runs", 10_000)),
            random_seed=int(simulation.get("random_seed", 20260618)),
        ),
        site=SiteConfig(
            language=str(site.get("language", "pt-BR")),
            output_dir=Path(str(site.get("output_dir", "public"))),
            top_count=int(site.get("top_count", 10)),
        ),
    )


def _parse_recent_matches(payload: dict[str, Any], *, declared: bool) -> RecentMatchesConfig:
    default_template = (
        "https://api.fifa.com/api/v3/calendar/matches?"
        "language=en&count=200&idTeam={team_id}&from={from_date}&to={to_date}"
    )
    sources = tuple(
        RecentMatchSourceConfig(
            source_id=str(item["source_id"]),
            authority=str(item.get("authority", "fifa")),
            url_template=str(item.get("url_template", default_template)),
        )
        for item in payload.get(
            "sources",
            [
                {
                    "source_id": "fifa-calendar-team-matches",
                    "authority": "fifa",
                    "url_template": default_template,
                }
            ],
        )
    )
    return RecentMatchesConfig(
        sources=sources,
        raw_output_dir=Path(str(payload.get("raw_output_dir", "data/raw/fifa_recent_matches"))),
        processed_output_dir=Path(
            str(payload.get("processed_output_dir", "data/processed/recent_matches"))
        ),
        declared=declared,
    )
