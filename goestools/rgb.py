"""RGB composites from ABI channels, drawn without resampling.

    rgb = true_color(files, -166, -162, 53, 56)
    draw_rgb(ax, rgb)

Channels come at 0.5, 1 and 2 km. They are aligned by averaging the finer one
down to the coarser grid by an exact integer factor, so nothing is interpolated
and the pixels stay where the satellite recorded them.

Recipes follow the NOAA/CIMSS and CIRA quick guides; see ``docs/RGB.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from .grid import GridSpec, clean_mesh, grid_spec
from .read import _pixel_window, find_channels, read_subset


@dataclass
class Composite:
    """An RGB image over a box, with everything needed to plot it."""

    rgb: np.ndarray               # (rows, cols, 3), 0..1
    name: str
    lon_corners: np.ndarray
    lat_corners: np.ndarray
    time: datetime | None
    satellite: str = ""
    gs: GridSpec | None = field(default=None, repr=False)

    @property
    def shape(self):
        return self.rgb.shape

    def __repr__(self):
        return f"<Composite {self.name} {self.rgb.shape} at {self.time}>"


def solar_zenith(when, lon, lat):
    """Solar zenith angle in degrees (NOAA's low-precision equations)."""
    day = when.timetuple().tm_yday
    hour = when.hour + when.minute / 60.0 + when.second / 3600.0

    gamma = 2.0 * np.pi / 365.0 * (day - 1 + (hour - 12) / 24.0)
    equation_of_time = 229.18 * (
        0.000075 + 0.001868 * np.cos(gamma) - 0.032077 * np.sin(gamma)
        - 0.014615 * np.cos(2 * gamma) - 0.040849 * np.sin(2 * gamma)
    )
    declination = (
        0.006918 - 0.399912 * np.cos(gamma) + 0.070257 * np.sin(gamma)
        - 0.006758 * np.cos(2 * gamma) + 0.000907 * np.sin(2 * gamma)
        - 0.002697 * np.cos(3 * gamma) + 0.00148 * np.sin(3 * gamma)
    )

    offset = equation_of_time + 4.0 * np.asarray(lon, dtype=float)
    hour_angle = np.radians((hour * 60.0 + offset) / 4.0 - 180.0)
    lat = np.radians(np.asarray(lat, dtype=float))
    cosine = (np.sin(lat) * np.sin(declination)
              + np.cos(lat) * np.cos(declination) * np.cos(hour_angle))
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))


