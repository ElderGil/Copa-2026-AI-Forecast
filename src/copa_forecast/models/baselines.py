from __future__ import annotations

import math

from copa_forecast.data.contracts import OfficialMatchRecord
from copa_forecast.features.leakage import parse_record_date


def elo_expected_score(team_rating: float, opponent_rating: float) -> float:
    return 1 / (1 + math.pow(10, (opponent_rating - team_rating) / 400))


def three_way_baseline(
    team_rating: float, opponent_rating: float, *, draw_probability: float = 0.26
) -> dict[str, float]:
    win_share = elo_expected_score(team_rating, opponent_rating)
    decisive = 1 - draw_probability
    return {
        "win": win_share * decisive,
        "draw": draw_probability,
        "loss": (1 - win_share) * decisive,
    }


def fifa_sum_ratings(matches: tuple[OfficialMatchRecord, ...]) -> dict[str, float]:
    """Compute a local FIFA SUM-style rating table from match records."""

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
        weight = fifa_sum_importance(match.match_importance)
        delta = weight * (home_actual - home_expected)
        ratings[home] = home_rating + delta
        ratings[away] = away_rating - delta
    return ratings


def fifa_sum_importance(match_importance: str) -> float:
    weights = {
        "friendly": 10.0,
        "nations_league": 15.0,
        "official_or_other": 25.0,
        "world_cup_qualifier": 25.0,
        "continental_final_competition": 35.0,
        "world_cup": 50.0,
    }
    return weights.get(match_importance, 25.0)


def _fifa_sum_expected_score(team_rating: float, opponent_rating: float) -> float:
    rating_difference = team_rating - opponent_rating
    return 1 / (10 ** (-rating_difference / 600) + 1)


def _actual_score(scored: int, conceded: int) -> float:
    if scored > conceded:
        return 1.0
    if scored < conceded:
        return 0.0
    return 0.5
