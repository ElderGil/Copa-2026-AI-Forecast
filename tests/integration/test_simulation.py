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


if __name__ == "__main__":
    unittest.main()
