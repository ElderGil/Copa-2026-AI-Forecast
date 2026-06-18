from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScheduleAdjustedRates:
    points_per_match: float
    goals_for_per_match: float
    goals_against_per_match: float
    goal_difference_per_match: float
    average_opponent_rating: float
    schedule_strength_adjustment: float


def adjust_rates_for_schedule_strength(
    *,
    points_per_match: float,
    goals_for_per_match: float,
    goals_against_per_match: float,
    goal_difference_per_match: float,
    average_opponent_rating: float,
) -> ScheduleAdjustedRates:
    """Adjust recent-form rates by average opponent strength.

    The correction is deliberately bounded. It should reduce obvious schedule
    bias without allowing the prior rating to dominate current-form evidence.
    """

    schedule_adjustment = bounded_schedule_strength_adjustment(average_opponent_rating)
    return ScheduleAdjustedRates(
        points_per_match=max(0.0, points_per_match + schedule_adjustment * 0.35),
        goals_for_per_match=max(0.0, goals_for_per_match + schedule_adjustment * 0.40),
        goals_against_per_match=max(0.0, goals_against_per_match - schedule_adjustment * 0.20),
        goal_difference_per_match=goal_difference_per_match + schedule_adjustment * 0.80,
        average_opponent_rating=average_opponent_rating,
        schedule_strength_adjustment=schedule_adjustment,
    )


def bounded_schedule_strength_adjustment(average_opponent_rating: float) -> float:
    raw_adjustment = (average_opponent_rating - 1500.0) / 400.0
    return min(0.35, max(-0.35, raw_adjustment))
