from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.request import urlopen

from copa_forecast.data.contracts import Fixture, Team


PARSER_VERSION = "fifa-json-parser-v1"


class FifaSourceError(RuntimeError):
    """Raised when a FIFA payload cannot be retrieved or parsed."""


class FifaCrawler(Protocol):
    def fetch(self, url_or_path: str) -> bytes:
        """Fetch raw payload bytes without parsing them."""


class FifaParser(Protocol):
    parser_version: str

    def parse(self, payload: bytes) -> "ParsedFifaPayload":
        """Parse raw bytes into normalized competition-state fragments."""


@dataclass(frozen=True)
class ParsedFifaPayload:
    teams: tuple[Team, ...]
    fixtures: tuple[Fixture, ...]


class UrlOrFileFifaCrawler:
    """Crawler that is intentionally decoupled from parser volatility."""

    def fetch(self, url_or_path: str) -> bytes:
        if url_or_path.startswith(("https://", "http://")):
            with urlopen(url_or_path, timeout=30) as response:
                return response.read()
        if url_or_path.startswith("file://"):
            return Path(url_or_path.removeprefix("file://")).read_bytes()
        return Path(url_or_path).read_bytes()


class JsonFifaParser:
    parser_version = PARSER_VERSION

    def parse(self, payload: bytes) -> ParsedFifaPayload:
        try:
            body = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise FifaSourceError("MVP parser expects a FIFA JSON-like payload.") from exc
        if not isinstance(body, dict):
            raise FifaSourceError("FIFA payload root must be a JSON object.")

        teams = tuple(_parse_team(item) for item in _items(body, "teams"))
        fixture_items = _items(body, "fixtures") or _items(body, "matches")
        fixtures = tuple(_parse_fixture(item) for item in fixture_items)
        if not teams and fixtures:
            teams = _teams_from_fixtures(fixtures)
        return ParsedFifaPayload(teams=teams, fixtures=fixtures)


def _items(body: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = body.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise FifaSourceError(f"FIFA field '{key}' must be a list.")
    return [item for item in value if isinstance(item, dict)]


def _parse_team(item: dict[str, Any]) -> Team:
    name = str(item.get("name") or item.get("fifa_name") or item.get("team") or "")
    if not name:
        raise FifaSourceError("Team item missing name.")
    team_id = str(item.get("id") or item.get("team_id") or item.get("code") or name)
    return Team(
        team_id=team_id,
        name=name,
        group=_optional_str(item.get("group")),
        flag_code=_optional_str(item.get("flag_code") or item.get("code")),
        confederation=_optional_str(item.get("confederation")),
    )


def _parse_fixture(item: dict[str, Any]) -> Fixture:
    home_team = _team_name(item, "home")
    away_team = _team_name(item, "away")
    if not home_team or not away_team:
        raise FifaSourceError("Fixture item missing home/away team.")
    match_id = str(
        item.get("id")
        or item.get("match_id")
        or item.get("fifa_match_id")
        or f"{home_team}-{away_team}-{item.get('kickoff', '')}"
    )
    return Fixture(
        match_id=match_id,
        fifa_match_id=_optional_str(item.get("fifa_match_id") or item.get("id")),
        home_team=home_team,
        away_team=away_team,
        group=_optional_str(item.get("group")),
        kickoff=_optional_str(item.get("kickoff") or item.get("date")),
        venue=_optional_str(item.get("venue") or item.get("stadium")),
        status=str(item.get("status") or "scheduled").casefold(),
        home_score=_optional_int(item.get("home_score")),
        away_score=_optional_int(item.get("away_score")),
    )


def _team_name(item: dict[str, Any], side: str) -> str:
    direct = item.get(f"{side}_team")
    if isinstance(direct, str):
        return direct
    nested = item.get(side)
    if isinstance(nested, str):
        return nested
    if isinstance(nested, dict):
        return str(nested.get("name") or nested.get("team") or "")
    return ""


def _teams_from_fixtures(fixtures: tuple[Fixture, ...]) -> tuple[Team, ...]:
    names = sorted({name for fx in fixtures for name in (fx.home_team, fx.away_team)})
    return tuple(Team(team_id=name, name=name) for name in names)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)

