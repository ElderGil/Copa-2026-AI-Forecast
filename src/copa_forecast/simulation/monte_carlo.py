from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class TeamStrength:
    team: str
    strength: float


def simulate_champion_once(
    teams: list[TeamStrength], *, rng: random.Random | None = None
) -> str:
    rng = rng or random.Random()
    total = sum(max(team.strength, 0.0) for team in teams)
    if total <= 0:
        raise ValueError("At least one team must have positive strength.")
    pick = rng.random() * total
    running = 0.0
    for team in teams:
        running += max(team.strength, 0.0)
        if running >= pick:
            return team.team
    return teams[-1].team


def simulate_champion_distribution(
    teams: list[TeamStrength], *, runs: int, seed: int
) -> dict[str, float]:
    rng = random.Random(seed)
    counts: Counter[str] = Counter(
        simulate_champion_once(teams, rng=rng) for _ in range(runs)
    )
    return {team: count / runs for team, count in counts.items()}

