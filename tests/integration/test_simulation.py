from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from copa_forecast.cli import simulate
from copa_forecast.data.contracts import OfficialCompetitionState, Team
from copa_forecast.simulation.monte_carlo import simulate_tournament_distribution


class SimulationIntegrationTest(unittest.TestCase):
    def test_world_cup_2026_distribution_has_one_champion_and_32_knockout_teams(self) -> None:
        state = _synthetic_world_cup_2026_state()
        strengths = {team.name: 100 + index for index, team in enumerate(state.teams)}

        distribution = simulate_tournament_distribution(
            state,
            strengths=strengths,
            runs=100,
            seed=20260618,
            as_of_date=date(2026, 6, 18),
        )

        self.assertEqual(len(distribution), 48)
        self.assertAlmostEqual(
            sum(team["champion"] for team in distribution.values()),
            1.0,
        )
        self.assertAlmostEqual(
            sum(team["round_of_32"] for team in distribution.values()),
            32.0,
        )

    def test_simulation_with_resolved_knockout_match_does_not_crash(self) -> None:
        from copa_forecast.data.contracts import Fixture
        state = _synthetic_world_cup_2026_state()
        
        # Add a resolved knockout fixture: team A1 from group A plays team B1 from group B
        resolved_knockout = Fixture(
            match_id="knockout-resolved-test",
            home_team="A1",
            away_team="B1",
            group=None,
            kickoff="2026-06-28T19:00:00Z",
            venue=None,
            status="scheduled",
        )
        
        state_with_knockout = OfficialCompetitionState(
            as_of_date=state.as_of_date,
            fifa_extract_ids=state.fifa_extract_ids,
            teams=state.teams,
            fixtures=(resolved_knockout,),
        )
        
        strengths = {team.name: 100 + index for index, team in enumerate(state.teams)}

        # This should execute without raising ValueError
        distribution = simulate_tournament_distribution(
            state_with_knockout,
            strengths=strengths,
            runs=10,
            seed=20260618,
            as_of_date=date(2026, 6, 18),
        )
        
        self.assertEqual(len(distribution), 48)

    def test_completed_knockout_result_zeroes_eliminated_team(self) -> None:
        import random

        from copa_forecast.data.contracts import Fixture
        from copa_forecast.simulation.monte_carlo import simulate_tournament_once

        state = _synthetic_complete_group_state()
        strengths = {team.name: 1500 + index for index, team in enumerate(state.teams)}

        # Discover a real round-of-32 pairing from the deterministic bracket.
        once = simulate_tournament_once(
            state,
            strengths=strengths,
            rng=random.Random(1),
            as_of_date=date(2026, 6, 30),
        )
        first = next(r for r in once.knockout_results if r.round_name == "round_of_32")
        stronger = max((first.home_team, first.away_team), key=lambda t: strengths[t])
        weaker = first.away_team if stronger == first.home_team else first.home_team

        # Force the stronger team to actually lose that match.
        ko = Fixture(
            match_id="ko-upset",
            home_team=first.home_team,
            away_team=first.away_team,
            group=None,
            kickoff="2026-06-28T19:00:00Z",
            venue=None,
            status="completed",
            home_score=(1 if first.home_team == weaker else 0),
            away_score=(1 if first.away_team == weaker else 0),
        )
        state_with_result = OfficialCompetitionState(
            as_of_date=state.as_of_date,
            fifa_extract_ids=state.fifa_extract_ids,
            teams=state.teams,
            fixtures=state.fixtures + (ko,),
        )

        distribution = simulate_tournament_distribution(
            state_with_result,
            strengths=strengths,
            runs=500,
            seed=7,
            as_of_date=date(2026, 6, 30),
        )

        self.assertEqual(distribution[stronger]["champion"], 0.0)
        self.assertEqual(distribution[stronger]["round_of_16"], 0.0)
        self.assertEqual(distribution[weaker]["round_of_16"], 1.0)
        self.assertAlmostEqual(
            sum(team["champion"] for team in distribution.values()), 1.0
        )

    def test_bracket_state_honors_results_and_placeholders(self) -> None:
        from copa_forecast.simulation.bracket import build_bracket_state

        state = _synthetic_complete_group_state()
        rounds, complete = build_bracket_state(state, as_of_date=date(2026, 6, 30))
        self.assertTrue(complete)
        by_key = dict(rounds)

        # With complete groups, round-of-32 teams are concrete; later rounds wait.
        r32 = by_key["round_of_32"]
        self.assertTrue(all(m.home.team and m.away.team for m in r32))
        self.assertTrue(all(m.winner is None for m in r32))
        r16 = by_key["round_of_16"]
        self.assertTrue(all(m.home.team is None for m in r16))
        self.assertIn("Vencedor J", r16[0].home.placeholder)

    def test_simulate_command_writes_advancement_artifacts(self) -> None:
        fixture = Path("tests/fixtures/fifa/sample_competition_state.json").resolve()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "forecast.json"
            output_dir = root / "public"
            config_path.write_text(
                json.dumps(
                    {
                        "run_id": "simulation-command",
                        "as_of_date": "2026-06-18",
                        "project_github_url": "https://github.com/example/copa",
                        "official_fifa": {
                            "raw_output_dir": str(root / "raw" / "fifa"),
                            "allow_cached_payloads": True,
                            "degraded_mode_allowed": False,
                            "sources": [
                                {
                                    "source_id": "sample-fifa-fixtures",
                                    "url": str(fixture),
                                    "purpose": "fixtures",
                                }
                            ],
                        },
                        "feature_windows": {
                            "current_months": 12,
                            "max_months": 24,
                            "decay_half_life_days": 180,
                        },
                        "simulation": {
                            "tournament_ruleset": "fifa-world-cup-2026",
                            "runs": 100,
                            "random_seed": 20260618,
                        },
                        "site": {
                            "language": "pt-BR",
                            "output_dir": str(output_dir),
                            "top_count": 10,
                        },
                    }
                ),
                encoding="utf-8",
            )

            exit_code = simulate(str(config_path))

            run_dir = root / "data" / "processed" / "simulation_runs" / "simulation-command"
            payload = json.loads((run_dir / "advancement.json").read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["run_id"], "simulation-command")
            self.assertTrue((run_dir / "advancement.csv").read_bytes().startswith(b"\xef\xbb\xbf"))


