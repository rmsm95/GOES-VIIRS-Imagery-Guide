"""GOES ABI fixed grid: scan angles to longitude/latitude and back.

The ABI stores pixels as scan angles ``x`` (east-west) and ``y`` (north-south)
in radians, together with the projection parameters of the satellite. The
equations here are the ones in the GOES-R Product User Guide, Volume 5,
section 4.2.8.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class GridSpec:
    """Projection parameters read from a file's ``goes_imager_projection``."""

    lon_origin: float   # longitude of the sub-satellite point (deg)
    H: float            # satellite distance from the Earth centre (m)
    r_eq: float         # semi-major axis (m)
    r_pol: float        # semi-minor axis (m)
    sweep: str = "x"    # sweep angle axis; "x" for GOES


def grid_spec(dataset) -> GridSpec:
    """Build a :class:`GridSpec` from an open netCDF4 Dataset."""
    projection = dataset.variables["goes_imager_projection"]
    return GridSpec(
        lon_origin=float(projection.longitude_of_projection_origin),
        H=float(projection.perspective_point_height) + float(projection.semi_major_axis),
        r_eq=float(projection.semi_major_axis),
        r_pol=float(projection.semi_minor_axis),
        sweep=str(projection.sweep_angle_axis),
    )


def xy_to_lonlat(x, y, gs: GridSpec):
    """Scan angles (rad) -> longitude/latitude (deg). Off-disk points are NaN.

    One-dimensional ``x`` and ``y`` are treated as grid axes and meshed, so a
    pair of axes gives the full 2-D grid.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.ndim == 1 and y.ndim == 1:
        x, y = np.meshgrid(x, y)
    if gs.sweep == "y":
        x, y = y, x

    lambda_0 = np.radians(gs.lon_origin)
    sin_x, cos_x = np.sin(x), np.cos(x)
    sin_y, cos_y = np.sin(y), np.cos(y)
    ratio = gs.r_eq ** 2 / gs.r_pol ** 2

    a = sin_x ** 2 + cos_x ** 2 * (cos_y ** 2 + ratio * sin_y ** 2)
    b = -2.0 * gs.H * cos_x * cos_y
    c = gs.H ** 2 - gs.r_eq ** 2
    discriminant = b ** 2 - 4.0 * a * c

    with np.errstate(invalid="ignore"):
        r_s = (-b - np.sqrt(discriminant)) / (2.0 * a)
    s_x = r_s * cos_x * cos_y
    s_y = -r_s * sin_x
    s_z = r_s * cos_x * sin_y

    with np.errstate(invalid="ignore", divide="ignore"):
        lat = np.arctan(ratio * s_z / np.sqrt((gs.H - s_x) ** 2 + s_y ** 2))
        lon = lambda_0 - np.arctan(s_y / (gs.H - s_x))

    off_disk = discriminant < 0
    return (np.where(off_disk, np.nan, np.degrees(lon)),
            np.where(off_disk, np.nan, np.degrees(lat)))


def lonlat_to_xy(lon, lat, gs: GridSpec):
    """Longitude/latitude (deg) -> scan angles (rad).

    Points on the far side of the Earth come back as NaN.
    """
    lon = np.radians(np.asarray(lon, dtype=float))
    lat = np.radians(np.asarray(lat, dtype=float))
    lambda_0 = np.radians(gs.lon_origin)

    geocentric = np.arctan((gs.r_pol ** 2 / gs.r_eq ** 2) * np.tan(lat))
    eccentricity = np.sqrt(1.0 - (gs.r_pol / gs.r_eq) ** 2)
    r_c = gs.r_pol / np.sqrt(1.0 - (eccentricity * np.cos(geocentric)) ** 2)

    delta = lon - lambda_0
    s_x = gs.H - r_c * np.cos(geocentric) * np.cos(delta)
    s_y = -r_c * np.cos(geocentric) * np.sin(delta)
    s_z = r_c * np.sin(geocentric)

    visible = gs.H * (gs.H - s_x) >= s_y ** 2 + (gs.r_eq ** 2 / gs.r_pol ** 2) * s_z ** 2
    with np.errstate(invalid="ignore", divide="ignore"):
        y = np.arctan(s_z / s_x)
        x = np.arcsin(-s_y / np.sqrt(s_x ** 2 + s_y ** 2 + s_z ** 2))
    if gs.sweep == "y":
        x, y = y, x
    return np.where(visible, x, np.nan), np.where(visible, y, np.nan)


def edges(values):
    """Cell edges of 1-D centres, so ``pcolormesh`` gets N+1 boundaries."""
    values = np.asarray(values, dtype=float)
    middle = 0.5 * (values[:-1] + values[1:])
    first = values[0] - (middle[0] - values[0])
    last = values[-1] + (values[-1] - middle[-1])
    return np.concatenate([[first], middle, [last]])


def corner_lonlat(x, y, gs: GridSpec):
    """Longitude/latitude of pixel corners, ready for ``pcolormesh``."""
    return xy_to_lonlat(edges(x), edges(y), gs)


def viewing_zenith(lon, lat, gs: GridSpec):
    """Satellite viewing zenith angle (deg) at each surface point."""
    lon = np.radians(np.asarray(lon, dtype=float))
    lat = np.radians(np.asarray(lat, dtype=float))
    lambda_0 = np.radians(gs.lon_origin)

    geocentric = np.arctan((gs.r_pol ** 2 / gs.r_eq ** 2) * np.tan(lat))
    eccentricity = np.sqrt(1.0 - (gs.r_pol / gs.r_eq) ** 2)
    r_c = gs.r_pol / np.sqrt(1.0 - (eccentricity * np.cos(geocentric)) ** 2)

    delta = lon - lambda_0
    s_x = gs.H - r_c * np.cos(geocentric) * np.cos(delta)
    s_y = -r_c * np.cos(geocentric) * np.sin(delta)
    s_z = r_c * np.sin(geocentric)

    distance = np.sqrt(s_x ** 2 + s_y ** 2 + s_z ** 2)
    # Angle at the surface point between the local vertical and the satellite.
    cosine = (s_x * np.cos(geocentric) * np.cos(delta)
              - s_y * np.cos(geocentric) * np.sin(delta)
              + s_z * np.sin(geocentric)) / distance
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))


def clean_mesh(lon_corners, lat_corners, values):
    """Make corner coordinates safe for ``pcolormesh``.

    Pixels beyond the edge of the disk have no longitude or latitude, and
    ``pcolormesh`` refuses non-finite coordinates. Those corners are replaced
    with a finite placeholder and the cells that touch them are masked, so they
    are simply not drawn.

    Returns ``(lon, lat, masked_values)``.
    """
    lon_corners = np.asarray(lon_corners, dtype=float)
    lat_corners = np.asarray(lat_corners, dtype=float)
    values = np.asarray(values)

    bad_corner = ~(np.isfinite(lon_corners) & np.isfinite(lat_corners))
    # A cell is unusable if any of its four corners is.
    bad_cell = (bad_corner[:-1, :-1] | bad_corner[1:, :-1]
                | bad_corner[:-1, 1:] | bad_corner[1:, 1:])

    # The placeholder never shows, because those cells are masked.
    filler_lon = np.nanmean(lon_corners) if np.any(~bad_corner) else 0.0
    filler_lat = np.nanmean(lat_corners) if np.any(~bad_corner) else 0.0
    lon = np.where(bad_corner, filler_lon, lon_corners)
    lat = np.where(bad_corner, filler_lat, lat_corners)

    rows, cols = bad_cell.shape
    trimmed = values[:rows, :cols]
    invalid = bad_cell
    if np.issubdtype(trimmed.dtype, np.floating):
        invalid = invalid | ~np.isfinite(trimmed)
    return lon, lat, np.ma.masked_where(invalid, trimmed)


def cartopy_crs(gs: GridSpec):
    """A cartopy Geostationary projection matching this file's grid.

    Use it to draw a whole scan as the disk the satellite actually sees,
    instead of stretching it onto a flat longitude/latitude map.
    """
    import cartopy.crs as ccrs

    return ccrs.Geostationary(
        central_longitude=gs.lon_origin,
        satellite_height=gs.H - gs.r_eq,      # height above the ellipsoid
        sweep_axis=gs.sweep,
        globe=ccrs.Globe(semimajor_axis=gs.r_eq, semiminor_axis=gs.r_pol),
    )


def projection_extent(x, y, gs: GridSpec):
    """``[left, right, bottom, top]`` in projection metres, for ``imshow``.

    The ABI y axis runs north to south, so the top edge comes from ``y[0]``.
    """
    height = gs.H - gs.r_eq
    ex = edges(np.asarray(x, dtype=float)) * height
    ey = edges(np.asarray(y, dtype=float)) * height
    return [float(ex[0]), float(ex[-1]), float(ey[-1]), float(ey[0])]
