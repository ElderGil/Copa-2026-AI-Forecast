from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from copa_forecast.config import ForecastConfig
from copa_forecast.data.contracts import (
    COMPLETED_STATUSES,
    Fixture,
    OfficialCompetitionState,
    OfficialMatchRecord,
    Team,
)
from copa_forecast.features.leakage import parse_record_date
from copa_forecast.features.pillars import (
    EvidencePillar,
    describe_pillar_coverage,
    split_pillars_by_coverage,
)
from copa_forecast.features.recent import RecentTeamFeatures, build_recent_team_features
from copa_forecast.models.baselines import fifa_sum_ratings
from copa_forecast.models.strength import (
    ScheduleAdjustedRates,
    adjust_rates_for_schedule_strength,
)
from copa_forecast.reporting.countries import display_team_name, flag_emoji
from copa_forecast.reporting.explanations import build_team_explanation
from copa_forecast.simulation.monte_carlo import (
    simulate_tournament_distribution,
)

MODEL_VERSION = "mvp-recency-sos-dynamic-draw-v4"


@dataclass(frozen=True)
class TeamTournamentSignal:
    played: int = 0
    points: int = 0
    goals_for: int = 0
    goals_against: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against


def build_latest_forecast(
    *,
    config: ForecastConfig,
    state: OfficialCompetitionState,
    generated_at: datetime | None = None,
    recent_matches: tuple[OfficialMatchRecord, ...] = (),
    match_temperature: float = 1.0,
) -> dict[str, Any]:
    """Create the public latest.json payload for the current forecast run."""

    generated_at = generated_at or datetime.now(UTC)
    as_of_date = config.as_of_date
    played_recent_matches = _played_recent_matches(recent_matches, as_of_date=as_of_date)
    rating_priors = fifa_sum_ratings(played_recent_matches)
    recent_features = build_recent_team_features(
        teams=state.teams,
        matches=recent_matches,
        as_of_date=as_of_date,
        current_window_months=config.feature_windows.current_months,
        max_window_months=config.feature_windows.max_months,
        half_life_days=config.feature_windows.decay_half_life_days,
        opponent_ratings=rating_priors,
    )
    pillars = build_evidence_pillars(
        state,
        recent_features=recent_features,
        rating_priors=rating_priors,
    )
    included_pillars, excluded_pillars = split_pillars_by_coverage(pillars)
    included_keys = [pillar.name for pillar in included_pillars]
    excluded_keys = [pillar.name for pillar in excluded_pillars]

    signals = build_tournament_signals(state, as_of_date=as_of_date)
    strengths = build_team_strengths(
        state.teams,
        signals=signals,
        included_pillars=set(included_keys),
        recent_features=recent_features,
        rating_priors=rating_priors,
    )
    advancement = simulate_tournament_distribution(
        state,
        strengths=strengths,
        runs=config.simulation.runs,
        seed=config.simulation.random_seed,
        as_of_date=as_of_date,
        temperature=match_temperature,
    )
    calibration_status = (
        f"temperature_scaled_from_backtest:T={match_temperature:.3f}"
        if match_temperature != 1.0
        else "uncalibrated_dynamic_draw_pending_backtest"
    )

    ranked = sorted(
        state.teams,
        key=lambda team: (
            -advancement.get(team.name, {}).get("champion", 0.0),
            team.name.casefold(),
        ),
    )
    teams = [
        _team_row(
            rank=index,
            team=team,
            probability=advancement.get(team.name, {}).get("champion", 0.0),
            advancement=advancement.get(team.name, {}),
            strength=strengths[team.name],
            signal=signals.get(team.name, TeamTournamentSignal()),
            recent_feature=recent_features.get(team.name, RecentTeamFeatures(team.name)),
            rating_prior=rating_priors.get(team.name),
            used_pillars=included_keys,
            excluded_pillars=excluded_keys,
        )
        for index, team in enumerate(ranked, start=1)
    ]

    return {
        "run_id": config.run_id,
        "updated_at": generated_at.isoformat(),
        "as_of_date": as_of_date.isoformat(),
        "model_version": MODEL_VERSION,
        "calibration_status": calibration_status,
        "teams": teams,
        "pillars": [_pillar_payload(pillar, used=pillar in included_pillars) for pillar in pillars],
        "benchmarks": [
            {
                "key": "fifa_power_rankings_aramco",
                "label": "FIFA Power Rankings by Aramco",
                "status": "official_candidate_pending_structured_etl",
                "source": "FIFA",
                "source_url": "https://www.fifa.com/pt/tournaments/mens/worldcup/canadamexicousa2026/power-rankings",
                "model_use": "benchmark_and_explainability_candidate_not_active_feature",
            }
        ],
        "metadata": {
            "run_id": config.run_id,
            "as_of_date": as_of_date.isoformat(),
            "generated_at": generated_at.isoformat(),
            "model_version": MODEL_VERSION,
            "official_state": {
                "is_official": state.is_official,
                "degraded": state.degraded,
                "fifa_extract_ids": list(state.fifa_extract_ids),
                "team_count": len(state.teams),
                "fixture_count": len(state.fixtures),
                "recent_match_count": len(recent_matches),
            },
            "feature_windows": {
                "current_months": config.feature_windows.current_months,
                "max_months": config.feature_windows.max_months,
                "decay_half_life_days": config.feature_windows.decay_half_life_days,
            },
            "simulation": {
                "method": "monte_carlo_tournament_path",
                "bracket_model": "fifa_2026_round_of_32_slots_with_deterministic_third_assignment",
                "ruleset": config.simulation.tournament_ruleset,
                "runs": config.simulation.runs,
                "random_seed": config.simulation.random_seed,
                "match_probability_temperature": match_temperature,
            },
        },
    }


