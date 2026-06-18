from __future__ import annotations

import unittest
from pathlib import Path

from copa_forecast.data.sources.fifa import JsonFifaParser


class FifaParserTest(unittest.TestCase):
    def test_parser_normalizes_fixture_payload(self) -> None:
        payload = Path("tests/fixtures/fifa/sample_competition_state.json").read_bytes()
        parsed = JsonFifaParser().parse(payload)
        self.assertEqual(len(parsed.teams), 4)
        self.assertEqual(len(parsed.fixtures), 2)
        self.assertEqual(parsed.fixtures[0].status, "completed")
        self.assertEqual(parsed.fixtures[0].home_score, 2)


if __name__ == "__main__":
    unittest.main()

