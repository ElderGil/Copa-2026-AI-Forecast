from __future__ import annotations

import unittest

from copa_forecast.features.pillars import EvidencePillar, split_pillars_by_coverage


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


if __name__ == "__main__":
    unittest.main()

