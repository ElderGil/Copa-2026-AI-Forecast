from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TeamExplanation:
    team: str
    used_pillars: tuple[str, ...]
    excluded_pillars: tuple[str, ...]
    summary: str
    drivers: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "team": self.team,
            "used_pillars": list(self.used_pillars),
            "excluded_pillars": list(self.excluded_pillars),
            "summary": self.summary,
            "drivers": list(self.drivers),
        }


@dataclass(frozen=True)
class TeamRunDelta:
    team: str
    previous_rank: int | None
    current_rank: int | None
    rank_delta: int | None
    previous_champion_probability: float | None
    current_champion_probability: float | None
    champion_probability_delta: float | None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "team": self.team,
            "previous_rank": self.previous_rank,
            "current_rank": self.current_rank,
            "rank_delta": self.rank_delta,
            "previous_champion_probability": self.previous_champion_probability,
            "current_champion_probability": self.current_champion_probability,
            "champion_probability_delta": self.champion_probability_delta,
        }


def build_team_explanation(
    *,
    team: str,
    used_pillars: list[str],
    excluded_pillars: list[str],
    drivers: list[str] | None = None,
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
        drivers=tuple(drivers or ()),
    )


def build_team_explanation_from_row(team_row: dict[str, Any]) -> TeamExplanation:
    return build_team_explanation(
        team=str(team_row["team"]),
        used_pillars=[str(item) for item in team_row.get("used_pillars", [])],
        excluded_pillars=[str(item) for item in team_row.get("excluded_pillars", [])],
        drivers=team_row_drivers(team_row),
    )


def team_row_drivers(team_row: dict[str, Any]) -> list[str]:
    drivers: list[str] = []
    probability = float(team_row.get("champion_probability", 0.0))
    if probability:
        drivers.append(f"chance_titulo={probability:.4f}")
    advancement = team_row.get("advancement_probabilities", {})
    if isinstance(advancement, dict) and advancement:
        final_probability = advancement.get("final")
        if final_probability is not None:
            drivers.append(f"chance_final={float(final_probability):.4f}")
    signal = team_row.get("tournament_signal", {})
    if isinstance(signal, dict):
        points = signal.get("points")
        goal_difference = signal.get("goal_difference")
        if points is not None:
            drivers.append(f"pontos_torneio={points}")
        if goal_difference is not None:
            drivers.append(f"saldo_gols={goal_difference}")
    strength = team_row.get("strength")
    if strength is not None:
        drivers.append(f"forca_modelo={float(strength):.2f}")
    return drivers


def build_explanation_payload(
    latest: dict[str, Any],
    *,
    team: str | None = None,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = latest.get("teams", [])
    if team:
        rows = [row for row in rows if str(row.get("team", "")).casefold() == team.casefold()]
        if not rows:
            raise ValueError(f"Team not found in latest forecast: {team}")

    explanations = [
        build_team_explanation_from_row(row).to_json_dict()
        | {
            "rank": row.get("rank"),
            "champion_probability": row.get("champion_probability"),
            "advancement_probabilities": row.get("advancement_probabilities", {}),
        }
        for row in rows
    ]
    payload: dict[str, Any] = {
        "run_id": latest.get("run_id"),
        "as_of_date": latest.get("as_of_date"),
        "team_count": len(explanations),
        "pillars": latest.get("pillars", []),
        "teams": explanations,
    }
    if previous is not None:
        payload["comparison"] = compare_forecast_runs(previous=previous, current=latest)
    return payload


def compare_forecast_runs(
    *, previous: dict[str, Any], current: dict[str, Any]
) -> dict[str, Any]:
    previous_teams = {
        str(team["team"]): team for team in previous.get("teams", []) if "team" in team
    }
    current_teams = {
        str(team["team"]): team for team in current.get("teams", []) if "team" in team
    }
    names = sorted(set(previous_teams) | set(current_teams), key=str.casefold)
    deltas = [
        _team_delta(name, previous_teams.get(name), current_teams.get(name)).to_json_dict()
        for name in names
    ]
    movers = sorted(
        deltas,
        key=lambda item: abs(float(item["champion_probability_delta"] or 0.0)),
        reverse=True,
    )
    return {
        "previous_run_id": previous.get("run_id"),
        "current_run_id": current.get("run_id"),
        "previous_as_of_date": previous.get("as_of_date"),
        "current_as_of_date": current.get("as_of_date"),
        "team_deltas": deltas,
        "top_probability_movers": movers[:10],
    }


def _team_delta(
    team: str, previous_row: dict[str, Any] | None, current_row: dict[str, Any] | None
) -> TeamRunDelta:
    previous_rank = _optional_int(previous_row, "rank")
    current_rank = _optional_int(current_row, "rank")
    previous_probability = _optional_float(previous_row, "champion_probability")
    current_probability = _optional_float(current_row, "champion_probability")
    rank_delta = None
    if previous_rank is not None and current_rank is not None:
        rank_delta = previous_rank - current_rank
    probability_delta = None
    if previous_probability is not None and current_probability is not None:
        probability_delta = current_probability - previous_probability
    return TeamRunDelta(
        team=team,
        previous_rank=previous_rank,
        current_rank=current_rank,
        rank_delta=rank_delta,
        previous_champion_probability=previous_probability,
        current_champion_probability=current_probability,
        champion_probability_delta=probability_delta,
    )


def _optional_int(row: dict[str, Any] | None, key: str) -> int | None:
    if row is None or row.get(key) is None:
        return None
    return int(row[key])


def _optional_float(row: dict[str, Any] | None, key: str) -> float | None:
    if row is None or row.get(key) is None:
        return None
    return float(row[key])
