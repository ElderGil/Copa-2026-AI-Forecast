from __future__ import annotations

import unittest

from copa_forecast.reporting.countries import display_team_name, flag_emoji


class CountryPresentationTest(unittest.TestCase):
    def test_localizes_fifa_team_names_to_portuguese_display(self) -> None:
        self.assertEqual(display_team_name("Côte d'Ivoire"), "Costa do Marfim")
        self.assertEqual(display_team_name("Germany"), "Alemanha")

    def test_builds_flag_emoji_from_fifa_code(self) -> None:
        self.assertEqual(flag_emoji("BRA"), "🇧🇷")
        self.assertEqual(flag_emoji("CIV"), "🇨🇮")


if __name__ == "__main__":
    unittest.main()
