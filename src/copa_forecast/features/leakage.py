from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Mapping


class TemporalLeakageError(ValueError):
    """Raised when records include data after the as_of_date cutoff."""


def parse_record_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()


def records_before_as_of_date(
    records: Iterable[Mapping[str, object]],
    *,
    date_field: str,
    as_of_date: date,
) -> list[Mapping[str, object]]:
    """Return only records strictly before the as_of_date temporal cutoff."""

    before: list[Mapping[str, object]] = []
    for record in records:
        record_date = parse_record_date(record[date_field])
        if record_date < as_of_date:
            before.append(record)
    return before


def assert_no_future_records(
    records: Iterable[Mapping[str, object]],
    *,
    date_field: str,
    as_of_date: date,
) -> None:
    for record in records:
        record_date = parse_record_date(record[date_field])
        if record_date >= as_of_date:
            raise TemporalLeakageError(
                f"Record dated {record_date} is not before as_of_date {as_of_date}."
            )

