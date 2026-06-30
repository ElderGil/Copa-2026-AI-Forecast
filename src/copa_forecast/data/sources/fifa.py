from __future__ import annotations

import json
import time
from dataclasses import dataclass
from http.client import IncompleteRead
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from copa_forecast.data.contracts import Fixture, OfficialMatchRecord, Team

PARSER_VERSION = "fifa-json-parser-v1"
USER_AGENT = (
    "copa-2026-ai-forecast/0.1 "
    "(+https://github.com/ElderGil/Copa-2026-AI-Forecast)"
)


class FifaSourceError(RuntimeError):
    """Raised when a FIFA payload cannot be retrieved or parsed."""


class FifaCrawler(Protocol):
    def fetch(self, url_or_path: str) -> bytes:
        """Fetch raw payload bytes without parsing them."""


class FifaParser(Protocol):
    parser_version: str

    def parse(self, payload: bytes) -> ParsedFifaPayload:
        """Parse raw bytes into normalized competition-state fragments."""


@dataclass(frozen=True)
class ParsedFifaPayload:
    teams: tuple[Team, ...]
    fixtures: tuple[Fixture, ...]


class UrlOrFileFifaCrawler:
    """Crawler that is intentionally decoupled from parser volatility.

    HTTP fetches send a User-Agent and retry with backoff so a single transient
    failure does not abort a 48-team daily ETL. Only http(s), file://, and bare
    local paths are accepted; any other scheme is rejected.
    """

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        retries: int = 3,
        backoff_seconds: float = 1.5,
        user_agent: str = USER_AGENT,
    ) -> None:
        self._timeout = timeout
        self._retries = max(1, retries)
        self._backoff_seconds = backoff_seconds
        self._user_agent = user_agent

    def fetch(self, url_or_path: str) -> bytes:
        if url_or_path.startswith(("https://", "http://")):
            return self._fetch_http(url_or_path)
        if url_or_path.startswith("file://"):
            return Path(url_or_path.removeprefix("file://")).read_bytes()
        if "://" in url_or_path.split("?", 1)[0]:
            raise FifaSourceError(f"Unsupported source scheme: {url_or_path}")
        return Path(url_or_path).read_bytes()

    def _fetch_http(self, url: str) -> bytes:
        last_error: Exception | None = None
        for attempt in range(self._retries):
            try:
                request = Request(
                    url,
                    headers={
                        "User-Agent": self._user_agent,
                        "Accept": "application/json",
                    },
                )
                with urlopen(request, timeout=self._timeout) as response:
                    return response.read()
            except IncompleteRead as exc:
                # Large chunked FIFA payloads occasionally truncate; the partial
                # body is usually the full document, so use it if it parses, else
                # retry.
                last_error = exc
                if _looks_like_json(exc.partial):
                    return exc.partial
                if attempt + 1 < self._retries:
                    time.sleep(self._backoff_seconds * (attempt + 1))
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt + 1 < self._retries:
                    time.sleep(self._backoff_seconds * (attempt + 1))
        raise FifaSourceError(
            f"Failed to fetch FIFA payload after {self._retries} attempts: {url}"
        ) from last_error


