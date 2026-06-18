from __future__ import annotations

import unittest

from copa_forecast.reporting.explanations import build_team_explanation


class ExplanationTest(unittest.TestCase):
    def test_builds_used_and_excluded_pillar_summary(self) -> None:
        explanation = build_team_explanation(
            team="Brazil",
            used_pillars=["official_competition_state", "tournament_path"],
            excluded_pillars=["recent_form_window"],
            drivers=["chance_titulo=0.2500"],
        )

        self.assertEqual(explanation.team, "Brazil")
        self.assertEqual(
            explanation.used_pillars,
            ("official_competition_state", "tournament_path"),
        )
        self.assertIn("2 pilares usados", explanation.summary)
        self.assertIn("1 pilares excluidos", explanation.summary)
        self.assertEqual(explanation.drivers, ("chance_titulo=0.2500",))


if __name__ == "__main__":
    unittest.main()
