from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from copa_forecast.data.ingest import build_competition_state, persist_raw_extract
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
                retrieved_at=datetime(2026, 6, 18, tzinfo=timezone.utc),
            )
            state = build_competition_state(
                extract=extract, as_of_date="2026-06-18", parser=parser
            )
            require_non_empty_state(state)
            self.assertTrue(state.is_official)
            self.assertEqual(len(state.fixtures), 2)


if __name__ == "__main__":
    unittest.main()
