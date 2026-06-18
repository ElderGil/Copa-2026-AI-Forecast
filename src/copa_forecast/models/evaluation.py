from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from copa_forecast.data.contracts import OfficialMatchRecord
from copa_forecast.features.leakage import parse_record_date
from copa_forecast.features.windows import exponential_decay_weight
from copa_forecast.models.baselines import three_way_baseline
from copa_forecast.models.calibration import (
    brier_score,
    calibration_bins,
    classification_accuracy,
    expected_calibration_error,
    log_loss,
    maximum_calibration_error,
    multiclass_brier_score,
    multiclass_log_loss,
)


MATCH_OUTCOME_LABELS = ("home_win", "draw", "away_win")


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


@dataclass(frozen=True)
class MatchBacktestSample:
    match_id: str
    match_date: str
    home_team: str
    away_team: str
    outcome: str
    home_score: int
    away_score: int
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    baseline_home_win_probability: float
    baseline_draw_probability: float
    baseline_away_win_probability: float
    fifa_sum_home_win_probability: float
    fifa_sum_draw_probability: float
    fifa_sum_away_win_probability: float
    predicted_label: str
    predicted_confidence: float
    prediction_correct: bool
    prior_home_matches: int
    prior_away_matches: int

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def model_prediction(self) -> dict[str, float]:
        return {
            "home_win": self.home_win_probability,
            "draw": self.draw_probability,
            "away_win": self.away_win_probability,
        }

    @property
    def baseline_prediction(self) -> dict[str, float]:
        return {
            "home_win": self.baseline_home_win_probability,
            "draw": self.baseline_draw_probability,
            "away_win": self.baseline_away_win_probability,
        }

    @property
    def fifa_sum_prediction(self) -> dict[str, float]:
        return {
            "home_win": self.fifa_sum_home_win_probability,
            "draw": self.fifa_sum_draw_probability,
            "away_win": self.fifa_sum_away_win_probability,
        }


