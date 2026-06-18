from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from copa_forecast.config import load_config
from copa_forecast.data.contracts import OfficialCompetitionState
from copa_forecast.data.ingest import build_competition_state, persist_raw_extract
from copa_forecast.data.recent_matches import load_recent_matches, run_recent_match_etl
from copa_forecast.data.sources.fifa import JsonFifaParser, UrlOrFileFifaCrawler
from copa_forecast.data.validate import (
    require_non_empty_state,
    require_official_competition_state,
)
from copa_forecast.forecast import build_latest_forecast
from copa_forecast.models.evaluation import rolling_origin_backtest
from copa_forecast.reporting.artifacts import (
    write_advancement_csv,
    write_advancement_probabilities,
    write_backtest_report,
    write_backtest_samples_csv,
    write_calibration_bins_csv,
    write_explanation_csv,
    write_explanation_payload,
    write_forecast_run_metadata,
    write_forecast_team_csv,
    write_pillar_report_csv,
    update_readme_validation_section,
)
from copa_forecast.reporting.explanations import build_explanation_payload
from copa_forecast.site.static_page import render_static_page


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="copa-forecast")
    subparsers = parser.add_subparsers(dest="command", required=True)
    fetch_parser = subparsers.add_parser("fetch-fifa")
    fetch_parser.add_argument("--config", required=True)
    recent_parser = subparsers.add_parser("etl-recent-matches")
    recent_parser.add_argument("--config", required=True)
    forecast_parser = subparsers.add_parser("forecast")
    forecast_parser.add_argument("--config", required=True)
    forecast_parser.add_argument("--recent-matches")
    simulate_parser = subparsers.add_parser("simulate")
    simulate_parser.add_argument("--config", required=True)
    simulate_parser.add_argument("--recent-matches")
    backtest_parser = subparsers.add_parser("backtest")
    backtest_parser.add_argument("--config", required=True)
    backtest_parser.add_argument("--matches")
    backtest_parser.add_argument("--evaluation-months", type=int, default=12)
    backtest_parser.add_argument("--lookback-months", type=int, default=24)
    backtest_parser.add_argument("--min-prior-matches", type=int, default=2)
    backtest_parser.add_argument("--bin-count", type=int, default=10)
    explain_parser = subparsers.add_parser("explain")
    explain_parser.add_argument("--latest-json", required=True)
    explain_parser.add_argument("--output", required=True)
    explain_parser.add_argument("--previous-json")
    explain_parser.add_argument("--team")
    site_parser = subparsers.add_parser("render-site")
    site_parser.add_argument("--config", required=True)
    site_parser.add_argument("--latest-json", required=True)
    args = parser.parse_args(argv)

    if args.command == "fetch-fifa":
        return fetch_fifa(args.config)
    if args.command == "etl-recent-matches":
        return etl_recent_matches(args.config)
    if args.command == "forecast":
        return forecast(args.config, recent_matches_path=args.recent_matches)
    if args.command == "simulate":
        return simulate(args.config, recent_matches_path=args.recent_matches)
    if args.command == "backtest":
        return backtest(
            args.config,
            matches_path=args.matches,
            evaluation_months=args.evaluation_months,
            lookback_months=args.lookback_months,
            min_prior_matches=args.min_prior_matches,
            bin_count=args.bin_count,
        )
    if args.command == "explain":
        return explain(
            latest_json=args.latest_json,
            output=args.output,
            previous_json=args.previous_json,
            team=args.team,
        )
    if args.command == "render-site":
        return render_site(args.config, args.latest_json)
    return 2


def fetch_fifa(config_path: str) -> int:
    states = _load_official_states(config_path)
    print(json.dumps({"states": len(states)}, sort_keys=True))
    return 0


def etl_recent_matches(config_path: str) -> int:
    config = load_config(config_path)
    states = _load_official_states(config_path)
    state = _merge_official_states(states)
    result = run_recent_match_etl(config=config, state=state)
    print(
        json.dumps(
            {
                "run_id": config.run_id,
                "matches": len(result.matches),
                "latest_matches": str(result.output_json),
                "matches_csv": str(result.output_csv),
                "coverage": str(result.coverage_json),
                "max_window_coverage": result.coverage.get("max_window_coverage"),
                "current_window_coverage": result.coverage.get("current_window_coverage"),
            },
            sort_keys=True,
        )
    )
    return 0


def forecast(config_path: str, *, recent_matches_path: str | None = None) -> int:
    config = load_config(config_path)
    states = _load_official_states(config_path)
    state = _merge_official_states(states)
    recent_matches = _load_recent_matches_for_run(
        config_path=config_path, recent_matches_path=recent_matches_path
    )
    latest = build_latest_forecast(config=config, state=state, recent_matches=recent_matches)
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


def simulate(config_path: str, *, recent_matches_path: str | None = None) -> int:
    config = load_config(config_path)
    states = _load_official_states(config_path)
    state = _merge_official_states(states)
    recent_matches = _load_recent_matches_for_run(
        config_path=config_path, recent_matches_path=recent_matches_path
    )
    latest = build_latest_forecast(config=config, state=state, recent_matches=recent_matches)
    run_dir = (
        config.site.output_dir.parent
        / "data"
        / "processed"
        / "simulation_runs"
        / config.run_id
    )
    advancement_json = run_dir / "advancement.json"
    advancement_csv = run_dir / "advancement.csv"
    write_advancement_probabilities(advancement_json, latest)
    write_advancement_csv(advancement_csv, latest)
    print(
        json.dumps(
            {
                "run_id": config.run_id,
                "teams": len(latest["teams"]),
                "advancement_json": str(advancement_json),
                "advancement_csv": str(advancement_csv),
            },
            sort_keys=True,
        )
    )
    return 0


