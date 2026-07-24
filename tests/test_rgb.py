from datetime import datetime
from unittest import TestCase

import numpy as np

from goestools.rgb import _aggregate, _stretch, solar_zenith


class StretchTests(TestCase):
    def test_range_maps_to_zero_and_one(self):
        values = np.array([-6.7, 2.6, -20.0, 20.0])

        scaled = _stretch(values, -6.7, 2.6)

        self.assertAlmostEqual(float(scaled[0]), 0.0)
        self.assertAlmostEqual(float(scaled[1]), 1.0)
        self.assertAlmostEqual(float(scaled[2]), 0.0)  # clipped low
        self.assertAlmostEqual(float(scaled[3]), 1.0)  # clipped high

    def test_gamma_brightens_the_midtones(self):
        plain = _stretch(np.array([0.5]), 0.0, 1.0)
        gamma = _stretch(np.array([0.5]), 0.0, 1.0, gamma=2.2)

        self.assertGreater(float(gamma[0]), float(plain[0]))


class AggregateTests(TestCase):
    def test_factor_of_one_changes_nothing(self):
        values = np.arange(6.0).reshape(2, 3)

        np.testing.assert_array_equal(_aggregate(values, 1), values)

    def test_blocks_are_averaged(self):
        values = np.array([[1.0, 3.0], [5.0, 7.0]])

        np.testing.assert_allclose(_aggregate(values, 2), [[4.0]])

    def test_odd_edges_are_dropped(self):
        # A 3x3 array aggregated by 2 keeps only the complete 2x2 block.
        values = np.arange(9.0).reshape(3, 3)

        self.assertEqual(_aggregate(values, 2).shape, (1, 1))


class SolarZenithTests(TestCase):
    def test_local_noon_at_the_equator_is_overhead(self):
        # Equinox, sun over the Greenwich meridian at 12 UTC.
        zenith = solar_zenith(datetime(2023, 3, 21, 12, 0), 0.0, 0.0)

        self.assertLess(float(zenith), 3.0)

    def test_night_side_is_below_the_horizon(self):
        zenith = solar_zenith(datetime(2023, 3, 21, 12, 0), 180.0, 0.0)

        self.assertGreater(float(zenith), 90.0)

    def test_shishaldin_is_dark_at_17_utc(self):
        # 17:00 UTC on 3 October 2023 is before sunrise at the volcano.
        zenith = solar_zenith(datetime(2023, 10, 3, 17, 0), -163.97, 54.76)

        self.assertGreater(float(zenith), 90.0)
