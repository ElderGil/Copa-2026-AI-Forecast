from __future__ import annotations

import math
import unittest

from copa_forecast.models.calibration import (
    apply_temperature,
    calibration_bins,
    classification_accuracy,
    expected_calibration_error,
    fit_temperature,
    maximum_calibration_error,
    multiclass_brier_score,
    multiclass_log_loss,
)


class CalibrationMetricTest(unittest.TestCase):
    def test_multiclass_scores_for_1x2_probabilities(self) -> None:
        predictions = [
            {"home_win": 0.7, "draw": 0.2, "away_win": 0.1},
            {"home_win": 0.2, "draw": 0.6, "away_win": 0.2},
        ]
        outcomes = ["home_win", "away_win"]
        labels = ("home_win", "draw", "away_win")

        self.assertAlmostEqual(
            multiclass_brier_score(predictions, outcomes, labels=labels),
            0.59,
        )
        self.assertAlmostEqual(
            multiclass_log_loss(predictions, outcomes, labels=labels),
            -(math.log(0.7) + math.log(0.2)) / 2,
        )
        self.assertEqual(classification_accuracy(predictions, outcomes, labels=labels), 0.5)

    def test_calibration_bins_and_errors(self) -> None:
        bins = calibration_bins([0.8, 0.6, 0.2], [1, 0, 0], bin_count=2)

        self.assertEqual(len(bins), 2)
        self.assertEqual(bins[0].sample_count, 1)
        self.assertAlmostEqual(bins[0].mean_probability, 0.2)
        self.assertAlmostEqual(bins[0].observed_frequency, 0.0)
        self.assertEqual(bins[1].sample_count, 2)
        self.assertAlmostEqual(bins[1].mean_probability, 0.7)
        self.assertAlmostEqual(bins[1].observed_frequency, 0.5)
        self.assertAlmostEqual(expected_calibration_error(bins), 0.2)
        self.assertAlmostEqual(maximum_calibration_error(bins), 0.2)


class TemperatureScalingTest(unittest.TestCase):
    labels = ("home_win", "draw", "away_win")

    def test_apply_temperature_softens_overconfident_vector(self) -> None:
        confident = {"home_win": 0.9, "draw": 0.07, "away_win": 0.03}
        softened = apply_temperature(confident, 2.0, labels=self.labels)
        self.assertAlmostEqual(sum(softened.values()), 1.0)
        self.assertLess(softened["home_win"], confident["home_win"])
        self.assertEqual(
            max(softened, key=softened.get), max(confident, key=confident.get)
        )

    def test_fit_temperature_above_one_for_overconfident_model(self) -> None:
        # Confident predictions that are right only ~half the time -> T > 1.
        predictions = [
            {"home_win": 0.85, "draw": 0.1, "away_win": 0.05},
            {"home_win": 0.85, "draw": 0.1, "away_win": 0.05},
        ]
        outcomes = ["home_win", "away_win"]
        temperature = fit_temperature(predictions, outcomes, labels=self.labels)
        self.assertGreater(temperature, 1.0)


if __name__ == "__main__":
    unittest.main()
