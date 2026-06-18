from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_excel_safe_csv(
    path: str | Path, rows: list[dict[str, object]], *, fieldnames: list[str]
) -> None:
    """Write CSV with UTF-8 BOM so Excel reads accents correctly."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_forecast_run_metadata(path: str | Path, latest: dict[str, Any]) -> None:
    """Persist run metadata separately from public page assets."""

    metadata = latest.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("latest payload must include a metadata object.")
    write_json(path, metadata)


def write_forecast_team_csv(path: str | Path, latest: dict[str, Any]) -> None:
    rows = [
        {
            "rank": team["rank"],
            "team": team["team"],
            "group": team.get("group") or "",
            "champion_probability": team["champion_probability"],
            "round_of_32_probability": _advancement(team, "round_of_32"),
            "semifinal_probability": _advancement(team, "semifinal"),
            "final_probability": _advancement(team, "final"),
            "strength": team.get("strength", ""),
            "used_pillars": "|".join(team.get("used_pillars", [])),
            "excluded_pillars": "|".join(team.get("excluded_pillars", [])),
        }
        for team in latest.get("teams", [])
    ]
    write_excel_safe_csv(
        path,
        rows,
        fieldnames=[
            "rank",
            "team",
            "group",
            "champion_probability",
            "round_of_32_probability",
            "semifinal_probability",
            "final_probability",
            "strength",
            "used_pillars",
            "excluded_pillars",
        ],
    )


def write_advancement_probabilities(path: str | Path, latest: dict[str, Any]) -> None:
    payload = {
        "run_id": latest.get("run_id"),
        "as_of_date": latest.get("as_of_date"),
        "teams": [
            {
                "team": team["team"],
                "rank": team["rank"],
                **team.get("advancement_probabilities", {}),
            }
            for team in latest.get("teams", [])
        ],
    }
    write_json(path, payload)


def write_advancement_csv(path: str | Path, latest: dict[str, Any]) -> None:
    rows = [
        {
            "team": team["team"],
            "rank": team["rank"],
            "round_of_32": _advancement(team, "round_of_32"),
            "round_of_16": _advancement(team, "round_of_16"),
            "quarterfinal": _advancement(team, "quarterfinal"),
            "semifinal": _advancement(team, "semifinal"),
            "final": _advancement(team, "final"),
            "champion": _advancement(team, "champion"),
        }
        for team in latest.get("teams", [])
    ]
    write_excel_safe_csv(
        path,
        rows,
        fieldnames=[
            "team",
            "rank",
            "round_of_32",
            "round_of_16",
            "quarterfinal",
            "semifinal",
            "final",
            "champion",
        ],
    )


def write_explanation_payload(path: str | Path, payload: dict[str, Any]) -> None:
    write_json(path, payload)


def write_explanation_csv(path: str | Path, payload: dict[str, Any]) -> None:
    rows = [
        {
            "team": team["team"],
            "rank": team.get("rank", ""),
            "champion_probability": team.get("champion_probability", ""),
            "used_pillars": "|".join(team.get("used_pillars", [])),
            "excluded_pillars": "|".join(team.get("excluded_pillars", [])),
            "drivers": "|".join(team.get("drivers", [])),
            "summary": team.get("summary", ""),
        }
        for team in payload.get("teams", [])
    ]
    write_excel_safe_csv(
        path,
        rows,
        fieldnames=[
            "team",
            "rank",
            "champion_probability",
            "used_pillars",
            "excluded_pillars",
            "drivers",
            "summary",
        ],
    )


def write_pillar_report_csv(path: str | Path, latest: dict[str, Any]) -> None:
    rows = [
        {
            "key": pillar.get("key") or pillar.get("name"),
            "label": pillar.get("label", ""),
            "status": pillar.get("status", ""),
            "coverage": pillar.get("coverage", ""),
            "available_teams": pillar.get("available_teams", ""),
            "total_teams": pillar.get("total_teams", ""),
            "missing_teams": pillar.get("missing_teams", ""),
            "reason": pillar.get("reason", ""),
            "source": pillar.get("source", ""),
        }
        for pillar in latest.get("pillars", [])
    ]
    write_excel_safe_csv(
        path,
        rows,
        fieldnames=[
            "key",
            "label",
            "status",
            "coverage",
            "available_teams",
            "total_teams",
            "missing_teams",
            "reason",
            "source",
        ],
    )


def _advancement(team: dict[str, Any], key: str) -> object:
    return team.get("advancement_probabilities", {}).get(key, "")
