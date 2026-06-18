from __future__ import annotations

import unittest

from copa_forecast.features.pillars import (
    EvidencePillar,
    describe_pillar_coverage,
    split_pillars_by_coverage,
)


class PillarCoverageTest(unittest.TestCase):
    def test_excludes_pillar_when_ten_of_forty_eight_are_missing(self) -> None:
        included, excluded = split_pillars_by_coverage(
            [
                EvidencePillar("xg", available_teams=38, total_teams=48, source="provider"),
                EvidencePillar("form", available_teams=48, total_teams=48, source="official"),
            ]
        )
        self.assertEqual([item.name for item in included], ["form"])
        self.assertEqual([item.name for item in excluded], ["xg"])

    def test_reports_reason_when_ten_or_more_teams_are_missing(self) -> None:
        report = describe_pillar_coverage(
            EvidencePillar("squad_context", available_teams=38, total_teams=48, source="official")
        )

        self.assertEqual(report.status, "excluded_low_coverage")
        self.assertEqual(report.missing_teams, 10)
        self.assertEqual(report.reason, "ten_or_more_teams_missing")


if __name__ == "__main__":
    unittest.main()
