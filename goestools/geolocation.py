"""Geolocation for the GOES ABI fixed grid.

The ABI stores its pixels as scan angles ``x`` (east-west) and ``y``
(north-south) in radians on a fixed grid, together with the satellite's
projection parameters. These functions convert between those scan angles and
geodetic longitude/latitude using the equations in the GOES-R Product User
Guide (Volume 5, section 4.2.8).

Both directions are provided:

* :func:`scan_to_lonlat` -- scan angles to longitude/latitude, used to place
  pixels on a map;
* :func:`lonlat_to_scan` -- longitude/latitude to scan angles, used to find
  which pixels a domain covers without geolocating the whole grid.
"""

from __future__ import annotations

import numpy as np


# GRS80 ellipsoid, as used by the ABI fixed grid.
R_EQ = 6378137.0            # semi-major axis, metres
R_POL = 6356752.31414       # semi-minor axis, metres
ECCENTRICITY = 0.0818191910435


def _projection_constants(sat_height, sat_lon):
    """Perspective point height above the centre of the Earth, and origin."""
    return sat_height + R_EQ, np.radians(sat_lon)


def scan_to_lonlat(x, y, sat_height, sat_lon, sweep="x"):
    """Longitude and latitude (degrees) of ABI scan angles.

    ``x`` and ``y`` are scan angles in radians; they are broadcast against each
    other, so 1-D arrays give a full 2-D grid. Points that miss the Earth are
    returned as NaN.
    """
    x = np.asarray(x, dtype="float64")
    y = np.asarray(y, dtype="float64")
    if x.ndim == 1 and y.ndim == 1:
        x, y = np.meshgrid(x, y)

    height, lambda_0 = _projection_constants(sat_height, sat_lon)
    if sweep == "y":  # e.g. Meteosat; GOES uses "x"
        x, y = y, x

    sin_x, cos_x = np.sin(x), np.cos(x)
    sin_y, cos_y = np.sin(y), np.cos(y)

    ratio = R_EQ ** 2 / R_POL ** 2
    a = sin_x ** 2 + cos_x ** 2 * (cos_y ** 2 + ratio * sin_y ** 2)
    b = -2.0 * height * cos_x * cos_y
    c = height ** 2 - R_EQ ** 2

    # Distance from the satellite to the pixel. A negative discriminant means
    # the line of sight misses the Earth (off-disk).
    discriminant = b ** 2 - 4.0 * a * c
    with np.errstate(invalid="ignore"):
        r_s = (-b - np.sqrt(discriminant)) / (2.0 * a)

    s_x = r_s * cos_x * cos_y
    s_y = -r_s * sin_x
    s_z = r_s * cos_x * sin_y

    with np.errstate(invalid="ignore", divide="ignore"):
        latitude = np.arctan(ratio * s_z / np.sqrt((height - s_x) ** 2 + s_y ** 2))
        longitude = lambda_0 - np.arctan(s_y / (height - s_x))

    off_disk = discriminant < 0
    latitude = np.where(off_disk, np.nan, np.degrees(latitude))
    longitude = np.where(off_disk, np.nan, np.degrees(longitude))
    return longitude, latitude


def lonlat_to_scan(longitude, latitude, sat_height, sat_lon, sweep="x"):
    """ABI scan angles (radians) of geodetic longitude/latitude in degrees.

    Points on the far side of the Earth, which the satellite cannot see, come
    back as NaN.
    """
    longitude = np.radians(np.asarray(longitude, dtype="float64"))
    latitude = np.radians(np.asarray(latitude, dtype="float64"))
    height, lambda_0 = _projection_constants(sat_height, sat_lon)

    # Geocentric latitude and the local Earth radius there.
    geocentric = np.arctan((R_POL ** 2 / R_EQ ** 2) * np.tan(latitude))
    r_c = R_POL / np.sqrt(1.0 - (ECCENTRICITY * np.cos(geocentric)) ** 2)

    delta_lon = longitude - lambda_0
    s_x = height - r_c * np.cos(geocentric) * np.cos(delta_lon)
    s_y = -r_c * np.cos(geocentric) * np.sin(delta_lon)
    s_z = r_c * np.sin(geocentric)

    # Visible only if the point is on the near side of the Earth.
    visible = height * (height - s_x) >= s_y ** 2 + (R_EQ ** 2 / R_POL ** 2) * s_z ** 2

    with np.errstate(invalid="ignore", divide="ignore"):
        y = np.arctan(s_z / s_x)
        x = np.arcsin(-s_y / np.sqrt(s_x ** 2 + s_y ** 2 + s_z ** 2))

    if sweep == "y":
        x, y = y, x
    return np.where(visible, x, np.nan), np.where(visible, y, np.nan)


def cell_edges(values):
    """Edges of 1-D cell centres, so ``pcolormesh`` gets N+1 boundaries."""
    values = np.asarray(values, dtype="float64")
    middle = 0.5 * (values[:-1] + values[1:])
    first = values[0] - (middle[0] - values[0])
    last = values[-1] + (values[-1] - middle[-1])
    return np.concatenate([[first], middle, [last]])


def corner_lonlat(x, y, sat_height, sat_lon, sweep="x"):
    """Longitude/latitude of pixel *corners*, ready for ``pcolormesh``.

    Returns arrays one row and one column larger than the data, which is what
    ``pcolormesh`` expects when the coordinates bound the cells.
    """
    return scan_to_lonlat(cell_edges(x), cell_edges(y), sat_height, sat_lon, sweep)
