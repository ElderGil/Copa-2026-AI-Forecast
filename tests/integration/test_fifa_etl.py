from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from copa_forecast.config import parse_config
from copa_forecast.data.ingest import build_competition_state, persist_raw_extract
from copa_forecast.data.recent_matches import run_recent_match_etl
from copa_forecast.data.sources.fifa import JsonFifaParser
from copa_forecast.data.validate import require_non_empty_state


class FifaEtlIntegrationTest(unittest.TestCase):
    def test_cached_payload_becomes_official_state(self) -> None:
        payload = Path("tests/fixtures/fifa/sample_competition_state.json").read_bytes()
        parser = JsonFifaParser()
        with tempfile.TemporaryDirectory() as tmp:
            extract = persist_raw_extract(
                source_id="fixtures",
                source_url="file://tests/fixtures/fifa/sample_competition_state.json",
                payload=payload,
                output_dir=tmp,
                parser_version=parser.parser_version,
                retrieved_at=datetime(2026, 6, 18, tzinfo=UTC),
            )
            state = build_competition_state(
                extract=extract, as_of_date="2026-06-18", parser=parser
            )
            require_non_empty_state(state)
            self.assertTrue(state.is_official)
            self.assertEqual(len(state.fixtures), 2)

    def test_recent_match_etl_writes_processed_matches_and_coverage(self) -> None:
        payload = Path("tests/fixtures/fifa/sample_competition_state.json").read_bytes()
        parser = JsonFifaParser()
        recent_template = Path("tests/fixtures/fifa/recent_{team_id}.json").resolve()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            extract = persist_raw_extract(
                source_id="fixtures",
                source_url="file://tests/fixtures/fifa/sample_competition_state.json",
                payload=payload,
                output_dir=root / "raw" / "fifa",
                parser_version=parser.parser_version,
                retrieved_at=datetime(2026, 6, 18, tzinfo=UTC),
            )
            state = build_competition_state(
                extract=extract, as_of_date="2026-06-18", parser=parser
            )
            config = parse_config(
                {
                    "run_id": "recent-etl-test",
                    "as_of_date": "2026-06-18",
                    "project_github_url": "https://github.com/example/copa",
                    "official_fifa": {
                        "raw_output_dir": str(root / "raw" / "fifa"),
                        "sources": [
                            {
                                "source_id": "sample-fifa-fixtures",
                                "url": str(Path("tests/fixtures/fifa/sample_competition_state.json").resolve()),
                                "purpose": "fixtures",
                            }
                        ],
                    },
                    "recent_matches": {
                        "raw_output_dir": str(root / "raw" / "recent"),
                        "processed_output_dir": str(root / "processed" / "recent"),
                        "sources": [
                            {
                                "source_id": "fifa-calendar-team-matches",
                                "authority": "FIFA",
                                "url_template": str(recent_template),
                            }
                        ],
                    },
                    "feature_windows": {"current_months": 12, "max_months": 24},
                    "simulation": {"tournament_ruleset": "fifa-world-cup-2026"},
                    "site": {"output_dir": str(root / "public")},
                }
            )

            result = run_recent_match_etl(
                config=config,
                state=state,
                retrieved_at=datetime(2026, 6, 18, tzinfo=UTC),
            )

            self.assertEqual(len(result.matches), 2)
            self.assertTrue(result.output_json.exists())
            self.assertTrue(result.output_csv.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertEqual(result.coverage["teams_with_max_window_matches"], 4)
            self.assertEqual(result.coverage["max_window_coverage"], 1.0)


if __name__ == "__main__":
    unittest.main()