def rolling_origin_backtest(
    *,
    matches: tuple[OfficialMatchRecord, ...],
    as_of_date: date,
    evaluation_months: int = 12,
    lookback_months: int = 24,
    half_life_days: int = 180,
    min_prior_matches: int = 2,
    bin_count: int = 10,
) -> dict[str, Any]:
    played = tuple(
        sorted(
            (match for match in matches if match.is_played),
            key=lambda item: (parse_record_date(item.match_date), item.match_id),
        )
    )
    evaluation_start = _add_months(as_of_date, -evaluation_months)
    samples: list[MatchBacktestSample] = []

    for target in played:
        target_date = parse_record_date(target.match_date)
        if not (evaluation_start <= target_date < as_of_date):
            continue
        if target.home_score is None or target.away_score is None:
            continue
        lookback_start = _add_months(target_date, -lookback_months)
        prior = tuple(
            match
            for match in played
            if lookback_start <= parse_record_date(match.match_date) < target_date
        )
        home_prior = _count_team_matches(prior, target.home_team)
        away_prior = _count_team_matches(prior, target.away_team)
        if home_prior < min_prior_matches or away_prior < min_prior_matches:
            continue

        ratings = {
            target.home_team: _team_rating(
                team=target.home_team,
                prior_matches=prior,
                as_of_date=target_date,
                half_life_days=half_life_days,
            ),
            target.away_team: _team_rating(
                team=target.away_team,
                prior_matches=prior,
                as_of_date=target_date,
                half_life_days=half_life_days,
            ),
        }
        model = three_way_baseline(
            ratings[target.home_team], ratings[target.away_team]
        )
        baseline = three_way_baseline(1500.0, 1500.0)
        fifa_sum_ratings = _fifa_sum_ratings(prior)
        fifa_sum = three_way_baseline(
            fifa_sum_ratings.get(target.home_team, 1500.0),
            fifa_sum_ratings.get(target.away_team, 1500.0),
        )
        prediction = {
            "home_win": model["win"],
            "draw": model["draw"],
            "away_win": model["loss"],
        }
        predicted_label = max(
            MATCH_OUTCOME_LABELS, key=lambda label: (prediction[label], label)
        )
        outcome = _match_outcome(target.home_score, target.away_score)
        samples.append(
            MatchBacktestSample(
                match_id=target.match_id,
                match_date=target.match_date,
                home_team=target.home_team,
                away_team=target.away_team,
                outcome=outcome,
                home_score=target.home_score,
                away_score=target.away_score,
                home_win_probability=prediction["home_win"],
                draw_probability=prediction["draw"],
                away_win_probability=prediction["away_win"],
                baseline_home_win_probability=baseline["win"],
                baseline_draw_probability=baseline["draw"],
                baseline_away_win_probability=baseline["loss"],
                fifa_sum_home_win_probability=fifa_sum["win"],
                fifa_sum_draw_probability=fifa_sum["draw"],
                fifa_sum_away_win_probability=fifa_sum["loss"],
                predicted_label=predicted_label,
                predicted_confidence=prediction[predicted_label],
                prediction_correct=predicted_label == outcome,
                prior_home_matches=home_prior,
                prior_away_matches=away_prior,
            )
        )

    if not samples:
        raise ValueError("Backtest produced no samples; relax date window or min_prior_matches.")

    model_predictions = [sample.model_prediction for sample in samples]
    baseline_predictions = [sample.baseline_prediction for sample in samples]
    fifa_sum_predictions = [sample.fifa_sum_prediction for sample in samples]
    outcomes = [sample.outcome for sample in samples]
    model_metrics = _multiclass_metrics(model_predictions, outcomes)
    baseline_metrics = _multiclass_metrics(baseline_predictions, outcomes)
    fifa_sum_metrics = _multiclass_metrics(fifa_sum_predictions, outcomes)
    confidence_bins = calibration_bins(
        [sample.predicted_confidence for sample in samples],
        [1 if sample.prediction_correct else 0 for sample in samples],
        bin_count=bin_count,
    )

    return {
        "model_name": "recency_weighted_1x2_baseline",
        "baseline_name": "equal_strength_1x2_baseline",
        "primary_baseline_name": "fifa_sum_style_elo_baseline",
        "primary_baseline_source": "FIFA/Coca-Cola World Ranking SUM methodology; computed locally from FIFA match records",
        "as_of_date": as_of_date.isoformat(),
        "evaluation_start": evaluation_start.isoformat(),
        "evaluation_months": evaluation_months,
        "lookback_months": lookback_months,
        "half_life_days": half_life_days,
        "min_prior_matches": min_prior_matches,
        "sample_count": len(samples),
        "labels": list(MATCH_OUTCOME_LABELS),
        "temporal_validation": {
            "method": "rolling_origin",
            "leakage_rule": "training matches must be strictly before target match date",
        },
        "metrics": model_metrics,
        "baseline_metrics": baseline_metrics,
        "baseline_comparison": {
            "brier_delta": model_metrics["brier_score"] - baseline_metrics["brier_score"],
            "log_loss_delta": model_metrics["log_loss"] - baseline_metrics["log_loss"],
            "accuracy_delta": model_metrics["accuracy"] - baseline_metrics["accuracy"],
        },
        "primary_baseline_metrics": fifa_sum_metrics,
        "primary_baseline_comparison": {
            "brier_delta": model_metrics["brier_score"] - fifa_sum_metrics["brier_score"],
            "log_loss_delta": model_metrics["log_loss"] - fifa_sum_metrics["log_loss"],
            "accuracy_delta": model_metrics["accuracy"] - fifa_sum_metrics["accuracy"],
        },
        "baselines": {
            "equal_strength": {
                "name": "equal_strength_1x2_baseline",
                "role": "minimum sanity floor",
                "metrics": baseline_metrics,
                "comparison": {
                    "brier_delta": model_metrics["brier_score"] - baseline_metrics["brier_score"],
                    "log_loss_delta": model_metrics["log_loss"] - baseline_metrics["log_loss"],
                    "accuracy_delta": model_metrics["accuracy"] - baseline_metrics["accuracy"],
                },
            },
            "fifa_sum_style": {
                "name": "fifa_sum_style_elo_baseline",
                "role": "primary public benchmark",
                "source": "FIFA/Coca-Cola World Ranking SUM methodology",
                "license_policy": "No external table is redistributed; ratings are computed locally from official FIFA match records already stored by the pipeline.",
                "metrics": fifa_sum_metrics,
                "comparison": {
                    "brier_delta": model_metrics["brier_score"] - fifa_sum_metrics["brier_score"],
                    "log_loss_delta": model_metrics["log_loss"] - fifa_sum_metrics["log_loss"],
                    "accuracy_delta": model_metrics["accuracy"] - fifa_sum_metrics["accuracy"],
                },
            },
        },
        "calibration": {
            "type": "predicted_label_confidence",
            "expected_calibration_error": expected_calibration_error(confidence_bins),
            "maximum_calibration_error": maximum_calibration_error(confidence_bins),
            "bins": [item.to_json_dict() for item in confidence_bins],
        },
        "samples": [sample.to_json_dict() for sample in samples],
    }


