"""Read an ABI file and crop it to a longitude/latitude box.

    sub = read_subset("OR_ABI-L1b-RadF-M6C13_G18_....nc", -166, -162, 53, 56)
    ax.pcolormesh(sub.lon_corners, sub.lat_corners, sub.bt)

The box is ``lon_min, lon_max, lat_min, lat_max`` (west, east, south, north).
Pass no box to read the whole scan.

Nothing is resampled: the pixels stay where the satellite recorded them and are
drawn through their corner coordinates. Only the pixels inside the box are read
from disk, so cropping a Full Disk file is cheap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np

from .grid import GridSpec, corner_lonlat, grid_spec, lonlat_to_xy, xy_to_lonlat


@dataclass
class Subset:
    """One channel over a box, with everything needed to plot it."""

    values: np.ndarray            # the quantity that was asked for
    quantity: str                 # "bt", "reflectance" or "radiance"
    units: str
    lon: np.ndarray               # pixel centres
    lat: np.ndarray
    lon_corners: np.ndarray       # pixel corners, for pcolormesh
    lat_corners: np.ndarray
    time: datetime | None
    channel: int | None
    satellite: str = ""
    scene: str = ""
    gs: GridSpec | None = field(default=None, repr=False)

    # Convenience names, so the quantity can be read by its own word.
    @property
    def bt(self):
        """Brightness temperature (K); only for infrared channels."""
        if self.quantity != "bt":
            raise AttributeError(f"this subset holds {self.quantity}, not bt")
        return self.values

    @property
    def reflectance(self):
        if self.quantity != "reflectance":
            raise AttributeError(f"this subset holds {self.quantity}, not reflectance")
        return self.values

    @property
    def shape(self):
        return self.values.shape

    def __repr__(self):
        channel = f"C{self.channel:02d}" if self.channel else "?"
        return (f"<Subset {self.satellite} {channel} {self.quantity} "
                f"{self.values.shape} at {self.time}>")


def _pixel_window(x, y, gs, lon_min, lon_max, lat_min, lat_max, pad=6):
    """Index window covering a lon/lat box, found through the scan angles."""
    # Sample the whole box: on a geostationary grid the extreme scan angles can
    # fall inside the box rather than on its edge.
    steps = np.linspace(0.0, 1.0, 101)
    box_lon, box_lat = np.meshgrid(
        lon_min + steps * (lon_max - lon_min),
        lat_min + steps * (lat_max - lat_min),
    )
    scan_x, scan_y = lonlat_to_xy(box_lon.ravel(), box_lat.ravel(), gs)
    if not np.any(np.isfinite(scan_x)):
        raise ValueError("Requested box is not visible from the satellite.")

    inside_x = np.where((x >= np.nanmin(scan_x)) & (x <= np.nanmax(scan_x)))[0]
    inside_y = np.where((y >= np.nanmin(scan_y)) & (y <= np.nanmax(scan_y)))[0]
    if inside_x.size == 0 or inside_y.size == 0:
        raise ValueError("Requested box falls outside this file's coverage.")

    i0, i1 = max(inside_x[0] - pad, 0), min(inside_x[-1] + pad + 1, x.size)
    j0, j1 = max(inside_y[0] - pad, 0), min(inside_y[-1] + pad + 1, y.size)
    return i0, i1, j0, j1


def _scan_time(dataset):
    import netCDF4

    if "time_bounds" not in dataset.variables:
        return None
    variable = dataset.variables["time_bounds"]
    # time_bounds carries no units of its own; they live on "t".
    units = getattr(variable, "units", None) or getattr(
        dataset.variables.get("t"), "units", None
    )
    if units is None:
        return None
    stamps = netCDF4.num2date(
        variable[:], units,
        only_use_cftime_datetimes=False, only_use_python_datetimes=True,
    )
    return stamps[0]


def read_subset(path, lon_min=None, lon_max=None, lat_min=None, lat_max=None,
                quantity="auto", stride=1, window=None):
    """Read one ABI file, cropped to a lon/lat box.

    quantity
        ``"bt"`` for brightness temperature (K), ``"reflectance"``,
        ``"radiance"``, or ``"auto"`` to pick brightness temperature for the
        infrared channels (C07 and up) and reflectance for the visible ones.
    stride
        Take every n-th pixel; useful for a quick look at a whole Full Disk.
    window
        ``(i0, i1, j0, j1)`` index window, if you would rather give indices
        than a box. Used internally to line channels up with each other.
    """
    import netCDF4

    with netCDF4.Dataset(str(path), "r") as dataset:
        gs = grid_spec(dataset)
        x = np.asarray(dataset.variables["x"][:], dtype=float)
        y = np.asarray(dataset.variables["y"][:], dtype=float)
        channel = (int(dataset.variables["band_id"][0])
                   if "band_id" in dataset.variables else None)

        if window is not None:
            i0, i1, j0, j1 = window
        elif lon_min is None:
            i0, i1, j0, j1 = 0, x.size, 0, y.size
        else:
            i0, i1, j0, j1 = _pixel_window(
                x, y, gs, lon_min, lon_max, lat_min, lat_max
            )

        x = x[i0:i1:stride]
        y = y[j0:j1:stride]
        radiance = np.asarray(
            dataset.variables["Rad"][j0:j1:stride, i0:i1:stride], dtype="float32"
        )
        radiance = np.where(np.isfinite(radiance), radiance, np.nan)

        if quantity == "auto":
            quantity = "bt" if (channel or 0) >= 7 else "reflectance"

        if quantity == "radiance":
            values = radiance
            units = getattr(dataset.variables["Rad"], "units", "")
        elif quantity == "bt":
            fk1 = float(dataset.variables["planck_fk1"][0])
            fk2 = float(dataset.variables["planck_fk2"][0])
            bc1 = float(dataset.variables["planck_bc1"][0])
            bc2 = float(dataset.variables["planck_bc2"][0])
            with np.errstate(invalid="ignore", divide="ignore"):
                values = (fk2 / np.log((fk1 / radiance) + 1.0) - bc1) / bc2
            units = "K"
        elif quantity == "reflectance":
            values = radiance * float(dataset.variables["kappa0"][0])
            units = "1"
        else:
            raise ValueError(
                "quantity must be 'auto', 'bt', 'reflectance' or 'radiance'"
            )

        time = _scan_time(dataset)
        satellite = getattr(dataset, "platform_ID", "")
        scene = getattr(dataset, "scene_id", "")

    lon, lat = xy_to_lonlat(x, y, gs)
    lon_corners, lat_corners = corner_lonlat(x, y, gs)
    return Subset(values, quantity, units, lon, lat, lon_corners, lat_corners,
                  time, channel, satellite, scene, gs)


def channel_of(path):
    """ABI channel number in a file name, or None."""
    import re

    match = re.search(r"[-_]M\dC(\d{2})[_-]", Path(path).name)
    return int(match.group(1)) if match else None


def find_channels(files, channels):
    """Map channel names like ``"C13"`` to the file that holds them."""
    found = {}
    for path in files:
        number = channel_of(path)
        if number is not None:
            found[f"C{number:02d}"] = path
    missing = [c for c in channels if c not in found]
    if missing:
        available = ", ".join(sorted(found)) or "none"
        raise FileNotFoundError(
            f"Missing channel(s) {', '.join(missing)}. Found: {available}. "
            "Download every channel this product needs, from the same scan."
        )
    return {c: found[c] for c in channels}