def _aggregate(values, factor):
    """Average blocks of ``factor`` x ``factor`` pixels."""
    if factor == 1:
        return values
    rows = values.shape[0] // factor * factor
    cols = values.shape[1] // factor * factor
    block = values[:rows, :cols].reshape(rows // factor, factor,
                                         cols // factor, factor)
    with np.errstate(invalid="ignore"):
        return np.nanmean(block, axis=(1, 3))


def _stretch(values, low, high, gamma=1.0):
    """Clip to a physical range, scale to 0..1, then apply gamma."""
    scaled = np.clip((np.asarray(values, dtype=float) - low) / (high - low), 0.0, 1.0)
    return scaled ** (1.0 / gamma) if gamma != 1.0 else scaled


def read_channels(files, channels, lon_min=None, lon_max=None,
                  lat_min=None, lat_max=None, quantity="auto", stride=1):
    """Read several channels onto the coarsest of their grids.

    Returns ``(arrays, reference)``: ``arrays`` maps each channel name to a 2-D
    array, and ``reference`` is the :class:`~goestools.read.Subset` of the
    coarsest channel, which carries the coordinates and the scan time.
    """
    import netCDF4

    paths = find_channels(files, channels)

    sizes = {}
    for name, path in paths.items():
        with netCDF4.Dataset(str(path), "r") as dataset:
            sizes[name] = dataset.variables["x"].size
    coarsest = min(sizes, key=sizes.get)

    # The index window is worked out once, on the coarsest grid.
    with netCDF4.Dataset(str(paths[coarsest]), "r") as dataset:
        gs = grid_spec(dataset)
        x = np.asarray(dataset.variables["x"][:], dtype=float)
        y = np.asarray(dataset.variables["y"][:], dtype=float)
    if lon_min is None:
        window = (0, x.size, 0, y.size)
    else:
        window = _pixel_window(x, y, gs, lon_min, lon_max, lat_min, lat_max)

    reference = read_subset(paths[coarsest], quantity=quantity,
                            stride=stride, window=window)
    arrays = {coarsest: reference.values}

    i0, i1, j0, j1 = window
    for name, path in paths.items():
        if name == coarsest:
            continue
        factor = sizes[name] // sizes[coarsest]
        if factor * sizes[coarsest] != sizes[name]:
            raise ValueError(
                f"{name} is not an integer multiple of the {coarsest} grid; "
                "they cannot be aligned exactly."
            )
        finer = read_subset(
            path, quantity=quantity, stride=stride,
            window=(i0 * factor, i1 * factor, j0 * factor, j1 * factor),
        )
        arrays[name] = _aggregate(finer.values, factor)

    # Trim any odd row or column left by the aggregation.
    rows = min(a.shape[0] for a in arrays.values())
    cols = min(a.shape[1] for a in arrays.values())
    return {k: v[:rows, :cols] for k, v in arrays.items()}, reference


def _finish(rgb, name, reference):
    rows, cols = rgb.shape[0], rgb.shape[1]
    return Composite(rgb, name,
                     reference.lon_corners[:rows + 1, :cols + 1],
                     reference.lat_corners[:rows + 1, :cols + 1],
                     reference.time, reference.satellite, reference.gs)


def true_color(files, lon_min=None, lon_max=None, lat_min=None, lat_max=None,
               gamma=2.2, sun_correction=True, stride=1):
    """True Color: real colour, daylight only.

    ABI has no green band, so green is synthesised from the blue, red and
    vegetation channels (NOAA/CIMSS):

        R = C02,  G = 0.45*C02 + 0.10*C03 + 0.45*C01,  B = C01

    With ``sun_correction`` the reflectances are divided by the cosine of the
    solar zenith angle, which evens out the brightness. No Rayleigh correction
    is applied, so parts of the disk far from the sub-satellite point look
    hazier than in an operational product.
    """
    arrays, reference = read_channels(
        files, ["C01", "C02", "C03"], lon_min, lon_max, lat_min, lat_max,
        quantity="reflectance", stride=stride,
    )
    blue, red, veggie = arrays["C01"], arrays["C02"], arrays["C03"]

    if sun_correction and reference.time is not None:
        zenith = solar_zenith(reference.time,
                              np.nanmean(reference.lon), np.nanmean(reference.lat))
        cosine = max(float(np.cos(np.radians(min(float(zenith), 80.0)))), 0.15)
        blue, red, veggie = blue / cosine, red / cosine, veggie / cosine

    green = 0.45 * red + 0.10 * veggie + 0.45 * blue
    rgb = np.dstack([_stretch(red, 0.0, 1.0, gamma),
                     _stretch(green, 0.0, 1.0, gamma),
                     _stretch(blue, 0.0, 1.0, gamma)])
    return _finish(rgb, "True Color", reference)


def ash(files, lon_min=None, lon_max=None, lat_min=None, lat_max=None, stride=1):
    """Ash RGB (CIRA). Works day and night; ash tends to red or magenta."""
    arrays, reference = read_channels(
        files, ["C11", "C13", "C14", "C15"], lon_min, lon_max, lat_min, lat_max,
        quantity="bt", stride=stride,
    )
    rgb = np.dstack([
        _stretch(arrays["C15"] - arrays["C13"], -6.7, 2.6),
        _stretch(arrays["C14"] - arrays["C11"], -6.0, 6.3),
        _stretch(arrays["C13"], 243.6, 302.4),
    ])
    return _finish(rgb, "Ash RGB", reference)


def volcanic_emissions(files, lon_min=None, lon_max=None, lat_min=None,
                       lat_max=None, stride=1):
    """SO2 / Volcanic Emissions RGB (CIRA). Qualitative, not a retrieval."""
    arrays, reference = read_channels(
        files, ["C09", "C10", "C11", "C13"], lon_min, lon_max, lat_min, lat_max,
        quantity="bt", stride=stride,
    )
    rgb = np.dstack([
        _stretch(arrays["C09"] - arrays["C10"], -4.0, 2.0),
        _stretch(arrays["C13"] - arrays["C11"], -4.0, 5.0),
        _stretch(arrays["C13"], 243.05, 302.95),
    ])
    return _finish(rgb, "SO2 / Volcanic Emissions RGB", reference)


def draw_rgb(ax, composite, **kwargs):
    """Draw a :class:`Composite` with ``pcolormesh`` corner coordinates.

    ``pcolormesh`` colours cells from a 2-D array, so the RGB is handed over as
    a per-cell colour list. Pixels with no data are left transparent.
    """
    rgb = np.asarray(composite.rgb, dtype=float)
    lon, lat, placeholder = clean_mesh(
        composite.lon_corners, composite.lat_corners, rgb[..., 0]
    )
    rows, cols = placeholder.shape
    colours = rgb[:rows, :cols].reshape(-1, 3)
    drawn = ~np.ma.getmaskarray(placeholder).ravel()
    good = np.isfinite(colours).all(axis=1) & drawn
    rgba = np.column_stack([
        np.clip(np.where(good[:, None], colours, 0.0), 0.0, 1.0),
        good.astype(float),
    ])

    mesh = ax.pcolormesh(lon, lat, placeholder, **kwargs)
    mesh.set_facecolor(rgba)
    mesh.set_array(None)
    return mesh