def build_evidence_pillars(
    state: OfficialCompetitionState,
    *,
    recent_features: dict[str, RecentTeamFeatures] | None = None,
    rating_priors: dict[str, float] | None = None,
) -> list[EvidencePillar]:
    total_teams = len(state.teams)
    teams_with_path = _teams_with_tournament_path(state)
    recent_features = recent_features or {}
    teams_with_recent_external_form = {
        team for team, feature in recent_features.items() if feature.matches_24m > 0
    }
    teams_with_current_form = {
        team for team, feature in recent_features.items() if feature.matches_12m > 0
    }
    rating_priors = rating_priors or {}
    teams_with_rating_prior = {
        team.name for team in state.teams if team.name in rating_priors
    }
    teams_with_opponent_context = teams_with_recent_external_form & teams_with_rating_prior
    teams_with_squad_context = set()
    return [
        EvidencePillar(
            "official_competition_state",
            available_teams=total_teams,
            total_teams=total_teams,
            source="FIFA",
        ),
        EvidencePillar(
            "tournament_path",
            available_teams=len(teams_with_path),
            total_teams=total_teams,
            source="FIFA fixtures/results",
        ),
        EvidencePillar(
            "recent_form_window",
            available_teams=len(teams_with_recent_external_form),
            total_teams=total_teams,
            source="FIFA calendar official match records",
        ),
        EvidencePillar(
            "current_form_12m",
            available_teams=len(teams_with_current_form),
            total_teams=total_teams,
            source="FIFA calendar official match records",
        ),
        EvidencePillar(
            "attacking_trend",
            available_teams=len(teams_with_recent_external_form),
            total_teams=total_teams,
            source="FIFA calendar official match records",
        ),
        EvidencePillar(
            "defensive_trend",
            available_teams=len(teams_with_recent_external_form),
            total_teams=total_teams,
            source="FIFA calendar official match records",
        ),
        EvidencePillar(
            "match_importance",
            available_teams=len(teams_with_recent_external_form),
            total_teams=total_teams,
            source="FIFA competition/stage metadata",
        ),
        EvidencePillar(
            "venue_context",
            available_teams=len(teams_with_recent_external_form),
            total_teams=total_teams,
            source="FIFA stadium metadata",
        ),
        EvidencePillar(
            "fifa_sum_rating_prior",
            available_teams=len(teams_with_rating_prior),
            total_teams=total_teams,
            source="FIFA/Coca-Cola SUM-style rating computed from FIFA match records",
        ),
        EvidencePillar(
            "opponent_strength_context",
            available_teams=len(teams_with_opponent_context),
            total_teams=total_teams,
            source="FIFA calendar match records + local FIFA/SUM opponent ratings",
        ),
        EvidencePillar(
            "squad_context",
            available_teams=len(teams_with_squad_context),
            total_teams=total_teams,
            source="official squad reports - pending ETL",
        ),
    ]


