from __future__ import annotations

import unittest
from datetime import date

from copa_forecast.features.leakage import (
    TemporalLeakageError,
    assert_no_future_records,
    records_before_as_of_date,
)


class LeakageTest(unittest.TestCase):
    def test_filters_records_before_as_of_date(self) -> None:
        records = [{"match_date": "2026-06-17"}, {"match_date": "2026-06-18"}]
        filtered = records_before_as_of_date(
            records, date_field="match_date", as_of_date=date(2026, 6, 18)
        )
        self.assertEqual(len(filtered), 1)

    def test_rejects_same_day_or_future_records(self) -> None:
        with self.assertRaises(TemporalLeakageError):
            assert_no_future_records(
                [{"match_date": "2026-06-18"}],
                date_field="match_date",
                as_of_date=date(2026, 6, 18),
            )


if __name__ == "__main__":
    unittest.main()

