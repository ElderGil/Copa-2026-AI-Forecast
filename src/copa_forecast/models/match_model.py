from __future__ import annotations

from dataclasses import dataclass

from copa_forecast.models.baselines import three_way_baseline


@dataclass(frozen=True)
class MatchProbability:
    team: str
    opponent: str
    win: float
    draw: float
    loss: float

    def normalized(self) -> MatchProbability:
        total = self.win + self.draw + self.loss
        if total <= 0:
            raise ValueError("Probability total must be positive.")
        return MatchProbability(
            team=self.team,
            opponent=self.opponent,
            win=self.win / total,
            draw=self.draw / total,
            loss=self.loss / total,
        )


class BaselineMatchModel:
    """Public match-probability interface over the shared three-way model."""

    def predict(
        self,
        team: str,
        opponent: str,
        ratings: dict[str, float],
        *,
        home_advantage: float = 0.0,
        temperature: float = 1.0,
    ) -> MatchProbability:
        probs = three_way_baseline(
            ratings[team],
            ratings[opponent],
            home_advantage=home_advantage,
            temperature=temperature,
        )
        return MatchProbability(
            team=team,
            opponent=opponent,
            win=probs["win"],
            draw=probs["draw"],
            loss=probs["loss"],
        ).normalized()

