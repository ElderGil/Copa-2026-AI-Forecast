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
            "strength",
            "used_pillars",
            "excluded_pillars",
        ],
    )