def build_tournament_signals(
    state: OfficialCompetitionState, *, as_of_date: date
) -> dict[str, TeamTournamentSignal]:
    signals = {team.name: TeamTournamentSignal() for team in state.teams}
    for fixture in _completed_fixtures_before_cutoff(state.fixtures, as_of_date=as_of_date):
        if fixture.home_score is None or fixture.away_score is None:
            continue
        home_points, away_points = _fixture_points(fixture.home_score, fixture.away_score)
        signals[fixture.home_team] = _add_signal(
            signals.get(fixture.home_team, TeamTournamentSignal()),
            points=home_points,
            goals_for=fixture.home_score,
            goals_against=fixture.away_score,
        )
        signals[fixture.away_team] = _add_signal(
            signals.get(fixture.away_team, TeamTournamentSignal()),
            points=away_points,
            goals_for=fixture.away_score,
            goals_against=fixture.home_score,
        )
    return signals


def build_team_strengths(
    teams: tuple[Team, ...],
    *,
    signals: dict[str, TeamTournamentSignal],
    included_pillars: set[str],
    recent_features: dict[str, RecentTeamFeatures] | None = None,
    rating_priors: dict[str, float] | None = None,
) -> dict[str, float]:
    strengths: dict[str, float] = {}
    recent_features = recent_features or {}
    rating_priors = rating_priors or {}
    for team in teams:
        signal = signals.get(team.name, TeamTournamentSignal())
        recent = recent_features.get(team.name, RecentTeamFeatures(team.name))
        rates = _recent_rates(recent)
        if "opponent_strength_context" in included_pillars:
            rates = adjust_rates_for_schedule_strength(
                points_per_match=rates.points_per_match,
                goals_for_per_match=rates.goals_for_per_match,
                goals_against_per_match=rates.goals_against_per_match,
                goal_difference_per_match=rates.goal_difference_per_match,
                average_opponent_rating=rates.average_opponent_rating,
            )
        strength = 1500.0
        if "tournament_path" in included_pillars:
            strength += signal.points * 10.0
            strength += signal.goal_difference * 4.0
            strength += signal.goals_for * 1.5
            strength -= max(signal.goals_against - signal.goals_for, 0) * 2.0
        if "recent_form_window" in included_pillars:
            strength += (rates.points_per_match - 1.35) * 60.0
        if "attacking_trend" in included_pillars:
            strength += rates.goals_for_per_match * 8.0
        if "defensive_trend" in included_pillars:
            strength += rates.goal_difference_per_match * 100.0
            strength -= rates.goals_against_per_match * 5.0
        if "match_importance" in included_pillars:
            strength += min(recent.weighted_importance, 30.0) * 1.5
        if "fifa_sum_rating_prior" in included_pillars:
            strength += rating_priors.get(team.name, 1500.0) - 1500.0
        strengths[team.name] = max(strength, 1.0)
    return strengths


def _completed_fixtures_before_cutoff(
    fixtures: tuple[Fixture, ...], *, as_of_date: date
) -> list[Fixture]:
    completed = []
    for fixture in fixtures:
        if fixture.status.casefold() not in COMPLETED_STATUSES:
            continue
        if not fixture.kickoff:
            continue
        if parse_record_date(fixture.kickoff) < as_of_date:
            completed.append(fixture)
    return completed


