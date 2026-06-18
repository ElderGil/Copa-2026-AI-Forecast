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


def write_backtest_report(path: str | Path, report: dict[str, Any]) -> None:
    write_json(path, report)


def write_backtest_samples_csv(path: str | Path, report: dict[str, Any]) -> None:
    rows = [
        {
            "match_id": sample.get("match_id", ""),
            "match_date": sample.get("match_date", ""),
            "home_team": sample.get("home_team", ""),
            "away_team": sample.get("away_team", ""),
            "home_score": sample.get("home_score", ""),
            "away_score": sample.get("away_score", ""),
            "outcome": sample.get("outcome", ""),
            "home_win_probability": sample.get("home_win_probability", ""),
            "draw_probability": sample.get("draw_probability", ""),
            "away_win_probability": sample.get("away_win_probability", ""),
            "fifa_sum_home_win_probability": sample.get(
                "fifa_sum_home_win_probability", ""
            ),
            "fifa_sum_draw_probability": sample.get("fifa_sum_draw_probability", ""),
            "fifa_sum_away_win_probability": sample.get(
                "fifa_sum_away_win_probability", ""
            ),
            "predicted_label": sample.get("predicted_label", ""),
            "predicted_confidence": sample.get("predicted_confidence", ""),
            "prediction_correct": sample.get("prediction_correct", ""),
            "prior_home_matches": sample.get("prior_home_matches", ""),
            "prior_away_matches": sample.get("prior_away_matches", ""),
        }
        for sample in report.get("samples", [])
    ]
    write_excel_safe_csv(
        path,
        rows,
        fieldnames=[
            "match_id",
            "match_date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "outcome",
            "home_win_probability",
            "draw_probability",
            "away_win_probability",
            "fifa_sum_home_win_probability",
            "fifa_sum_draw_probability",
            "fifa_sum_away_win_probability",
            "predicted_label",
            "predicted_confidence",
            "prediction_correct",
            "prior_home_matches",
            "prior_away_matches",
        ],
    )


def update_readme_validation_section(path: str | Path, report: dict[str, Any]) -> None:
    target = Path(path)
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    section = _validation_markdown_section(report)
    start = "<!-- validation-stats:start -->"
    end = "<!-- validation-stats:end -->"
    block = f"{start}\n{section}\n{end}"
    if start in existing and end in existing:
        before = existing.split(start, 1)[0].rstrip()
        after = existing.split(end, 1)[1].lstrip()
        text = f"{before}\n\n{block}\n\n{after}".rstrip() + "\n"
    else:
        text = f"{existing.rstrip()}\n\n{block}\n"
    target.write_text(text, encoding="utf-8")


