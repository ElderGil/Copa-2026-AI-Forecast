from __future__ import annotations

import unittest

from copa_forecast.config import ConfigError, parse_config


class ForecastConfigTest(unittest.TestCase):
    def test_requires_fifa_source(self) -> None:
        with self.assertRaises(ConfigError):
            parse_config(
                {
                    "run_id": "bad",
                    "as_of_date": "2026-06-18",
                    "project_github_url": "https://github.com/example/repo",
                    "official_fifa": {"sources": [], "raw_output_dir": "data/raw/fifa"},
                    "feature_windows": {"current_months": 12, "max_months": 24},
                    "simulation": {"tournament_ruleset": "fifa-world-cup-2026"},
                    "site": {"output_dir": "public"},
                }
            )

    def test_parses_valid_config(self) -> None:
        config = parse_config(
            {
                "run_id": "ok",
                "as_of_date": "2026-06-18",
                "project_github_url": "https://github.com/example/repo",
                "official_fifa": {
                    "sources": [
                        {
                            "source_id": "fixtures",
                            "url": "tests/fixtures/fifa/sample_competition_state.json",
                            "purpose": "fixtures",
                        }
                    ],
                    "raw_output_dir": "data/raw/fifa",
                },
                "feature_windows": {"current_months": 12, "max_months": 24},
                "simulation": {"tournament_ruleset": "fifa-world-cup-2026"},
                "site": {"output_dir": "public"},
            }
        )
        self.assertEqual(config.run_id, "ok")
        self.assertEqual(config.official_fifa.sources[0].source_id, "fixtures")
        self.assertEqual(config.recent_matches.sources[0].source_id, "fifa-calendar-team-matches")
        self.assertEqual(config.recent_matches.raw_output_dir.as_posix(), "data/raw/fifa_recent_matches")
        self.assertFalse(config.recent_matches.declared)

    def test_marks_recent_matches_when_declared(self) -> None:
        config = parse_config(
            {
                "run_id": "ok",
                "as_of_date": "2026-06-18",
                "project_github_url": "https://github.com/example/repo",
                "official_fifa": {
                    "sources": [
                        {
                            "source_id": "fixtures",
                            "url": "tests/fixtures/fifa/sample_competition_state.json",
                            "purpose": "fixtures",
                        }
                    ],
                    "raw_output_dir": "data/raw/fifa",
                },
                "recent_matches": {
                    "processed_output_dir": "data/processed/recent_matches",
                    "sources": [
                        {
                            "source_id": "fifa-calendar-team-matches",
                            "authority": "FIFA",
                            "url_template": "tests/fixtures/fifa/recent_{team_id}.json",
                        }
                    ],
                },
                "feature_windows": {"current_months": 12, "max_months": 24},
                "simulation": {"tournament_ruleset": "fifa-world-cup-2026"},
                "site": {"output_dir": "public"},
            }
        )

        self.assertTrue(config.recent_matches.declared)


if __name__ == "__main__":
    unittest.main()