def _played_recent_matches(
    matches: tuple[OfficialMatchRecord, ...], *, as_of_date: date
) -> tuple[OfficialMatchRecord, ...]:
    return tuple(
        match
        for match in matches
        if match.is_played and parse_record_date(match.match_date) < as_of_date
    )


def _fixture_points(home_score: int, away_score: int) -> tuple[int, int]:
    if home_score > away_score:
        return 3, 0
    if home_score < away_score:
        return 0, 3
    return 1, 1


def _add_signal(
    current: TeamTournamentSignal, *, points: int, goals_for: int, goals_against: int
) -> TeamTournamentSignal:
    return TeamTournamentSignal(
        played=current.played + 1,
        points=current.points + points,
        goals_for=current.goals_for + goals_for,
        goals_against=current.goals_against + goals_against,
    )


def _recent_rates(recent_feature: RecentTeamFeatures) -> ScheduleAdjustedRates:
    weighted_denominator = max(recent_feature.weighted_importance, 1.0)
    return ScheduleAdjustedRates(
        points_per_match=recent_feature.weighted_points / weighted_denominator,
        goals_for_per_match=recent_feature.weighted_goals_for / weighted_denominator,
        goals_against_per_match=recent_feature.weighted_goals_against / weighted_denominator,
        goal_difference_per_match=recent_feature.weighted_goal_difference
        / weighted_denominator,
        average_opponent_rating=recent_feature.average_opponent_rating,
        schedule_strength_adjustment=0.0,
    )


def _display_rates(
    recent_feature: RecentTeamFeatures, *, used_pillars: list[str]
) -> ScheduleAdjustedRates:
    rates = _recent_rates(recent_feature)
    if "opponent_strength_context" not in used_pillars:
        return rates
    return adjust_rates_for_schedule_strength(
        points_per_match=rates.points_per_match,
        goals_for_per_match=rates.goals_for_per_match,
        goals_against_per_match=rates.goals_against_per_match,
        goal_difference_per_match=rates.goal_difference_per_match,
        average_opponent_rating=rates.average_opponent_rating,
    )


def _teams_with_tournament_path(state: OfficialCompetitionState) -> set[str]:
    names = {team.name for team in state.teams if team.group}
    for fixture in state.fixtures:
        names.add(fixture.home_team)
        names.add(fixture.away_team)
    return names


def _team_row(
    *,
    rank: int,
    team: Team,
    probability: float,
    advancement: dict[str, float],
    strength: float,
    signal: TeamTournamentSignal,
    recent_feature: RecentTeamFeatures,
    rating_prior: float | None,
    used_pillars: list[str],
    excluded_pillars: list[str],
) -> dict[str, Any]:
    explanation = build_team_explanation(
        team=team.name,
        used_pillars=used_pillars,
        excluded_pillars=excluded_pillars,
        drivers=_team_drivers(
            probability=probability,
            advancement=advancement,
            signal=signal,
            strength=strength,
            recent_feature=recent_feature,
            rating_prior=rating_prior,
            used_pillars=used_pillars,
        ),
    )
    weighted_denominator = max(recent_feature.weighted_importance, 1.0)
    adjusted_rates = _display_rates(recent_feature, used_pillars=used_pillars)
    return {
        "rank": rank,
        "team": team.name,
        "display_name": display_team_name(team.name),
        "team_id": team.team_id,
        "flag": team.flag_code or "",
        "flag_emoji": flag_emoji(team.flag_code),
        "group": team.group,
        "champion_probability": probability,
        "advancement_probabilities": {
            key: round(value, 6) for key, value in sorted(advancement.items())
        },
        "strength": round(strength, 4),
        "tournament_signal": {
            "played": signal.played,
            "points": signal.points,
            "goals_for": signal.goals_for,
            "goals_against": signal.goals_against,
            "goal_difference": signal.goal_difference,
        },
        "recent_features": {
            "matches_24m": recent_feature.matches_24m,
            "matches_12m": recent_feature.matches_12m,
            "weighted_points": round(recent_feature.weighted_points, 4),
            "weighted_goals_for": round(recent_feature.weighted_goals_for, 4),
            "weighted_goals_against": round(recent_feature.weighted_goals_against, 4),
            "weighted_goal_difference": round(recent_feature.weighted_goal_difference, 4),
            "weighted_importance": round(recent_feature.weighted_importance, 4),
            "weighted_opponent_rating": round(recent_feature.weighted_opponent_rating, 4),
            "average_opponent_rating": round(adjusted_rates.average_opponent_rating, 4),
            "schedule_strength_adjustment": round(
                adjusted_rates.schedule_strength_adjustment, 4
            ),
            "weighted_points_per_match": round(
                recent_feature.weighted_points / weighted_denominator, 4
            ),
            "weighted_goal_difference_per_match": round(
                recent_feature.weighted_goal_difference / weighted_denominator, 4
            ),
            "sos_adjusted_points_per_match": round(
                adjusted_rates.points_per_match, 4
            ),
            "sos_adjusted_goal_difference_per_match": round(
                adjusted_rates.goal_difference_per_match, 4
            ),
            "sos_adjusted_goals_for_per_match": round(
                adjusted_rates.goals_for_per_match, 4
            ),
            "sos_adjusted_goals_against_per_match": round(
                adjusted_rates.goals_against_per_match, 4
            ),
            "fifa_sum_rating_prior": round(rating_prior, 4) if rating_prior is not None else None,
            "home_matches": recent_feature.home_matches,
            "away_matches": recent_feature.away_matches,
            "neutral_matches": recent_feature.neutral_matches,
        },
        "used_pillars": list(explanation.used_pillars),
        "excluded_pillars": list(explanation.excluded_pillars),
        "drivers": list(explanation.drivers),
        "summary": explanation.summary,
    }


