from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from copa_forecast.data.contracts import FifaExtract, OfficialCompetitionState
from copa_forecast.data.sources.fifa import FifaParser, JsonFifaParser


def persist_raw_extract(
    *,
    source_id: str,
    source_url: str,
    payload: bytes,
    output_dir: str | Path,
    payload_format: str = "json",
    parser_version: str,
    retrieved_at: datetime | None = None,
) -> FifaExtract:
    """Persist raw FIFA bytes before parsing to preserve auditability."""

    retrieved_at = retrieved_at or datetime.now(timezone.utc)
    checksum = hashlib.sha256(payload).hexdigest()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    timestamp = retrieved_at.strftime("%Y%m%dT%H%M%SZ")
    payload_path = output_path / f"{timestamp}_{source_id}.{payload_format}"
    payload_path.write_bytes(payload)

    extract = FifaExtract(
        extract_id=f"{source_id}-{timestamp}",
        source_id=source_id,
        source_url=source_url,
        retrieved_at=retrieved_at,
        payload_path=payload_path,
        payload_format=payload_format,
        checksum=checksum,
        parser_version=parser_version,
    )
    payload_path.with_suffix(payload_path.suffix + ".meta.json").write_text(
        json.dumps(extract.to_json_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return extract


def build_competition_state(
    *,
    extract: FifaExtract,
    as_of_date: str,
    parser: FifaParser | None = None,
) -> OfficialCompetitionState:
    parser = parser or JsonFifaParser()
    parsed = parser.parse(extract.payload_path.read_bytes())
    return OfficialCompetitionState(
        as_of_date=as_of_date,
        fifa_extract_ids=(extract.extract_id,),
        teams=parsed.teams,
        fixtures=parsed.fixtures,
    )
