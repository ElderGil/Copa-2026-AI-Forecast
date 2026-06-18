from __future__ import annotations

import unittest

from copa_forecast.data.contracts import OfficialMatchRecord
from copa_forecast.models.prior import global_elo_ratings


def _match(home: str, away: str, hs: int, as_: int, date: str) -> OfficialMatchRecord:
    return OfficialMatchRecord(
        match_id=f"{home}-{away}-{date}",
        source_id="test",
        source_url="fixture",
        match_date=date,
        home_team=home,
        away_team=away,
        competition="International Friendly",
        match_importance="friendly",
        venue_context="neutral",
        status="completed",
        home_score=hs,
        away_score=as_,
    )


class GlobalEloPriorTest(unittest.TestCase):
    def test_iterative_prior_spreads_more_than_a_single_pass(self) -> None:
        # A short chain A>B>C>D should produce a wider spread under the iterative
        # prior than a single epoch, because opponent quality propagates.
        matches = tuple(
            _match(h, a, 2, 0, f"2025-0{i + 1}-01")
            for i, (h, a) in enumerate(
                [("A", "B"), ("A", "C"), ("B", "C"), ("B", "D"), ("C", "D")]
            )
        )
        single = global_elo_ratings(matches, max_epochs=1)
        converged = global_elo_ratings(matches, max_epochs=60)
        single_spread = max(single.values()) - min(single.values())
        converged_spread = max(converged.values()) - min(converged.values())
        self.assertGreater(converged_spread, single_spread)
        # Ordering reflects the win network.
        self.assertGreater(converged["A"], converged["D"])

    def test_beating_weak_opponents_is_discounted(self) -> None:
        # "Bully" beats only a weak team repeatedly; "Contender" beats a strong
        # team. The contender should end up rated above the bully.
        matches = (
            # Establish a clear gap: Strong dominates Weak.
            _match("Strong", "Weak", 3, 0, "2025-01-01"),
            _match("Strong", "Weak", 3, 0, "2025-02-01"),
            _match("Strong", "Weak", 3, 0, "2025-03-01"),
            # One win each: the bully beats the weak side, the contender the strong side.
            _match("Bully", "Weak", 1, 0, "2025-04-01"),
            _match("Contender", "Strong", 1, 0, "2025-05-01"),
        )
        ratings = global_elo_ratings(matches)
        self.assertGreater(ratings["Strong"], ratings["Weak"])
        self.assertGreater(ratings["Contender"], ratings["Bully"])

    def test_empty_input_returns_empty(self) -> None:
        self.assertEqual(global_elo_ratings(()), {})


if __name__ == "__main__":
    unittest.main()
