from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Iterable, Mapping

from copa_forecast.features.leakage import parse_record_date


def exponential_decay_weight(
    match_date: date, *, as_of_date: date, half_life_days: int
) -> float:
    age_days = max((as_of_date - match_date).days, 0)
    if half_life_days <= 0:
        raise ValueError("half_life_days must be positive.")
    return math.pow(0.5, age_days / half_life_days)


def rolling_window_records(
    records: Iterable[Mapping[str, object]],
    *,
    date_field: str,
    as_of_date: date,
    months: int,
) -> list[Mapping[str, object]]:
    start_date = as_of_date - timedelta(days=round(months * 30.4375))
    return [
        record
        for record in records
        if start_date <= parse_record_date(record[date_field]) < as_of_date
    ]

