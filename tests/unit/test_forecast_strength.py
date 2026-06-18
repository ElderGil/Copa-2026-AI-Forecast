from __future__ import annotations

import unittest

from copa_forecast.data.contracts import Team
from copa_forecast.features.recent import RecentTeamFeatures
from copa_forecast.forecast import TeamTournamentSignal, build_team_strengths


class ForecastStrengthTest(unittest.TestCase):
    def test_recent_strength_uses_rates_instead_of_raw_match_volume(self) -> None:
        strengths = build_team_strengths(
            (
                Team(team_id="A", name="Short Sample"),
                Team(team_id="B", name="Long Sample"),
            ),
            signals={
                "Short Sample": TeamTournamentSignal(),
                "Long Sample": TeamTournamentSignal(),
            },
            included_pillars={
                "recent_form_window",
                "attacking_trend",
                "defensive_trend",
                "match_importance",
            },
            recent_features={
                "Short Sample": RecentTeamFeatures(
                    team="Short Sample",
                    matches_24m=5,
                    weighted_points=7.5,
                    weighted_goals_for=5.0,
                    weighted_goals_against=2.5,
                    weighted_importance=5.0,
                ),
                "Long Sample": RecentTeamFeatures(
                    team="Long Sample",
                    matches_24m=25,
                    weighted_points=37.5,
                    weighted_goals_for=25.0,
                    weighted_goals_against=12.5,
                    weighted_importance=25.0,
                ),
            },
        )

        self.assertLess(strengths["Long Sample"] - strengths["Short Sample"], 35.0)

    def test_opponent_strength_adjustment_separates_identical_raw_form(self) -> None:
        strengths = build_team_strengths(
            (
                Team(team_id="A", name="Strong Schedule"),
                Team(team_id="B", name="Weak Schedule"),
            ),
            signals={
                "Strong Schedule": TeamTournamentSignal(),
                "Weak Schedule": TeamTournamentSignal(),
            },
            included_pillars={
                "recent_form_window",
                "attacking_trend",
                "defensive_trend",
                "opponent_strength_context",
            },
            recent_features={
                "Strong Schedule": RecentTeamFeatures(
                    team="Strong Schedule",
                    matches_24m=8,
                    weighted_points=16.0,
                    weighted_goals_for=16.0,
                    weighted_goals_against=8.0,
                    weighted_importance=8.0,
                    weighted_opponent_rating=1600.0 * 8.0,
                ),
                "Weak Schedule": RecentTeamFeatures(
                    team="Weak Schedule",
                    matches_24m=8,
                    weighted_points=16.0,
                    weighted_goals_for=16.0,
                    weighted_goals_against=8.0,
                    weighted_importance=8.0,
                    weighted_opponent_rating=1400.0 * 8.0,
                ),
            },
        )

        self.assertGreater(strengths["Strong Schedule"], strengths["Weak Schedule"])


if __name__ == "__main__":
    unittest.main()
