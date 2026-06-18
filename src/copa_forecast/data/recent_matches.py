from __future__ import annotations

import json
from dataclasses import dataclass, fields
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from copa_forecast.config import ForecastConfig, RecentMatchSourceConfig
from copa_forecast.data.contracts import (
    OfficialCompetitionState,
    OfficialMatchRecord,
    Team,
)
from copa_forecast.data.ingest import persist_raw_extract
from copa_forecast.data.sources.fifa import (
    FifaCalendarMatchParser,
    UrlOrFileFifaCrawler,
)
from copa_forecast.features.leakage import assert_no_future_records, parse_record_date
from copa_forecast.reporting.artifacts import write_excel_safe_csv, write_json
from copa_forecast.timeutils import add_months


@dataclass(frozen=True)
class RecentMatchEtlResult:
    matches: tuple[OfficialMatchRecord, ...]
    coverage: dict[str, Any]
    output_json: Path
    output_csv: Path
    coverage_json: Path


def run_recent_match_etl(
    *,
    config: ForecastConfig,
    state: OfficialCompetitionState,
    retrieved_at: datetime | None = None,
) -> RecentMatchEtlResult:
    retrieved_at = retrieved_at or datetime.now(UTC)
    # Fetch the deep history window so the opponent-adjusted Elo prior reflects
    # multi-year pedigree; recent-form features still filter to max_months.
    from_date = add_months(config.as_of_date, -config.feature_windows.prior_months)
    crawler = UrlOrFileFifaCrawler()
    parser = FifaCalendarMatchParser()
    records: list[OfficialMatchRecord] = []

    for source in config.recent_matches.sources:
        for team in state.teams:
            if not team.team_id:
                continue
            source_url = _source_url(
                source,
                team=team,
                from_date=from_date,
                to_date=config.as_of_date,
            )
            payload = crawler.fetch(source_url)
            extract = persist_raw_extract(
                source_id=f"{source.source_id}-{_safe_id(team.team_id)}",
                source_url=source_url,
                payload=payload,
                output_dir=config.recent_matches.raw_output_dir,
                parser_version=parser.parser_version,
                retrieved_at=retrieved_at,
            )
            records.extend(
                parser.parse_matches(
                    extract.payload_path.read_bytes(),
                    source_id=source.source_id,
                    source_url=source_url,
                )
            )

    matches = tuple(
        _dedupe_matches(
            _date_bound_played_matches(
                records,
                as_of_date=config.as_of_date,
                from_date=from_date,
            )
        )
    )
    # Audited temporal guard: the processed feed must never contain a match dated
    # on or after the run's as_of_date.
    assert_no_future_records(
        [match.to_json_dict() for match in matches],
        date_field="match_date",
        as_of_date=config.as_of_date,
    )
    output_dir = config.recent_matches.processed_output_dir
    output_json = output_dir / "latest_matches.json"
    output_csv = output_dir / "latest_matches.csv"
    coverage_json = output_dir / "coverage.json"
    coverage = build_recent_match_coverage(
        teams=state.teams,
        matches=matches,
        as_of_date=config.as_of_date,
        current_window_months=config.feature_windows.current_months,
        max_window_months=config.feature_windows.max_months,
    )
    write_json(
        output_json,
        {
            "run_id": config.run_id,
            "as_of_date": config.as_of_date.isoformat(),
            "from_date": from_date.isoformat(),
            "source_ids": [source.source_id for source in config.recent_matches.sources],
            "matches": [match.to_json_dict() for match in matches],
        },
    )
    write_recent_matches_csv(output_csv, matches)
    write_json(coverage_json, coverage)
    return RecentMatchEtlResult(
        matches=matches,
        coverage=coverage,
        output_json=output_json,
        output_csv=output_csv,
        coverage_json=coverage_json,
    )


def load_recent_matches(path: str | Path) -> tuple[OfficialMatchRecord, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    allowed = {field.name for field in fields(OfficialMatchRecord)}
    records: list[OfficialMatchRecord] = []
    for item in payload.get("matches", []):
        if not isinstance(item, dict):
            continue
        kwargs = {key: value for key, value in item.items() if key in allowed}
        try:
            records.append(OfficialMatchRecord(**kwargs))
        except TypeError:
            # Skip records missing required fields rather than failing the run.
            continue
    return tuple(records)


def build_recent_match_coverage(
    *,
    teams: tuple[Team, ...],
    matches: tuple[OfficialMatchRecord, ...],
    as_of_date: date,
    current_window_months: int,
    max_window_months: int,
) -> dict[str, Any]:
    max_from = add_months(as_of_date, -max_window_months)
    current_from = add_months(as_of_date, -current_window_months)
    by_team = {team.name: {"max_window": 0, "current_window": 0} for team in teams}
    for match in matches:
        match_date = parse_record_date(match.match_date)
        for team in (match.home_team, match.away_team):
            if team not in by_team:
                continue
            if max_from <= match_date < as_of_date:
                by_team[team]["max_window"] += 1
            if current_from <= match_date < as_of_date:
                by_team[team]["current_window"] += 1
    max_covered = sum(1 for item in by_team.values() if item["max_window"] > 0)
    current_covered = sum(1 for item in by_team.values() if item["current_window"] > 0)
    total = len(teams)
    return {
        "as_of_date": as_of_date.isoformat(),
        "current_window_months": current_window_months,
        "max_window_months": max_window_months,
        "team_count": total,
        "match_count": len(matches),
        "teams_with_max_window_matches": max_covered,
        "teams_with_current_window_matches": current_covered,
        "max_window_coverage": max_covered / total if total else 0.0,
        "current_window_coverage": current_covered / total if total else 0.0,
        "teams": by_team,
    }


def write_recent_matches_csv(path: str | Path, matches: tuple[OfficialMatchRecord, ...]) -> None:
    rows = [match.to_json_dict() for match in matches]
    write_excel_safe_csv(
        path,
        rows,
        fieldnames=[
            "match_id",
            "source_id",
            "match_date",
            "home_team",
            "away_team",
            "competition",
            "match_importance",
            "venue_context",
            "status",
            "home_score",
            "away_score",
            "home_penalty_score",
            "away_penalty_score",
            "venue",
            "fifa_match_id",
            "home_team_id",
            "away_team_id",
            "source_url",
        ],
    )


def _source_url(
    source: RecentMatchSourceConfig, *, team: Team, from_date: date, to_date: date
) -> str:
    return source.url_template.format(
        team_id=team.team_id,
        team_name=team.name,
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
    )


def _date_bound_played_matches(
    matches: list[OfficialMatchRecord], *, as_of_date: date, from_date: date
) -> list[OfficialMatchRecord]:
    bounded = []
    for match in matches:
        match_date = parse_record_date(match.match_date)
        if from_date <= match_date < as_of_date and match.is_played:
            bounded.append(match)
    return bounded


def _dedupe_matches(matches: list[OfficialMatchRecord]) -> list[OfficialMatchRecord]:
    deduped: dict[str, OfficialMatchRecord] = {}
    for match in matches:
        key = match.fifa_match_id or match.match_id
        deduped[key] = match
    return sorted(deduped.values(), key=lambda item: (item.match_date, item.match_id))


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in value)
