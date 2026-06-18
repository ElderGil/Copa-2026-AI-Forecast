from __future__ import annotations

import unittest
from pathlib import Path

from copa_forecast.data.sources.fifa import FifaCalendarMatchParser, JsonFifaParser


class FifaParserTest(unittest.TestCase):
    def test_parser_normalizes_fixture_payload(self) -> None:
        payload = Path("tests/fixtures/fifa/sample_competition_state.json").read_bytes()
        parsed = JsonFifaParser().parse(payload)
        self.assertEqual(len(parsed.teams), 4)
        self.assertEqual(len(parsed.fixtures), 2)
        self.assertEqual(parsed.fixtures[0].status, "completed")
        self.assertEqual(parsed.fixtures[0].home_score, 2)

    def test_calendar_parser_keeps_senior_mens_national_matches(self) -> None:
        payload = Path("tests/fixtures/fifa/recent_BRA.json").read_bytes()
        matches = FifaCalendarMatchParser().parse_matches(
            payload,
            source_id="fifa-calendar-team-matches",
            source_url="tests/fixtures/fifa/recent_BRA.json",
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].home_team, "Brazil")
        self.assertEqual(matches[0].away_team, "Morocco")
        self.assertEqual(matches[0].match_importance, "friendly")
        self.assertEqual(matches[0].venue_context, "neutral")


if __name__ == "__main__":
    unittest.main()
