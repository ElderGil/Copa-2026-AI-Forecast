from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from copa_forecast.data.ingest import persist_raw_extract


class FifaRawStoreTest(unittest.TestCase):
    def test_persists_payload_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            extract = persist_raw_extract(
                source_id="fixtures",
                source_url="https://www.fifa.com/example",
                payload=b'{"fixtures":[]}',
                output_dir=tmp,
                parser_version="parser-test",
                retrieved_at=datetime(2026, 6, 18, tzinfo=timezone.utc),
            )
            self.assertTrue(extract.payload_path.exists())
            self.assertTrue(Path(str(extract.payload_path) + ".meta.json").exists())
            self.assertEqual(extract.parser_version, "parser-test")


if __name__ == "__main__":
    unittest.main()