def _looks_like_json(payload: bytes) -> bool:
    try:
        json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    return True


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
        result_items = _items(body, "Results")
        if fixture_items:
            fixtures = tuple(_parse_fixture(item) for item in fixture_items)
        else:
            fixtures = tuple(
                fixture
                for fixture in (_parse_fixture_or_none(item) for item in result_items)
                if fixture is not None
            )
        if not teams and "Results" in body:
            teams = _teams_from_calendar_results(result_items)
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
        or item.get("IdMatch")
        or f"{home_team}-{away_team}-{item.get('kickoff', '')}"
    )
    home_score = item.get("home_score") if "home_score" in item else item.get("HomeTeamScore")
    away_score = item.get("away_score") if "away_score" in item else item.get("AwayTeamScore")
    home_penalty = (
        item.get("home_penalty_score")
        if "home_penalty_score" in item
        else item.get("HomeTeamPenaltyScore")
    )
    away_penalty = (
        item.get("away_penalty_score")
        if "away_penalty_score" in item
        else item.get("AwayTeamPenaltyScore")
    )
    return Fixture(
        match_id=match_id,
        fifa_match_id=_optional_str(item.get("fifa_match_id") or item.get("id") or item.get("IdMatch")),
        home_team=home_team,
        away_team=away_team,
        group=_fixture_group(item),
        kickoff=_optional_str(item.get("kickoff") or item.get("date") or item.get("Date")),
        venue=_optional_str(item.get("venue") or item.get("stadium")) or _venue_name(item.get("Stadium")),
        status=str(item.get("status") or _calendar_status(item, home_score=_optional_int(home_score), away_score=_optional_int(away_score))).casefold(),
        home_score=_optional_int(home_score),
        away_score=_optional_int(away_score),
        home_penalty_score=_optional_int(home_penalty),
        away_penalty_score=_optional_int(away_penalty),
        match_number=_optional_int(
            item.get("match_number")
            if "match_number" in item
            else item.get("MatchNumber")
        ),
    )


def _parse_fixture_or_none(item: dict[str, Any]) -> Fixture | None:
    try:
        return _parse_fixture(item)
    except FifaSourceError:
        return None


class FifaCalendarMatchParser:
    parser_version = "fifa-calendar-match-parser-v1"

    def parse_matches(
        self, payload: bytes, *, source_id: str, source_url: str
    ) -> tuple[OfficialMatchRecord, ...]:
        try:
            body = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise FifaSourceError("FIFA calendar parser expects JSON payload.") from exc
        results = _items(body, "Results")
        return tuple(
            record
            for record in (
                _parse_calendar_match(item, source_id=source_id, source_url=source_url)
                for item in results
            )
            if record is not None
        )


def _team_name(item: dict[str, Any], side: str) -> str:
    direct = item.get(f"{side}_team")
    if isinstance(direct, str):
        return direct
    nested = item.get(side)
    if nested is None:
        nested = item.get(side.title())
    if isinstance(nested, str):
        return nested
    if isinstance(nested, dict):
        return str(nested.get("name") or nested.get("team") or _localized(nested.get("TeamName")) or "")
    return ""


def _teams_from_fixtures(fixtures: tuple[Fixture, ...]) -> tuple[Team, ...]:
    names = sorted({name for fx in fixtures for name in (fx.home_team, fx.away_team)})
    return tuple(Team(team_id=name, name=name) for name in names)


def _teams_from_calendar_results(items: list[dict[str, Any]]) -> tuple[Team, ...]:
    teams: dict[str, Team] = {}
    for item in items:
        group = _fixture_group(item)
        for side in ("Home", "Away"):
            team = item.get(side) or {}
            if not _is_senior_mens_national_team(team):
                continue
            name = _localized(team.get("TeamName"))
            team_id = _optional_str(team.get("IdTeam"))
            if not name or not team_id:
                continue
            existing = teams.get(team_id)
            group_to_use = group
            if existing and existing.group and not group:
                group_to_use = existing.group
            teams[team_id] = Team(
                team_id=team_id,
                name=name,
                group=group_to_use,
                flag_code=_optional_str(team.get("IdCountry") or team.get("Abbreviation")),
                confederation=None,
            )
    return tuple(sorted(teams.values(), key=lambda item: item.name.casefold()))


def _fixture_group(item: dict[str, Any]) -> str | None:
    direct = _optional_str(item.get("group"))
    if direct:
        return direct
    group_name = _localized(item.get("GroupName"))
    if not group_name:
        return None
    group_name = group_name.strip()
    if group_name.casefold().startswith("group "):
        return group_name.split()[-1]
    return group_name