def _synthetic_world_cup_2026_state() -> OfficialCompetitionState:
    teams = []
    for group in "ABCDEFGHIJKL":
        for position in range(1, 5):
            teams.append(
                Team(
                    team_id=f"{group}{position}",
                    name=f"{group}{position}",
                    group=group,
                    flag_code=f"{group}{position}",
                )
            )
    return OfficialCompetitionState(
        as_of_date="2026-06-18",
        fifa_extract_ids=("synthetic-official-shape",),
        teams=tuple(teams),
        fixtures=(),
    )


def _synthetic_complete_group_state() -> OfficialCompetitionState:
    """A 12x4 state with every group match played (higher seed always wins),
    so the knockout bracket is fully deterministic."""
    from copa_forecast.data.contracts import Fixture

    teams = []
    fixtures = []
    for group in "ABCDEFGHIJKL":
        names = [f"{group}{position}" for position in range(1, 5)]
        for name in names:
            teams.append(
                Team(team_id=name, name=name, group=group, flag_code="br")
            )
        for i in range(4):
            for j in range(i + 1, 4):
                fixtures.append(
                    Fixture(
                        match_id=f"grp-{group}-{i}-{j}",
                        home_team=names[i],
                        away_team=names[j],
                        group=group,
                        kickoff="2026-06-15T19:00:00Z",
                        venue=None,
                        status="completed",
                        home_score=2,
                        away_score=0,
                    )
                )
    return OfficialCompetitionState(
        as_of_date="2026-06-30",
        fifa_extract_ids=("synthetic-complete-groups",),
        teams=tuple(teams),
        fixtures=tuple(fixtures),
    )


if __name__ == "__main__":
    unittest.main()
