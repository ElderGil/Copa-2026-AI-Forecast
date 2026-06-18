from __future__ import annotations

import unittest

from copa_forecast.reporting.explanations import (
    build_explanation_payload,
    compare_forecast_runs,
)


class RunComparisonTest(unittest.TestCase):
    def test_compares_rank_and_probability_deltas(self) -> None:
        previous = {
            "run_id": "previous",
            "as_of_date": "2026-06-18",
            "teams": [
                {"team": "Brazil", "rank": 2, "champion_probability": 0.20},
                {"team": "Mexico", "rank": 1, "champion_probability": 0.30},
            ],
        }
        current = {
            "run_id": "current",
            "as_of_date": "2026-06-19",
            "teams": [
                {"team": "Brazil", "rank": 1, "champion_probability": 0.25},
                {"team": "Mexico", "rank": 2, "champion_probability": 0.28},
            ],
        }

        comparison = compare_forecast_runs(previous=previous, current=current)
        brazil = [
            item for item in comparison["team_deltas"] if item["team"] == "Brazil"
        ][0]

        self.assertEqual(comparison["previous_run_id"], "previous")
        self.assertEqual(comparison["current_run_id"], "current")
        self.assertEqual(brazil["rank_delta"], 1)
        self.assertAlmostEqual(brazil["champion_probability_delta"], 0.05)

    def test_builds_team_filtered_explanation_payload(self) -> None:
        latest = {
            "run_id": "current",
            "as_of_date": "2026-06-19",
            "pillars": [],
            "teams": [
                {
                    "team": "Brazil",
                    "rank": 1,
                    "champion_probability": 0.25,
                    "advancement_probabilities": {"final": 0.50},
                    "tournament_signal": {"points": 3, "goal_difference": 1},
                    "strength": 120,
                    "used_pillars": ["official_competition_state"],
                    "excluded_pillars": ["recent_form_window"],
                }
            ],
        }

        payload = build_explanation_payload(latest, team="Brazil")

        self.assertEqual(payload["team_count"], 1)
        self.assertEqual(payload["teams"][0]["team"], "Brazil")
        self.assertIn("chance_final=0.5000", payload["teams"][0]["drivers"])


if __name__ == "__main__":
    unittest.main()
