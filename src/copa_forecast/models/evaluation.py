from __future__ import annotations

from dataclasses import dataclass

from copa_forecast.models.calibration import brier_score, log_loss


@dataclass(frozen=True)
class EvaluationReport:
    brier_score: float
    log_loss: float
    sample_count: int


def evaluate_binary_probabilities(
    probabilities: list[float], outcomes: list[int]
) -> EvaluationReport:
    return EvaluationReport(
        brier_score=brier_score(probabilities, outcomes),
        log_loss=log_loss(probabilities, outcomes),
        sample_count=len(probabilities),
    )

