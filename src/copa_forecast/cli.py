from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from copa_forecast.config import load_config
from copa_forecast.data.ingest import build_competition_state, persist_raw_extract
from copa_forecast.data.contracts import OfficialCompetitionState
from copa_forecast.data.sources.fifa import JsonFifaParser, UrlOrFileFifaCrawler
from copa_forecast.data.validate import (
    require_non_empty_state,
    require_official_competition_state,
)
from copa_forecast.forecast import build_latest_forecast
from copa_forecast.reporting.artifacts import (
    write_forecast_run_metadata,
    write_forecast_team_csv,
)
from copa_forecast.site.static_page import render_static_page


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="copa-forecast")
    subparsers = parser.add_subparsers(dest="command", required=True)
    fetch_parser = subparsers.add_parser("fetch-fifa")
    fetch_parser.add_argument("--config", required=True)
    forecast_parser = subparsers.add_parser("forecast")
    forecast_parser.add_argument("--config", required=True)
    site_parser = subparsers.add_parser("render-site")
    site_parser.add_argument("--config", required=True)
    site_parser.add_argument("--latest-json", required=True)
    args = parser.parse_args(argv)

    if args.command == "fetch-fifa":
        return fetch_fifa(args.config)
    if args.command == "forecast":
        return forecast(args.config)
    if args.command == "render-site":
        return render_site(args.config, args.latest_json)
    return 2


def fetch_fifa(config_path: str) -> int:
    states = _load_official_states(config_path)
    print(json.dumps({"states": len(states)}, sort_keys=True))
    return 0


def forecast(config_path: str) -> int:
    config = load_config(config_path)
    states = _load_official_states(config_path)
    state = _merge_official_states(states)
    latest = build_latest_forecast(config=config, state=state)
    render_static_page(
        latest=latest,
        github_url=config.project_github_url,
        output_dir=config.site.output_dir,
    )

    run_dir = (
        config.site.output_dir.parent
        / "data"
        / "processed"
        / "forecast_runs"
        / config.run_id
    )
    write_forecast_run_metadata(run_dir / "metadata.json", latest)
    write_forecast_team_csv(run_dir / "teams.csv", latest)
    print(
        json.dumps(
            {
                "run_id": config.run_id,
                "teams": len(latest["teams"]),
                "latest_json": str(config.site.output_dir / "data" / "latest.json"),
                "metadata": str(run_dir / "metadata.json"),
            },
            sort_keys=True,
        )
    )
    return 0


def _load_official_states(config_path: str) -> list[OfficialCompetitionState]:
    config = load_config(config_path)
    crawler = UrlOrFileFifaCrawler()
    parser = JsonFifaParser()
    states: list[OfficialCompetitionState] = []
    for source in config.official_fifa.sources:
        payload = crawler.fetch(source.url)
        extract = persist_raw_extract(
            source_id=source.source_id,
            source_url=source.url,
            payload=payload,
            output_dir=config.official_fifa.raw_output_dir,
            parser_version=parser.parser_version,
            retrieved_at=datetime.now(timezone.utc),
        )
        state = build_competition_state(
            extract=extract,
            as_of_date=config.as_of_date.isoformat(),
            parser=parser,
        )
        require_official_competition_state(
            state, degraded_mode_allowed=config.official_fifa.degraded_mode_allowed
        )
        require_non_empty_state(state)
        states.append(state)
    return states


def _merge_official_states(states: list[OfficialCompetitionState]) -> OfficialCompetitionState:
    if not states:
        raise ValueError("At least one official competition state is required.")
    if len(states) == 1:
        return states[0]

    team_by_id = {}
    fixtures = []
    extract_ids = []
    for state in states:
        extract_ids.extend(state.fifa_extract_ids)
        for team in state.teams:
            team_by_id[team.team_id] = team
        fixtures.extend(state.fixtures)
    return OfficialCompetitionState(
        as_of_date=states[-1].as_of_date,
        fifa_extract_ids=tuple(extract_ids),
        teams=tuple(team_by_id.values()),
        fixtures=tuple(fixtures),
        degraded=any(state.degraded for state in states),
    )


def render_site(config_path: str, latest_json: str) -> int:
    config = load_config(config_path)
    latest = json.loads(Path(latest_json).read_text(encoding="utf-8"))
    render_static_page(
        latest=latest,
        github_url=config.project_github_url,
        output_dir=config.site.output_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
