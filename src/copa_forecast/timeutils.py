from __future__ import annotations

from datetime import date


def days_in_month(year: int, month: int) -> int:
    """Return the number of days in a given month, accounting for leap years."""

    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return 29 if leap else 28
    if month in {4, 6, 9, 11}:
        return 30
    return 31


def add_months(value: date, months: int) -> date:
    """Shift a date by a whole number of calendar months (can be negative)."""

    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, days_in_month(year, month))
    return date(year, month, day)
