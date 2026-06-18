from __future__ import annotations

import unittest

from copa_forecast.data.normalize import TeamNameNormalizer, normalize_name


class NormalizeTest(unittest.TestCase):
    def test_normalize_name_strips_accents(self) -> None:
        self.assertEqual(normalize_name("Cote d'Ivoire"), "cote d ivoire")

    def test_alias_canonicalization(self) -> None:
        normalizer = TeamNameNormalizer({"USA": "United States"})
        self.assertEqual(normalizer.canonicalize("usa"), "United States")


if __name__ == "__main__":
    unittest.main()