def _multiclass_metrics(
    predictions: list[dict[str, float]], outcomes: list[str]
) -> dict[str, float]:
    return {
        "brier_score": multiclass_brier_score(
            predictions, outcomes, labels=MATCH_OUTCOME_LABELS
        ),
        "log_loss": multiclass_log_loss(
            predictions, outcomes, labels=MATCH_OUTCOME_LABELS
        ),
        "accuracy": classification_accuracy(
            predictions, outcomes, labels=MATCH_OUTCOME_LABELS
        ),
    }


def _team_rating(
    *,
    team: str,
    prior_matches: tuple[OfficialMatchRecord, ...],
    as_of_date: date,
    half_life_days: int,
) -> float:
    rating = 1500.0
    for match in prior_matches:
        if match.home_score is None or match.away_score is None:
            continue
        if team not in (match.home_team, match.away_team):
            continue
        match_date = parse_record_date(match.match_date)
        weight = exponential_decay_weight(
            match_date, as_of_date=as_of_date, half_life_days=half_life_days
        )
        importance = _importance_weight(match.match_importance)
        if team == match.home_team:
            scored = match.home_score
            conceded = match.away_score
        else:
            scored = match.away_score
            conceded = match.home_score
        points = _points(scored, conceded)
        goal_difference = scored - conceded
        rating += points * 35.0 * weight * importance
        rating += goal_difference * 12.0 * weight * importance
        rating += scored * 3.5 * weight * importance
    return rating


def _fifa_sum_ratings(matches: tuple[OfficialMatchRecord, ...]) -> dict[str, float]:
    ratings: dict[str, float] = {}
    for match in sorted(matches, key=lambda item: (parse_record_date(item.match_date), item.match_id)):
        if match.home_score is None or match.away_score is None:
            continue
        home = match.home_team
        away = match.away_team
        home_rating = ratings.get(home, 1500.0)
        away_rating = ratings.get(away, 1500.0)
        home_expected = _fifa_sum_expected_score(home_rating, away_rating)
        home_actual = _actual_score(match.home_score, match.away_score)
        weight = _fifa_sum_importance(match.match_importance)
        delta = weight * (home_actual - home_expected)
        ratings[home] = home_rating + delta
        ratings[away] = away_rating - delta
    return ratings


def _fifa_sum_expected_score(team_rating: float, opponent_rating: float) -> float:
    rating_difference = team_rating - opponent_rating
    return 1 / (10 ** (-rating_difference / 600) + 1)


def _actual_score(scored: int, conceded: int) -> float:
    if scored > conceded:
        return 1.0
    if scored < conceded:
        return 0.0
    return 0.5


def _count_team_matches(matches: tuple[OfficialMatchRecord, ...], team: str) -> int:
    return sum(1 for match in matches if team in (match.home_team, match.away_team))


def _match_outcome(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "home_win"
    if home_score < away_score:
        return "away_win"
    return "draw"


def _points(scored: int, conceded: int) -> int:
    if scored > conceded:
        return 3
    if scored < conceded:
        return 0
    return 1


def _importance_weight(match_importance: str) -> float:
    weights = {
        "friendly": 0.75,
        "nations_league": 1.0,
        "official_or_other": 1.0,
        "world_cup_qualifier": 1.25,
        "continental_final_competition": 1.35,
        "world_cup": 1.60,
    }
    return weights.get(match_importance, 1.0)


def _fifa_sum_importance(match_importance: str) -> float:
    weights = {
        "friendly": 10.0,
        "nations_league": 15.0,
        "official_or_other": 25.0,
        "world_cup_qualifier": 25.0,
        "continental_final_competition": 35.0,
        "world_cup": 50.0,
    }
    return weights.get(match_importance, 25.0)


def _add_months(value: date, months: int) -> date:
    month = value.month - 1 + months
    year = value.year + month // 12
    month = month % 12 + 1
    day = min(day_count(year, month), value.day)
    return date(year, month, day)


def day_count(year: int, month: int) -> int:
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return 29 if leap else 28
    if month in {4, 6, 9, 11}:
        return 30
    return 31
