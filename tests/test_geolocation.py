from unittest import TestCase

import numpy as np

from goestools.geolocation import (
    cell_edges,
    lonlat_to_scan,
    scan_to_lonlat,
)

# GOES-18 parameters, as stored in the ABI files.
SAT_HEIGHT = 35786023.0
SAT_LON = -137.0


class ScanAngleRoundTripTests(TestCase):
    def test_lonlat_survives_a_round_trip(self):
        lon = np.array([-163.97, -150.0, -120.0])
        lat = np.array([54.76, 0.0, -30.0])

        x, y = lonlat_to_scan(lon, lat, SAT_HEIGHT, SAT_LON)
        # scan_to_lonlat meshgrids 1-D inputs, so paired points sit on the
        # diagonal of the result.
        back_lon, back_lat = scan_to_lonlat(x, y, SAT_HEIGHT, SAT_LON)

        np.testing.assert_allclose(np.diagonal(back_lon), lon, atol=1e-6)
        np.testing.assert_allclose(np.diagonal(back_lat), lat, atol=1e-6)

    def test_paired_points_can_skip_the_meshgrid(self):
        # Passing 2-D arrays keeps the points paired, without meshgridding.
        lon = np.array([[-163.97, -150.0]])
        lat = np.array([[54.76, 0.0]])

        x, y = lonlat_to_scan(lon, lat, SAT_HEIGHT, SAT_LON)
        back_lon, back_lat = scan_to_lonlat(x, y, SAT_HEIGHT, SAT_LON)

        np.testing.assert_allclose(back_lon, lon, atol=1e-6)
        np.testing.assert_allclose(back_lat, lat, atol=1e-6)

    def test_sub_satellite_point_is_the_grid_origin(self):
        x, y = lonlat_to_scan(SAT_LON, 0.0, SAT_HEIGHT, SAT_LON)

        self.assertAlmostEqual(float(x), 0.0, places=9)
        self.assertAlmostEqual(float(y), 0.0, places=9)

    def test_the_far_side_of_the_earth_is_not_visible(self):
        # Directly opposite the satellite: it cannot be seen.
        x, y = lonlat_to_scan(SAT_LON + 180.0, 0.0, SAT_HEIGHT, SAT_LON)

        self.assertTrue(np.isnan(x))
        self.assertTrue(np.isnan(y))

    def test_off_disk_scan_angles_are_nan(self):
        # A scan angle far larger than the Earth's angular radius (~8.7 deg).
        lon, lat = scan_to_lonlat(np.radians(20.0), 0.0, SAT_HEIGHT, SAT_LON)

        self.assertTrue(np.isnan(lon))
        self.assertTrue(np.isnan(lat))

    def test_one_dimensional_inputs_make_a_grid(self):
        lon, lat = scan_to_lonlat(
            np.array([-0.01, 0.0, 0.01]), np.array([-0.01, 0.0]),
            SAT_HEIGHT, SAT_LON,
        )

        self.assertEqual(lon.shape, (2, 3))
        self.assertEqual(lat.shape, (2, 3))


class CellEdgeTests(TestCase):
    def test_edges_have_one_more_point_than_centres(self):
        edges = cell_edges(np.array([1.0, 2.0, 3.0]))

        self.assertEqual(edges.shape, (4,))
        np.testing.assert_allclose(edges, [0.5, 1.5, 2.5, 3.5])

    def test_edges_follow_a_descending_axis(self):
        # The ABI y axis decreases with index.
        edges = cell_edges(np.array([3.0, 2.0, 1.0]))

        np.testing.assert_allclose(edges, [3.5, 2.5, 1.5, 0.5])
