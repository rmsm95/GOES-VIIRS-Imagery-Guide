from unittest import TestCase

import numpy as np

from examples.day_night import blend_day_night, day_weight, ir_cloud_gray


class DayWeightTests(TestCase):
    def test_full_day_is_one_and_full_night_is_zero(self):
        weight = day_weight(np.array([0.0, 85.0, 91.0, 130.0]))
        self.assertEqual(weight[0], 1.0)
        self.assertEqual(weight[1], 1.0)
        self.assertEqual(weight[2], 0.0)
        self.assertEqual(weight[3], 0.0)

    def test_twilight_midpoint_is_a_half(self):
        # Default band is 85..91 degrees; the midpoint 88 is a 50/50 blend.
        self.assertAlmostEqual(float(day_weight(np.array([88.0]))[0]), 0.5)

    def test_weight_decreases_with_zenith(self):
        weight = day_weight(np.linspace(0.0, 180.0, 50))
        self.assertTrue(np.all(np.diff(weight) <= 1e-12))

    def test_invalid_limits_are_rejected(self):
        with self.assertRaises(ValueError):
            day_weight(np.array([90.0]), day_limit=91.0, night_limit=90.0)


class IrCloudGrayTests(TestCase):
    def test_cold_is_bright_and_warm_is_dark(self):
        gray = ir_cloud_gray(np.array([190.0, 300.0, 150.0, 320.0]))
        self.assertEqual(gray[0], 1.0)   # cold cloud top -> white
        self.assertEqual(gray[1], 0.0)   # warm surface -> black
        self.assertEqual(gray[2], 1.0)   # colder than range -> clipped bright
        self.assertEqual(gray[3], 0.0)   # warmer than range -> clipped dark

    def test_midrange_value(self):
        gray = ir_cloud_gray(np.array([245.0]))
        self.assertAlmostEqual(float(gray[0]), (300.0 - 245.0) / (300.0 - 190.0))

    def test_invalid_limits_are_rejected(self):
        with self.assertRaises(ValueError):
            ir_cloud_gray(np.array([250.0]), cold_kelvin=300.0, warm_kelvin=200.0)


class BlendDayNightTests(TestCase):
    def test_daytime_returns_the_day_rgb(self):
        day = np.random.default_rng(0).random((3, 4, 4))
        night = np.zeros((4, 4))
        blended = blend_day_night(day, night, np.ones((4, 4)))
        np.testing.assert_allclose(blended, day)

    def test_nighttime_returns_the_gray_clouds(self):
        day = np.ones((3, 2, 2))
        night = np.full((2, 2), 0.5)
        blended = blend_day_night(day, night, np.zeros((2, 2)))
        np.testing.assert_allclose(blended, np.full((3, 2, 2), 0.5))

    def test_twilight_is_a_half_mix(self):
        day = np.ones((3, 1, 1))
        night = np.zeros((1, 1))
        blended = blend_day_night(day, night, np.full((1, 1), 0.5))
        self.assertAlmostEqual(float(blended[0, 0, 0]), 0.5)

    def test_wrong_day_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            blend_day_night(np.ones((2, 2)), np.zeros((2, 2)), np.ones((2, 2)))

    def test_nan_pixels_become_zero(self):
        day = np.full((3, 1, 1), np.nan)
        blended = blend_day_night(day, np.zeros((1, 1)), np.ones((1, 1)))
        self.assertEqual(float(blended[0, 0, 0]), 0.0)
