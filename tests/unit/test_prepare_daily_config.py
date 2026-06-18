from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_daily_config import prepare_daily_config


class PrepareDailyConfigTest(unittest.TestCase):
    def test_prepare_daily_config_overrides_daily_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_config = root / "base.json"
            output_config = root / ".generated" / "daily.json"
            base_config.write_text(
                json.dumps(
                    {
                        "run_id": "fifa-real-2026-06-18",
                        "as_of_date": "2026-06-18",
                        "project_github_url": "https://github.com/old/repo",
                        "official_fifa": {
                            "raw_output_dir": "data/raw/fifa",
                            "sources": [
                                {
                                    "source_id": "fixtures",
                                    "url": "tests/fixtures/fifa/sample_competition_state.json",
                                    "purpose": "fixtures",
                                }
                            ],
                        },
                        "feature_windows": {"current_months": 12, "max_months": 24},
                        "simulation": {"tournament_ruleset": "fifa-world-cup-2026"},
                        "site": {"output_dir": "public"},
                    }
                ),
                encoding="utf-8",
            )

            payload = prepare_daily_config(
                config_path=base_config,
                output_path=output_config,
                as_of_date="2026-06-20",
                github_url="https://github.com/example/copa",
            )

            written = json.loads(output_config.read_text(encoding="utf-8"))
            self.assertEqual(payload["as_of_date"], "2026-06-20")
            self.assertEqual(payload["run_id"], "fifa-real-2026-06-20")
            self.assertEqual(payload["project_github_url"], "https://github.com/example/copa")
            self.assertEqual(written, payload)

    def test_prepare_daily_config_preserves_explicit_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_config = root / "base.json"
            output_config = root / "daily.json"
            base_config.write_text(
                json.dumps(
                    {
                        "run_id": "base",
                        "as_of_date": "2026-06-18",
                        "project_github_url": "https://github.com/example/copa",
                        "official_fifa": {
                            "raw_output_dir": "data/raw/fifa",
                            "sources": [
                                {
                                    "source_id": "fixtures",
                                    "url": "tests/fixtures/fifa/sample_competition_state.json",
                                    "purpose": "fixtures",
                                }
                            ],
                        },
                        "feature_windows": {"current_months": 12, "max_months": 24},
                        "simulation": {"tournament_ruleset": "fifa-world-cup-2026"},
                        "site": {"output_dir": "public"},
                    }
                ),
                encoding="utf-8",
            )

            payload = prepare_daily_config(
                config_path=base_config,
                output_path=output_config,
                as_of_date="2026-06-20",
                run_id="manual-review",
            )

            self.assertEqual(payload["run_id"], "manual-review")


if __name__ == "__main__":
    unittest.main()
