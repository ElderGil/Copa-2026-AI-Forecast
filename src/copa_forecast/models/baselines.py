from __future__ import annotations

import math


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

