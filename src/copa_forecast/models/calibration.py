from __future__ import annotations

import math


def brier_score(probabilities: list[float], outcomes: list[int]) -> float:
    if len(probabilities) != len(outcomes):
        raise ValueError("probabilities and outcomes must have the same length.")
    if not probabilities:
        raise ValueError("At least one probability is required.")
    return sum((p - y) ** 2 for p, y in zip(probabilities, outcomes)) / len(probabilities)


def log_loss(probabilities: list[float], outcomes: list[int], eps: float = 1e-15) -> float:
    if len(probabilities) != len(outcomes):
        raise ValueError("probabilities and outcomes must have the same length.")
    if not probabilities:
        raise ValueError("At least one probability is required.")
    total = 0.0
    for p, y in zip(probabilities, outcomes):
        bounded = min(max(p, eps), 1 - eps)
        total += y * math.log(bounded) + (1 - y) * math.log(1 - bounded)
    return -total / len(probabilities)

