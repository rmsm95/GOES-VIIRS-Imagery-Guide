"""Read VIIRS SDR granules (HDF5) and crop them to a longitude/latitude box.

VIIRS is an orbital swath, so unlike ABI it stores a latitude and a longitude
for every pixel in a separate geolocation file. That makes it simpler: there is
no fixed-grid geometry to invert, the coordinates are read straight off disk.

    sub = read_viirs("data/viirs", ["M05", "M04", "M03"], -166, -162, 53, 56)
    ax.pcolormesh(sub.lon, sub.lat, sub.values["M05"], shading="nearest")

Keep the band files and their geolocation from the same pass in one folder:
``GMTCO`` goes with the M bands, ``GITCO`` with the I bands.
"""

from __future__ import annotations

import glob
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

# Which geolocation file each band family needs, and where the arrays live.
GEO_FOR = {"M": ("GMTCO", "VIIRS-MOD-GEO-TC"), "I": ("GITCO", "VIIRS-IMG-GEO-TC")}
FALLBACK_GEO = {"M": ("GMODO", "VIIRS-MOD-GEO"), "I": ("GIMGO", "VIIRS-IMG-GEO")}


@dataclass
class ViirsSubset:
    """Several VIIRS bands over a box, with their per-pixel coordinates."""

    values: dict            # band name -> 2-D array
    lon: np.ndarray
    lat: np.ndarray
    time: datetime | None
    satellite: str = ""

    @property
    def shape(self):
        return self.lon.shape

    def __repr__(self):
        bands = ", ".join(sorted(self.values))
        return f"<ViirsSubset {self.satellite} [{bands}] {self.lon.shape} at {self.time}>"


def _h5_first(group, name):
    """First dataset whose path contains ``name``."""
    found = []
    group.visit(lambda key: found.append(key) if name in key else None)
    if not found:
        raise KeyError(f"{name} not found in the file")
    return found[0]


def _read_geolocation(folder, family):
    """Latitude/longitude arrays and the granule start time."""
    import h5py

    for prefix, _ in (GEO_FOR[family], FALLBACK_GEO[family]):
        matches = sorted(glob.glob(str(Path(folder) / f"{prefix}*.h5")))
        if matches:
            break
    else:
        raise FileNotFoundError(
            f"No geolocation file for the {family} bands. Download "
            f"{GEO_FOR[family][0]} from the same pass and put it in this folder."
        )

    with h5py.File(matches[0], "r") as handle:
        lat = np.asarray(handle[_h5_first(handle, "Latitude")][:], dtype="float32")
        lon = np.asarray(handle[_h5_first(handle, "Longitude")][:], dtype="float32")
        time = _granule_time(handle)

    # VIIRS marks missing geolocation with large negative values.
    lat = np.where(lat < -900, np.nan, lat)
    lon = np.where(lon < -900, np.nan, lon)
    return lon, lat, time


def _granule_time(handle):
    """Granule start time from the HDF5 attributes."""
    try:
        date = handle["Data_Products"]
        node = date[list(date.keys())[0]]
        gran = node[list(node.keys())[-1]]
        day = gran.attrs["Beginning_Date"][0][0].decode()
        clock = gran.attrs["Beginning_Time"][0][0].decode()
        return datetime.strptime(day + clock[:6], "%Y%m%d%H%M%S")
    except Exception:
        return None


def _read_band(folder, band):
    """Reflectance (or brightness temperature) for one band."""
    import h5py

    matches = sorted(glob.glob(str(Path(folder) / f"SV{band}*.h5")))
    if not matches:
        raise FileNotFoundError(
            f"No SV{band} file in {folder}. Download the band you asked for."
        )

    with h5py.File(matches[0], "r") as handle:
        try:
            raw_key = _h5_first(handle, "Reflectance")
            factor_key = _h5_first(handle, "ReflectanceFactors")
        except KeyError:
            raw_key = _h5_first(handle, "BrightnessTemperature")
            factor_key = _h5_first(handle, "BrightnessTemperatureFactors")
        raw = np.asarray(handle[raw_key][:], dtype="float32")
        scale, offset = np.asarray(handle[factor_key][:2], dtype="float32")

    # Values at or above the first fill code are missing.
    raw = np.where(raw >= 65528, np.nan, raw)
    return raw * scale + offset


def read_viirs(folder, bands, lon_min=None, lon_max=None,
               lat_min=None, lat_max=None):
    """Read VIIRS bands from a folder, cropped to a lon/lat box.

    All the bands must be the same family (all ``M`` or all ``I``), since the
    two families sit on different grids.
    """
    families = {band[0].upper() for band in bands}
    if len(families) != 1:
        raise ValueError("Mix of M and I bands; they sit on different grids.")
    family = families.pop()

    lon, lat, time = _read_geolocation(folder, family)
    values = {band: _read_band(folder, band) for band in bands}

    shape = next(iter(values.values())).shape
    if lon.shape != shape:
        raise ValueError(
            f"Geolocation is {lon.shape} but the bands are {shape}: the "
            "geolocation file does not match these bands."
        )

    if lon_min is not None:
        inside = ((lon >= lon_min) & (lon <= lon_max)
                  & (lat >= lat_min) & (lat <= lat_max))
        if not inside.any():
            raise ValueError(
                "This granule does not cover the box. VIIRS is polar-orbiting, "
                "so a given pass may simply miss the area."
            )
        rows = np.where(inside.any(axis=1))[0]
        cols = np.where(inside.any(axis=0))[0]
        row_slice = slice(rows[0], rows[-1] + 1)
        col_slice = slice(cols[0], cols[-1] + 1)
        lon, lat = lon[row_slice, col_slice], lat[row_slice, col_slice]
        values = {k: v[row_slice, col_slice] for k, v in values.items()}

    satellite = "Suomi NPP / NOAA-20"
    return ViirsSubset(values, lon, lat, time, satellite)


def viirs_true_color(folder, lon_min=None, lon_max=None, lat_min=None,
                     lat_max=None, gamma=2.2):
    """VIIRS True Color from M05 (red), M04 (green) and M03 (blue).

    Unlike ABI, VIIRS has a real green band, so nothing is synthesised.
    Returns ``(rgb, lon, lat, time)``.
    """
    sub = read_viirs(folder, ["M05", "M04", "M03"],
                     lon_min, lon_max, lat_min, lat_max)

    def stretch(values):
        return np.clip(values, 0.0, 1.0) ** (1.0 / gamma)

    rgb = np.dstack([stretch(sub.values["M05"]),
                     stretch(sub.values["M04"]),
                     stretch(sub.values["M03"])])
    return rgb, sub.lon, sub.lat, sub.time
