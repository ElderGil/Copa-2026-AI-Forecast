from __future__ import annotations

import re
import unicodedata


def normalize_name(value: str) -> str:
    """Return an accent-insensitive, deterministic team-name key."""

    decomposed = unicodedata.normalize("NFKD", value)
    ascii_value = decomposed.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.casefold().strip()
    ascii_value = re.sub(r"[^a-z0-9]+", " ", ascii_value)
    return re.sub(r"\s+", " ", ascii_value).strip()


class TeamNameNormalizer:
    def __init__(self, aliases: dict[str, str] | None = None) -> None:
        self._aliases = {
            normalize_name(alias): canonical
            for alias, canonical in (aliases or {}).items()
        }

    def canonicalize(self, value: str) -> str:
        key = normalize_name(value)
        return self._aliases.get(key, value.strip())

