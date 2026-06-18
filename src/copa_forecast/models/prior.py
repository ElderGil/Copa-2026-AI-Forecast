from __future__ import annotations

from copa_forecast.data.contracts import OfficialMatchRecord
from copa_forecast.features.leakage import parse_record_date
from copa_forecast.models.baselines import fifa_sum_importance

BASE_RATING = 1500.0


def global_elo_ratings(
    matches: tuple[OfficialMatchRecord, ...],
    *,
    max_epochs: int = 60,
    base_k: float = 10.0,
    epoch_decay: float = 0.15,
    convergence: float = 0.75,
) -> dict[str, float]:
    """Opponent-quality-aware strength prior via an iterative Elo.

    Unlike a single chronological pass (which cold-starts every team at 1500 and
    cannot discount beating weak opponents), this repeats epochs over the whole
    match set with a per-epoch-decaying K. The ratings converge to a stable
    spread that reflects the win/loss network: beating a low-rated team yields a
    high expected score and therefore little gain. The prior is venue-neutral and
    undecayed in time — recency is captured separately by the recent-form
    features, so this stands in for relative pedigree over the ingested window.
    """

    played = sorted(
        (match for match in matches if match.is_played),
        key=lambda match: (parse_record_date(match.match_date), match.match_id),
    )
    ratings: dict[str, float] = {}
    if not played:
        return ratings

    for epoch in range(max_epochs):
        k_scale = base_k / (1 + epoch * epoch_decay)
        max_delta = 0.0
        for match in played:
            home, away = match.home_team, match.away_team
            home_rating = ratings.get(home, BASE_RATING)
            away_rating = ratings.get(away, BASE_RATING)
            expected_home = 1 / (1 + 10 ** ((away_rating - home_rating) / 400))
            actual_home = _actual_score(match.home_score, match.away_score)
            weight = (
                k_scale
                * (fifa_sum_importance(match.match_importance) / 25.0)
                * _margin_multiplier(match.home_score, match.away_score)
            )
            delta = weight * (actual_home - expected_home)
            ratings[home] = home_rating + delta
            ratings[away] = away_rating - delta
            max_delta = max(max_delta, abs(delta))
        if max_delta < convergence:
            break
    return ratings


def _actual_score(home_score: int | None, away_score: int | None) -> float:
    if home_score is None or away_score is None:
        return 0.5
    if home_score > away_score:
        return 1.0
    if home_score < away_score:
        return 0.0
    return 0.5


def _margin_multiplier(home_score: int | None, away_score: int | None) -> float:
    if home_score is None or away_score is None:
        return 1.0
    return 1.0 + min(abs(home_score - away_score), 4) * 0.15