def _pillar_payload(pillar: EvidencePillar, *, used: bool) -> dict[str, Any]:
    report = describe_pillar_coverage(pillar)
    return {
        "key": pillar.name,
        "label": _pillar_label(pillar.name),
        "coverage": pillar.coverage,
        "available_teams": pillar.available_teams,
        "total_teams": pillar.total_teams,
        "missing_teams": pillar.missing_teams,
        "source": pillar.source,
        "status": "used" if used else report.status,
        "reason": report.reason,
    }


def _team_drivers(
    *,
    probability: float,
    advancement: dict[str, float],
    signal: TeamTournamentSignal,
    strength: float,
    recent_feature: RecentTeamFeatures,
    rating_prior: float | None,
    used_pillars: list[str],
) -> list[str]:
    rates = _display_rates(recent_feature, used_pillars=used_pillars)
    return [
        f"chance_titulo={probability:.4f}",
        f"chance_final={advancement.get('final', 0.0):.4f}",
        f"pontos_torneio={signal.points}",
        f"saldo_gols={signal.goal_difference}",
        f"jogos_24m={recent_feature.matches_24m}",
        f"pontos_por_jogo_24m_ajustado_sos={rates.points_per_match:.2f}",
        f"saldo_por_jogo_24m_ajustado_sos={rates.goal_difference_per_match:.2f}",
        f"media_rating_adversarios_24m={rates.average_opponent_rating:.1f}",
        f"prior_fifa_sum={rating_prior:.1f}" if rating_prior is not None else "prior_fifa_sum=indisponivel",
        f"forca_modelo={strength:.2f}",
    ]


def _pillar_label(key: str) -> str:
    labels = {
        "official_competition_state": "Estado oficial FIFA",
        "tournament_path": "Caminho e resultados do torneio",
        "recent_form_window": "Forma recente em janela temporal",
        "current_form_12m": "Forma atual nos ultimos 12 meses",
        "attacking_trend": "Tendencia ofensiva",
        "defensive_trend": "Tendencia defensiva",
        "match_importance": "Peso competitivo das partidas",
        "venue_context": "Contexto de mando e neutralidade",
        "fifa_sum_rating_prior": "Prior FIFA/SUM de forca relativa",
        "opponent_strength_context": "Forca media dos adversarios",
        "squad_context": "Contexto de elenco",
    }
    return labels.get(key, key.replace("_", " ").title())
