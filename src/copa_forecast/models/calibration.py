from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


def brier_score(probabilities: list[float], outcomes: list[int]) -> float:
    if len(probabilities) != len(outcomes):
        raise ValueError("probabilities and outcomes must have the same length.")
    if not probabilities:
        raise ValueError("At least one probability is required.")
    return sum((p - y) ** 2 for p, y in zip(probabilities, outcomes, strict=False)) / len(probabilities)


def log_loss(probabilities: list[float], outcomes: list[int], eps: float = 1e-15) -> float:
    if len(probabilities) != len(outcomes):
        raise ValueError("probabilities and outcomes must have the same length.")
    if not probabilities:
        raise ValueError("At least one probability is required.")
    total = 0.0
    for p, y in zip(probabilities, outcomes, strict=False):
        bounded = min(max(p, eps), 1 - eps)
        total += y * math.log(bounded) + (1 - y) * math.log(1 - bounded)
    return -total / len(probabilities)


@dataclass(frozen=True)
class CalibrationBin:
    lower_bound: float
    upper_bound: float
    sample_count: int
    mean_probability: float
    observed_frequency: float

    @property
    def absolute_error(self) -> float:
        return abs(self.mean_probability - self.observed_frequency)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "sample_count": self.sample_count,
            "mean_probability": self.mean_probability,
            "observed_frequency": self.observed_frequency,
            "absolute_error": self.absolute_error,
        }


def multiclass_brier_score(
    predictions: list[dict[str, float]], outcomes: list[str], *, labels: tuple[str, ...]
) -> float:
    _require_multiclass_inputs(predictions, outcomes, labels=labels)
    total = 0.0
    for prediction, outcome in zip(predictions, outcomes, strict=False):
        normalized = _normalized_prediction(prediction, labels=labels)
        total += sum(
            (normalized[label] - (1.0 if label == outcome else 0.0)) ** 2
            for label in labels
        )
    return total / len(predictions)


def multiclass_log_loss(
    predictions: list[dict[str, float]],
    outcomes: list[str],
    *,
    labels: tuple[str, ...],
    eps: float = 1e-15,
) -> float:
    _require_multiclass_inputs(predictions, outcomes, labels=labels)
    total = 0.0
    for prediction, outcome in zip(predictions, outcomes, strict=False):
        normalized = _normalized_prediction(prediction, labels=labels)
        probability = min(max(normalized[outcome], eps), 1.0)
        total += math.log(probability)
    return -total / len(predictions)


def classification_accuracy(
    predictions: list[dict[str, float]], outcomes: list[str], *, labels: tuple[str, ...]
) -> float:
    _require_multiclass_inputs(predictions, outcomes, labels=labels)
    correct = 0
    for prediction, outcome in zip(predictions, outcomes, strict=False):
        normalized = _normalized_prediction(prediction, labels=labels)
        winner = max(labels, key=lambda label: (normalized[label], label))
        correct += 1 if winner == outcome else 0
    return correct / len(predictions)


def calibration_bins(
    probabilities: list[float], outcomes: list[int], *, bin_count: int = 10
) -> list[CalibrationBin]:
    if len(probabilities) != len(outcomes):
        raise ValueError("probabilities and outcomes must have the same length.")
    if bin_count <= 0:
        raise ValueError("bin_count must be positive.")
    if not probabilities:
        return []

    buckets = [
        {"probabilities": [], "outcomes": []}
        for _ in range(bin_count)
    ]
    for probability, outcome in zip(probabilities, outcomes, strict=False):
        if outcome not in (0, 1):
            raise ValueError("outcomes must be binary values.")
        bounded = min(max(probability, 0.0), 1.0)
        index = min(int(bounded * bin_count), bin_count - 1)
        buckets[index]["probabilities"].append(bounded)
        buckets[index]["outcomes"].append(outcome)

    bins = []
    for index, bucket in enumerate(buckets):
        count = len(bucket["probabilities"])
        lower = index / bin_count
        upper = (index + 1) / bin_count
        if count == 0:
            bins.append(
                CalibrationBin(
                    lower_bound=lower,
                    upper_bound=upper,
                    sample_count=0,
                    mean_probability=0.0,
                    observed_frequency=0.0,
                )
            )
            continue
        bins.append(
            CalibrationBin(
                lower_bound=lower,
                upper_bound=upper,
                sample_count=count,
                mean_probability=sum(bucket["probabilities"]) / count,
                observed_frequency=sum(bucket["outcomes"]) / count,
            )
        )
    return bins


def expected_calibration_error(bins: list[CalibrationBin]) -> float:
    total = sum(item.sample_count for item in bins)
    if total == 0:
        return 0.0
    return sum(item.absolute_error * item.sample_count for item in bins) / total


def maximum_calibration_error(bins: list[CalibrationBin]) -> float:
    populated = [item.absolute_error for item in bins if item.sample_count > 0]
    return max(populated, default=0.0)


def apply_temperature(
    prediction: dict[str, float],
    temperature: float,
    *,
    labels: tuple[str, ...],
    eps: float = 1e-12,
) -> dict[str, float]:
    """Temperature-scale a probability vector via log-space division by T."""

    if temperature <= 0:
        raise ValueError("temperature must be positive.")
    normalized = _normalized_prediction(prediction, labels=labels)
    logits = {label: math.log(max(normalized[label], eps)) / temperature for label in labels}
    max_logit = max(logits.values())
    exps = {label: math.exp(logit - max_logit) for label, logit in logits.items()}
    total = sum(exps.values())
    return {label: value / total for label, value in exps.items()}


def fit_temperature(
    predictions: list[dict[str, float]],
    outcomes: list[str],
    *,
    labels: tuple[str, ...],
    bounds: tuple[float, float] = (0.5, 5.0),
    iterations: int = 40,
) -> float:
    """Find the temperature minimizing multiclass log loss (1-D golden search)."""

    _require_multiclass_inputs(predictions, outcomes, labels=labels)

    def loss(temperature: float) -> float:
        scaled = [
            apply_temperature(prediction, temperature, labels=labels)
            for prediction in predictions
        ]
        return multiclass_log_loss(scaled, outcomes, labels=labels)

    low, high = bounds
    golden = (math.sqrt(5) - 1) / 2
    c = high - golden * (high - low)
    d = low + golden * (high - low)
    fc, fd = loss(c), loss(d)
    for _ in range(iterations):
        if fc < fd:
            high, d, fd = d, c, fc
            c = high - golden * (high - low)
            fc = loss(c)
        else:
            low, c, fc = c, d, fd
            d = low + golden * (high - low)
            fd = loss(d)
    return round((low + high) / 2, 4)


def _require_multiclass_inputs(
    predictions: list[dict[str, float]], outcomes: list[str], *, labels: tuple[str, ...]
) -> None:
    if len(predictions) != len(outcomes):
        raise ValueError("predictions and outcomes must have the same length.")
    if not predictions:
        raise ValueError("At least one prediction is required.")
    if not labels:
        raise ValueError("At least one label is required.")
    allowed = set(labels)
    for outcome in outcomes:
        if outcome not in allowed:
            raise ValueError(f"Unknown outcome label: {outcome}")


def _normalized_prediction(
    prediction: dict[str, float], *, labels: tuple[str, ...]
) -> dict[str, float]:
    values = {label: float(prediction.get(label, 0.0)) for label in labels}
    if any(value < 0 for value in values.values()):
        raise ValueError("Prediction probabilities cannot be negative.")
    total = sum(values.values())
    if total <= 0:
        raise ValueError("Prediction probability total must be positive.")
    return {label: value / total for label, value in values.items()}
