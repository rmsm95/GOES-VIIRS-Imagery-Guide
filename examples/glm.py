"""GOES GLM lightning: download GLM-L2-LCFA flashes and read their locations.

The Geostationary Lightning Mapper reports individual optical *flashes* with a
latitude, longitude and time. LCFA files cover 20 seconds each, so a window of
a few minutes around an ABI scan gives the flashes to draw over that image.

Typical use:

    keys = lcfa_keys("noaa-goes18", datetime(2023, 10, 3, 20, 0), minutes=10)
    files = download_lcfa("noaa-goes18", keys, "data/glm")
    lons, lats = read_flashes(files, bbox=(-107.0, 35.0, -98.0, 43.0))
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, urlretrieve

import numpy as np


NOAA_BASE = "https://{bucket}.s3.amazonaws.com"
PRODUCT = "GLM-L2-LCFA"
KEY_PATTERN = re.compile(r"<Key>([^<]+)</Key>")
# Scan start token in the file name: sYYYYDOYHHMMSSm
START_PATTERN = re.compile(r"_s(\d{4})(\d{3})(\d{2})(\d{2})(\d{2})")


def _hour_keys(bucket: str, moment: datetime) -> list[str]:
    """Every LCFA key published in the hour containing ``moment``."""
    prefix = f"{PRODUCT}/{moment.year}/{moment.timetuple().tm_yday:03d}/{moment:%H}/"
    url = f"{NOAA_BASE.format(bucket=bucket)}/?list-type=2&prefix={prefix}&max-keys=1000"
    with urlopen(url, timeout=60) as response:
        body = response.read().decode("utf-8", "replace")
    return KEY_PATTERN.findall(body)


def key_start_time(key: str) -> datetime | None:
    """Scan start time encoded in an LCFA file name."""
    match = START_PATTERN.search(key)
    if not match:
        return None
    year, doy, hour, minute, second = (int(part) for part in match.groups())
    return datetime(year, 1, 1, hour, minute, second) + timedelta(days=doy - 1)


def lcfa_keys(bucket: str, start: datetime, minutes: int = 10) -> list[str]:
    """LCFA keys covering ``minutes`` from ``start`` (crossing the hour if needed)."""
    end = start + timedelta(minutes=minutes)
    keys: list[str] = []
    seen: set[str] = set()
    moment = start.replace(minute=0, second=0, microsecond=0)
    while moment <= end:
        for key in _hour_keys(bucket, moment):
            if key in seen:
                continue
            stamp = key_start_time(key)
            if stamp is not None and start <= stamp < end:
                seen.add(key)
                keys.append(key)
        moment += timedelta(hours=1)
    return sorted(keys)


def download_lcfa(bucket: str, keys: list[str], destination: str | Path) -> list[str]:
    """Download LCFA files, reusing anything already present."""
    folder = Path(destination)
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    base = NOAA_BASE.format(bucket=bucket)
    for key in keys:
        target = folder / Path(key).name
        if not target.exists() or target.stat().st_size == 0:
            urlretrieve(f"{base}/{key}", target)
        paths.append(str(target))
    return paths


def abi_scan_keys(bucket: str, product: str, moment: datetime, channels) -> list[str]:
    """ABI keys for one scan time, for the given channels.

    ``product`` is for example "ABI-L1b-RadF" (Full Disk) or "ABI-L1b-RadC".
    The scan whose start time falls in the same minute as ``moment`` is used.
    """
    prefix = f"{product}/{moment.year}/{moment.timetuple().tm_yday:03d}/{moment:%H}/"
    url = f"{NOAA_BASE.format(bucket=bucket)}/?list-type=2&prefix={prefix}&max-keys=1000"
    with urlopen(url, timeout=60) as response:
        body = response.read().decode("utf-8", "replace")
    keys = KEY_PATTERN.findall(body)
    stamp = f"_s{moment.year}{moment.timetuple().tm_yday:03d}{moment:%H%M}"
    wanted = []
    for channel in channels:
        for key in keys:
            if f"{channel}_" in key and stamp in key:
                wanted.append(key)
                break
    return wanted


def download_abi(bucket: str, keys: list[str], destination: str | Path) -> list[str]:
    """Download ABI files, reusing anything already present."""
    return download_lcfa(bucket, keys, destination)


def read_flashes(files, bbox=None):
    """Flash longitudes and latitudes from LCFA files, optionally clipped to a box.

    ``bbox`` is ``(min_lon, min_lat, max_lon, max_lat)``. Returns two arrays.
    """
    import xarray as xr

    longitudes: list[np.ndarray] = []
    latitudes: list[np.ndarray] = []
    for filename in files:
        with xr.open_dataset(filename) as dataset:
            if "flash_lat" not in dataset or "flash_lon" not in dataset:
                continue
            latitudes.append(np.asarray(dataset["flash_lat"].values, dtype="float64"))
            longitudes.append(np.asarray(dataset["flash_lon"].values, dtype="float64"))

    if not latitudes:
        return np.array([]), np.array([])

    lon = np.concatenate(longitudes)
    lat = np.concatenate(latitudes)
    keep = np.isfinite(lon) & np.isfinite(lat)
    if bbox is not None:
        min_lon, min_lat, max_lon, max_lat = bbox
        keep &= (lon >= min_lon) & (lon <= max_lon)
        keep &= (lat >= min_lat) & (lat <= max_lat)
    return lon[keep], lat[keep]
