from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from copa_forecast.data.contracts import OfficialMatchRecord, Team
from copa_forecast.features.leakage import parse_record_date
from copa_forecast.features.windows import exponential_decay_weight


@dataclass(frozen=True)
class RecentTeamFeatures:
    team: str
    matches_24m: int = 0
    matches_12m: int = 0
    weighted_points: float = 0.0
    weighted_goals_for: float = 0.0
    weighted_goals_against: float = 0.0
    weighted_importance: float = 0.0
    weighted_opponent_rating: float = 0.0
    home_matches: int = 0
    away_matches: int = 0
    neutral_matches: int = 0

    @property
    def weighted_goal_difference(self) -> float:
        return self.weighted_goals_for - self.weighted_goals_against

    @property
    def average_opponent_rating(self) -> float:
        if self.weighted_importance <= 0:
            return 1500.0
        return self.weighted_opponent_rating / self.weighted_importance


def build_recent_team_features(
    *,
    teams: tuple[Team, ...],
    matches: tuple[OfficialMatchRecord, ...],
    as_of_date: date,
    current_window_months: int,
    max_window_months: int,
    half_life_days: int,
    opponent_ratings: dict[str, float] | None = None,
) -> dict[str, RecentTeamFeatures]:
    current_start = _add_months(as_of_date, -current_window_months)
    max_start = _add_months(as_of_date, -max_window_months)
    accumulators = {team.name: _MutableRecentFeatures(team.name) for team in teams}
    opponent_ratings = opponent_ratings or {}
    for match in matches:
        match_date = parse_record_date(match.match_date)
        if not (max_start <= match_date < as_of_date):
            continue
        if match.home_score is None or match.away_score is None:
            continue
        weight = exponential_decay_weight(
            match_date, as_of_date=as_of_date, half_life_days=half_life_days
        )
        importance = _importance_weight(match.match_importance)
        _apply_match(
            accumulators,
            team=match.home_team,
            points=_points(match.home_score, match.away_score),
            goals_for=match.home_score,
            goals_against=match.away_score,
            weight=weight,
            importance=importance,
            opponent_rating=opponent_ratings.get(match.away_team, 1500.0),
            venue_context=match.venue_context,
            in_current_window=match_date >= current_start,
            listed_home=True,
        )
        _apply_match(
            accumulators,
            team=match.away_team,
            points=_points(match.away_score, match.home_score),
            goals_for=match.away_score,
            goals_against=match.home_score,
            weight=weight,
            importance=importance,
            opponent_rating=opponent_ratings.get(match.home_team, 1500.0),
            venue_context=match.venue_context,
            in_current_window=match_date >= current_start,
            listed_home=False,
        )
    return {team: item.to_features() for team, item in accumulators.items()}


class _MutableRecentFeatures:
    def __init__(self, team: str) -> None:
        self.team = team
        self.matches_24m = 0
        self.matches_12m = 0
        self.weighted_points = 0.0
        self.weighted_goals_for = 0.0
        self.weighted_goals_against = 0.0
        self.weighted_importance = 0.0
        self.weighted_opponent_rating = 0.0
        self.home_matches = 0
        self.away_matches = 0
        self.neutral_matches = 0

    def to_features(self) -> RecentTeamFeatures:
        return RecentTeamFeatures(
            team=self.team,
            matches_24m=self.matches_24m,
            matches_12m=self.matches_12m,
            weighted_points=self.weighted_points,
            weighted_goals_for=self.weighted_goals_for,
            weighted_goals_against=self.weighted_goals_against,
            weighted_importance=self.weighted_importance,
            weighted_opponent_rating=self.weighted_opponent_rating,
            home_matches=self.home_matches,
            away_matches=self.away_matches,
            neutral_matches=self.neutral_matches,
        )


def _apply_match(
    accumulators: dict[str, _MutableRecentFeatures],
    *,
    team: str,
    points: int,
    goals_for: int,
    goals_against: int,
    weight: float,
    importance: float,
    opponent_rating: float,
    venue_context: str,
    in_current_window: bool,
    listed_home: bool,
) -> None:
    if team not in accumulators:
        return
    item = accumulators[team]
    item.matches_24m += 1
    item.matches_12m += 1 if in_current_window else 0
    match_weight = weight * importance
    item.weighted_points += points * match_weight
    item.weighted_goals_for += goals_for * match_weight
    item.weighted_goals_against += goals_against * match_weight
    item.weighted_importance += match_weight
    item.weighted_opponent_rating += opponent_rating * match_weight
    if venue_context == "neutral":
        item.neutral_matches += 1
    elif listed_home:
        item.home_matches += 1
    else:
        item.away_matches += 1


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


def _add_months(value: date, months: int) -> date:
    month = value.month - 1 + months
    year = value.year + month // 12
    month = month % 12 + 1
    day = min(value.day, _days_in_month(year, month))
    return date(year, month, day)


def _days_in_month(year: int, month: int) -> int:
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return 29 if leap else 28
    if month in {4, 6, 9, 11}:
        return 30
    return 31
