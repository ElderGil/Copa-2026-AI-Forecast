from __future__ import annotations

import unittest
from datetime import date

from copa_forecast.features.windows import (
    exponential_decay_weight,
    rolling_window_records,
)


class WindowFeatureTest(unittest.TestCase):
    def test_rolling_window_keeps_recent_records_only(self) -> None:
        records = [{"match_date": "2026-06-01"}, {"match_date": "2024-01-01"}]
        recent = rolling_window_records(
            records, date_field="match_date", as_of_date=date(2026, 6, 18), months=12
        )
        self.assertEqual(recent, [{"match_date": "2026-06-01"}])

    def test_exponential_decay_half_life(self) -> None:
        weight = exponential_decay_weight(
            date(2026, 6, 8), as_of_date=date(2026, 6, 18), half_life_days=10
        )
        self.assertAlmostEqual(weight, 0.5)


if __name__ == "__main__":
    unittest.main()

