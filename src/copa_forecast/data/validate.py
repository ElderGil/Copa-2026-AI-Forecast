from __future__ import annotations

from copa_forecast.data.contracts import OfficialCompetitionState


class DataValidationError(ValueError):
    """Raised when forecast inputs fail credibility gates."""


def require_official_competition_state(
    state: OfficialCompetitionState, *, degraded_mode_allowed: bool = False
) -> None:
    if state.is_official:
        return
    if degraded_mode_allowed:
        return
    raise DataValidationError(
        "Official FIFA competition state is required for a credible forecast run."
    )


def require_non_empty_state(state: OfficialCompetitionState) -> None:
    if not state.teams:
        raise DataValidationError("Official competition state has no teams.")
    if not state.fixtures:
        raise DataValidationError("Official competition state has no fixtures.")