def _parse_calendar_match(
    item: dict[str, Any], *, source_id: str, source_url: str
) -> OfficialMatchRecord | None:
    home = item.get("Home") or {}
    away = item.get("Away") or {}
    if not _is_senior_mens_national_team(home) or not _is_senior_mens_national_team(away):
        return None
    home_name = _localized(home.get("TeamName"))
    away_name = _localized(away.get("TeamName"))
    match_date = _optional_str(item.get("Date"))
    if not home_name or not away_name or not match_date:
        return None
    competition = _localized(item.get("CompetitionName")) or "Unknown"
    home_score = _optional_int(item.get("HomeTeamScore") if "HomeTeamScore" in item else home.get("Score"))
    away_score = _optional_int(item.get("AwayTeamScore") if "AwayTeamScore" in item else away.get("Score"))
    return OfficialMatchRecord(
        match_id=str(item.get("IdMatch") or f"{home_name}-{away_name}-{match_date}"),
        fifa_match_id=_optional_str(item.get("IdMatch")),
        source_id=source_id,
        source_url=source_url,
        match_date=match_date,
        home_team=home_name,
        away_team=away_name,
        home_team_id=_optional_str(home.get("IdTeam")),
        away_team_id=_optional_str(away.get("IdTeam")),
        competition=competition,
        match_importance=_match_importance(competition, _localized(item.get("StageName"))),
        venue_context=_venue_context(home, away, item.get("Stadium")),
        status=_calendar_status(item, home_score=home_score, away_score=away_score),
        home_score=home_score,
        away_score=away_score,
        home_penalty_score=_optional_int(item.get("HomeTeamPenaltyScore")),
        away_penalty_score=_optional_int(item.get("AwayTeamPenaltyScore")),
        venue=_venue_name(item.get("Stadium")),
    )


def _is_senior_mens_national_team(team: dict[str, Any]) -> bool:
    return (
        team.get("TeamType") == 1
        and team.get("Gender") == 1
        and team.get("AgeType") in (None, 7)
    )


def _localized(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, list):
        return None
    english = [
        item
        for item in value
        if isinstance(item, dict)
        and str(item.get("Locale", "")).casefold() in {"en-gb", "en-us", "en"}
    ]
    candidates = english or [item for item in value if isinstance(item, dict)]
    if not candidates:
        return None
    return _optional_str(candidates[0].get("Description"))


def _match_importance(competition: str, stage: str | None) -> str:
    text = f"{competition} {stage or ''}".casefold()
    if "fifa world cup" in text and "qualifier" not in text:
        return "world_cup"
    if "qualifier" in text:
        return "world_cup_qualifier"
    if any(name in text for name in ("copa america", "euro", "africa cup", "asian cup", "gold cup")):
        return "continental_final_competition"
    if "nations league" in text:
        return "nations_league"
    if "friendly" in text:
        return "friendly"
    return "official_or_other"


def _venue_context(home: dict[str, Any], away: dict[str, Any], stadium: object) -> str:
    if not isinstance(stadium, dict):
        return "unknown"
    stadium_country = _optional_str(stadium.get("IdCountry"))
    home_country = _optional_str(home.get("IdCountry"))
    away_country = _optional_str(away.get("IdCountry"))
    if stadium_country and home_country and stadium_country == home_country:
        return "home"
    if stadium_country and away_country and stadium_country == away_country:
        return "away"
    if stadium_country:
        return "neutral"
    return "unknown"


def _venue_name(stadium: object) -> str | None:
    if not isinstance(stadium, dict):
        return None
    name = _localized(stadium.get("Name"))
    city = _localized(stadium.get("CityName"))
    if name and city:
        return f"{name}, {city}"
    return name or city


def _calendar_status(
    item: dict[str, Any], *, home_score: int | None, away_score: int | None
) -> str:
    if home_score is not None and away_score is not None:
        return "completed"
    raw_status = item.get("MatchStatus")
    if raw_status in (0, "0"):
        return "completed"
    return "scheduled"


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)