def _validation_markdown_section(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    primary = report["primary_baseline_metrics"]
    comparison = report["primary_baseline_comparison"]
    baseline_name = "FIFA SUM-style Elo"
    model_name = "Copa 2026 AI Forecast"
    updated_at = report.get("as_of_date", "")
    sample_count = report.get("sample_count", 0)
    evaluation_start = report.get("evaluation_start", "")
    ece = report.get("calibration", {}).get("expected_calibration_error", 0.0)
    mce = report.get("calibration", {}).get("maximum_calibration_error", 0.0)
    source_note = report.get("primary_baseline_source", "")
    previous_section = _previous_model_section(report.get("previous_model_comparison"))

    rows = [
        _metric_row(
            "Amostras avaliadas",
            f"{sample_count}",
            "-",
            "-",
            "Info",
            f"Partidas do período {evaluation_start} a {updated_at}; cada previsão usa apenas jogos anteriores à partida avaliada.",
        ),
        _metric_row(
            "Acurácia 1X2",
            _pct(metrics["accuracy"]),
            _pct(primary["accuracy"]),
            _delta_pct(comparison["accuracy_delta"]),
            _status_higher_is_better(comparison["accuracy_delta"]),
            "Percentual de vezes em que o resultado mais provável foi o resultado real: vitória mandante, empate ou vitória visitante.",
        ),
        _metric_row(
            "Brier score",
            _num(metrics["brier_score"]),
            _num(primary["brier_score"]),
            _num(comparison["brier_delta"]),
            _status_lower_is_better(comparison["brier_delta"]),
            "Erro probabilístico multiclasses; quanto menor, melhor. Zero seria uma previsão perfeita.",
        ),
        _metric_row(
            "Log loss",
            _num(metrics["log_loss"]),
            _num(primary["log_loss"]),
            _num(comparison["log_loss_delta"]),
            _status_lower_is_better(comparison["log_loss_delta"]),
            "Pune previsões confiantes e erradas; quanto menor, melhor. É mais severo que o Brier.",
        ),
        _metric_row(
            "ECE calibração",
            _num(ece),
            "-",
            "-",
            _status_ece(ece),
            "Expected Calibration Error; mede se a confiança prevista combina com a frequência real observada.",
        ),
        _metric_row(
            "MCE calibração",
            _num(mce),
            "-",
            "-",
            _status_mce(mce),
            "Maximum Calibration Error; pior desvio de calibração entre as faixas de confiança.",
        ),
    ]
    return "\n".join(
        [
            "## Estatísticas da Validação do Modelo",
            "",
            f"**Última atualização dos dados:** `{updated_at}`",
            f"**Modelo:** `{model_name}`",
            f"**Baseline principal:** `{baseline_name}`",
            "",
            "| Métrica | Copa 2026 AI Forecast | Baseline principal | Delta | Status |",
            "|---|---:|---:|---:|---|",
            *rows,
            *previous_section,
            "",
            "**Legenda:** `Bom` melhora o baseline principal ou está em faixa saudável; `Atenção` indica ganho pequeno ou calibração a monitorar; `Ruim` indica resultado pior que o benchmark ou calibração fraca.",
            "",
            f"<sub><em>Baseline principal: {source_note}. Não redistribuímos tabela externa de ranking ou odds; o benchmark é calculado localmente a partir dos registros oficiais FIFA já ingeridos pelo pipeline.</em></sub>",
        ]
    )


def _previous_model_section(comparison: object) -> list[str]:
    if not isinstance(comparison, dict):
        return []
    previous = comparison.get("previous", {})
    current = comparison.get("current", {})
    deltas = comparison.get("deltas", {})
    if not isinstance(previous, dict) or not isinstance(current, dict) or not isinstance(deltas, dict):
        return []
    previous_name = comparison.get("previous_model_name", "modelo_anterior")
    current_name = comparison.get("current_model_name", "modelo_atual")
    previous_samples = comparison.get("previous_sample_count", "-")
    current_samples = comparison.get("current_sample_count", "-")
    return [
        "",
        "### Comparativo da Alteração do Modelo",
        "",
        f"<sub><em>Registro automático para auditoria futura: comparação entre `{previous_name}` e `{current_name}` usando o backtest rolling-origin salvo anteriormente para o mesmo `run_id`.</em></sub>",
        "",
        f"<sub><em>Amostras avaliadas: antes `{previous_samples}`, agora `{current_samples}`. Se este número mudar, a leitura deve considerar alteração de base além da alteração do modelo.</em></sub>",
        "",
        "| Métrica | Antes | Agora | Delta | Leitura |",
        "|---|---:|---:|---:|---|",
        _previous_row(
            "Acurácia 1X2",
            _pct_optional(previous.get("accuracy")),
            _pct_optional(current.get("accuracy")),
            _delta_pct_optional(deltas.get("accuracy")),
            _change_status(deltas.get("accuracy"), higher_is_better=True),
        ),
        _previous_row(
            "Brier score",
            _num_optional(previous.get("brier_score")),
            _num_optional(current.get("brier_score")),
            _num_delta_optional(deltas.get("brier_score")),
            _change_status(deltas.get("brier_score"), higher_is_better=False),
        ),
        _previous_row(
            "Log loss",
            _num_optional(previous.get("log_loss")),
            _num_optional(current.get("log_loss")),
            _num_delta_optional(deltas.get("log_loss")),
            _change_status(deltas.get("log_loss"), higher_is_better=False),
        ),
        _previous_row(
            "ECE calibração",
            _num_optional(previous.get("expected_calibration_error")),
            _num_optional(current.get("expected_calibration_error")),
            _num_delta_optional(deltas.get("expected_calibration_error")),
            _change_status(deltas.get("expected_calibration_error"), higher_is_better=False),
        ),
        _previous_row(
            "MCE calibração",
            _num_optional(previous.get("maximum_calibration_error")),
            _num_optional(current.get("maximum_calibration_error")),
            _num_delta_optional(deltas.get("maximum_calibration_error")),
            _change_status(deltas.get("maximum_calibration_error"), higher_is_better=False),
        ),
    ]


def _previous_row(
    metric: str, previous: str, current: str, delta: str, status: str
) -> str:
    return f"| {metric} | {previous} | {current} | {delta} | {status} |"


def _metric_row(
    metric: str,
    model_value: str,
    baseline_value: str,
    delta: str,
    status: str,
    explanation: str,
) -> str:
    return (
        f"| {metric}<br><sub><em>{explanation}</em></sub> "
        f"| {model_value} | {baseline_value} | {delta} | {status} |"
    )


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _delta_pct(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value * 100:.2f} p.p."


def _num(value: float) -> str:
    return f"{value:.4f}"


def _pct_optional(value: object) -> str:
    if value is None:
        return "-"
    return _pct(float(value))


def _num_optional(value: object) -> str:
    if value is None:
        return "-"
    return _num(float(value))


def _delta_pct_optional(value: object) -> str:
    if value is None:
        return "-"
    return _delta_pct(float(value))


def _num_delta_optional(value: object) -> str:
    if value is None:
        return "-"
    value = float(value)
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.4f}"


