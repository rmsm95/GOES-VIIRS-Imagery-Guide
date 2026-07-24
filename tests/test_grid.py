from unittest import TestCase

import numpy as np

from goestools.grid import GridSpec, edges, lonlat_to_xy, xy_to_lonlat

# GOES-18, as stored in the ABI files.
GS = GridSpec(lon_origin=-137.0, H=35786023.0 + 6378137.0,
              r_eq=6378137.0, r_pol=6356752.31414)


class FixedGridTests(TestCase):
    def test_lonlat_survives_a_round_trip(self):
        lon = np.array([-163.97, -150.0, -120.0])
        lat = np.array([54.76, 0.0, -30.0])

        x, y = lonlat_to_xy(lon, lat, GS)
        # xy_to_lonlat meshes 1-D axes, so paired points sit on the diagonal.
        back_lon, back_lat = xy_to_lonlat(x, y, GS)

        np.testing.assert_allclose(np.diagonal(back_lon), lon, atol=1e-6)
        np.testing.assert_allclose(np.diagonal(back_lat), lat, atol=1e-6)

    def test_sub_satellite_point_is_the_grid_origin(self):
        x, y = lonlat_to_xy(GS.lon_origin, 0.0, GS)

        self.assertAlmostEqual(float(x), 0.0, places=9)
        self.assertAlmostEqual(float(y), 0.0, places=9)

    def test_the_far_side_of_the_earth_is_not_visible(self):
        x, y = lonlat_to_xy(GS.lon_origin + 180.0, 0.0, GS)

        self.assertTrue(np.isnan(x))
        self.assertTrue(np.isnan(y))

    def test_off_disk_scan_angles_are_nan(self):
        # Far beyond the Earth's angular radius of about 8.7 degrees.
        lon, lat = xy_to_lonlat(np.radians(20.0), 0.0, GS)

        self.assertTrue(np.isnan(lon))
        self.assertTrue(np.isnan(lat))

    def test_one_dimensional_axes_make_a_grid(self):
        lon, lat = xy_to_lonlat(np.array([-0.01, 0.0, 0.01]),
                                np.array([-0.01, 0.0]), GS)

        self.assertEqual(lon.shape, (2, 3))
        self.assertEqual(lat.shape, (2, 3))


class EdgeTests(TestCase):
    def test_edges_have_one_more_point_than_centres(self):
        result = edges(np.array([1.0, 2.0, 3.0]))

        self.assertEqual(result.shape, (4,))
        np.testing.assert_allclose(result, [0.5, 1.5, 2.5, 3.5])

    def test_edges_follow_a_descending_axis(self):
        # The ABI y axis decreases with index.
        np.testing.assert_allclose(edges(np.array([3.0, 2.0, 1.0])),
                                   [3.5, 2.5, 1.5, 0.5])