def backtest(
    config_path: str,
    *,
    matches_path: str | None = None,
    evaluation_months: int = 12,
    lookback_months: int = 24,
    min_prior_matches: int = 2,
    bin_count: int = 10,
) -> int:
    config = load_config(config_path)
    matches = _load_recent_matches_for_run(
        config_path=config_path, recent_matches_path=matches_path
    )
    if not matches:
        raise ValueError("Backtest requires a recent-match JSON file.")
    report = rolling_origin_backtest(
        matches=matches,
        as_of_date=config.as_of_date,
        evaluation_months=evaluation_months,
        lookback_months=lookback_months,
        half_life_days=config.feature_windows.decay_half_life_days,
        min_prior_matches=min_prior_matches,
        bin_count=bin_count,
    )
    run_dir = (
        config.site.output_dir.parent
        / "data"
        / "processed"
        / "backtests"
        / config.run_id
    )
    report_json = run_dir / "report.json"
    samples_csv = run_dir / "samples.csv"
    calibration_csv = run_dir / "calibration_bins.csv"
    readme_path = config.site.output_dir.parent / "README.md"
    previous_report = _read_json_if_exists(report_json)
    if previous_report:
        report["previous_model_comparison"] = _compare_backtest_reports(
            previous=previous_report,
            current=report,
        )
    write_backtest_report(report_json, report)
    write_backtest_samples_csv(samples_csv, report)
    write_calibration_bins_csv(calibration_csv, report)
    update_readme_validation_section(readme_path, report)
    print(
        json.dumps(
            {
                "run_id": config.run_id,
                "sample_count": report["sample_count"],
                "brier_score": report["metrics"]["brier_score"],
                "log_loss": report["metrics"]["log_loss"],
                "accuracy": report["metrics"]["accuracy"],
                "primary_baseline": report["primary_baseline_name"],
                "report": str(report_json),
                "samples_csv": str(samples_csv),
                "calibration_csv": str(calibration_csv),
                "readme": str(readme_path),
            },
            sort_keys=True,
        )
    )
    return 0


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _compare_backtest_reports(
    *, previous: dict[str, Any], current: dict[str, Any]
) -> dict[str, Any]:
    previous_metrics = {
        **previous.get("metrics", {}),
        "expected_calibration_error": previous.get("calibration", {}).get(
            "expected_calibration_error"
        ),
        "maximum_calibration_error": previous.get("calibration", {}).get(
            "maximum_calibration_error"
        ),
    }
    previous_model_name = previous.get("model_name", "unknown")
    previous_sample_count = previous.get("sample_count")
    current_metrics = current.get("metrics", {})
    current_calibration = current.get("calibration", {})
    return {
        "previous_model_name": previous_model_name,
        "current_model_name": current.get("model_name", "unknown"),
        "previous_sample_count": previous_sample_count,
        "current_sample_count": current.get("sample_count"),
        "deltas": {
            "accuracy": _metric_delta(current_metrics, previous_metrics, "accuracy"),
            "brier_score": _metric_delta(current_metrics, previous_metrics, "brier_score"),
            "log_loss": _metric_delta(current_metrics, previous_metrics, "log_loss"),
            "expected_calibration_error": _metric_delta(
                current_calibration,
                previous_metrics,
                "expected_calibration_error",
            ),
            "maximum_calibration_error": _metric_delta(
                current_calibration,
                previous_metrics,
                "maximum_calibration_error",
            ),
        },
        "previous": {
            "accuracy": previous_metrics.get("accuracy"),
            "brier_score": previous_metrics.get("brier_score"),
            "log_loss": previous_metrics.get("log_loss"),
            "expected_calibration_error": previous_metrics.get("expected_calibration_error"),
            "maximum_calibration_error": previous_metrics.get("maximum_calibration_error"),
        },
        "current": {
            "accuracy": current_metrics.get("accuracy"),
            "brier_score": current_metrics.get("brier_score"),
            "log_loss": current_metrics.get("log_loss"),
            "expected_calibration_error": current_calibration.get(
                "expected_calibration_error"
            ),
            "maximum_calibration_error": current_calibration.get(
                "maximum_calibration_error"
            ),
        },
    }


def _metric_delta(
    current: dict[str, Any], previous: dict[str, Any], key: str
) -> float | None:
    current_value = current.get(key)
    previous_value = previous.get(key)
    if current_value is None or previous_value is None:
        return None
    return float(current_value) - float(previous_value)


def explain(
    *,
    latest_json: str,
    output: str,
    previous_json: str | None = None,
    team: str | None = None,
) -> int:
    latest = json.loads(Path(latest_json).read_text(encoding="utf-8"))
    previous = (
        json.loads(Path(previous_json).read_text(encoding="utf-8"))
        if previous_json
        else None
    )
    payload = build_explanation_payload(latest, previous=previous, team=team)
    output_dir = Path(output)
    write_explanation_payload(output_dir / "explanations.json", payload)
    write_explanation_csv(output_dir / "explanations.csv", payload)
    write_pillar_report_csv(output_dir / "pillars.csv", latest)
    print(
        json.dumps(
            {
                "run_id": payload.get("run_id"),
                "team_count": payload.get("team_count"),
                "explanations_json": str(output_dir / "explanations.json"),
                "explanations_csv": str(output_dir / "explanations.csv"),
                "pillars_csv": str(output_dir / "pillars.csv"),
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


def _load_recent_matches_for_run(
    *, config_path: str, recent_matches_path: str | None
):
    config = load_config(config_path)
    if recent_matches_path:
        path = Path(recent_matches_path)
    elif config.recent_matches.declared:
        path = config.recent_matches.processed_output_dir / "latest_matches.json"
    else:
        return ()
    if not path.exists():
        return ()
    return load_recent_matches(path)


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