def _change_status(value: object, *, higher_is_better: bool) -> str:
    if value is None:
        return "Sem comparação"
    delta = float(value)
    if abs(delta) < 0.0005:
        return "Estável"
    improved = delta > 0 if higher_is_better else delta < 0
    return "Melhorou" if improved else "Piorou"


def _status_higher_is_better(delta: float) -> str:
    if delta >= 0.03:
        return "Bom"
    if delta >= 0:
        return "Atenção"
    return "Ruim"


def _status_lower_is_better(delta: float) -> str:
    if delta <= -0.03:
        return "Bom"
    if delta <= 0:
        return "Atenção"
    return "Ruim"


def _status_ece(value: float) -> str:
    if value <= 0.05:
        return "Bom"
    if value <= 0.15:
        return "Atenção"
    return "Ruim"


def _status_mce(value: float) -> str:
    if value <= 0.10:
        return "Bom"
    if value <= 0.25:
        return "Atenção"
    return "Ruim"


def write_calibration_bins_csv(path: str | Path, report: dict[str, Any]) -> None:
    bins = report.get("calibration", {}).get("bins", [])
    rows = [
        {
            "lower_bound": item.get("lower_bound", ""),
            "upper_bound": item.get("upper_bound", ""),
            "sample_count": item.get("sample_count", ""),
            "mean_probability": item.get("mean_probability", ""),
            "observed_frequency": item.get("observed_frequency", ""),
            "absolute_error": item.get("absolute_error", ""),
        }
        for item in bins
    ]
    write_excel_safe_csv(
        path,
        rows,
        fieldnames=[
            "lower_bound",
            "upper_bound",
            "sample_count",
            "mean_probability",
            "observed_frequency",
            "absolute_error",
        ],
    )


def _advancement(team: dict[str, Any], key: str) -> object:
    return team.get("advancement_probabilities", {}).get(key, "")
