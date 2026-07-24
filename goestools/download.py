"""Download GOES files from the public NOAA buckets on AWS.

No account or credentials are needed; the buckets are open.

    files = download("goes18", "ABI-L1b-RadF",
                     DateTimeIni="20231003-190000",
                     DateTimeFin="20231003-191000",
                     channel=["13"], path_out="data/")

Times are ``YYYYMMDD-HHMMSS`` in UTC. ``DateTimeFin`` may be left out to take
the single scan at ``DateTimeIni``.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, urlretrieve

BUCKET = "https://{bucket}.s3.amazonaws.com"
KEY_PATTERN = re.compile(r"<Key>([^<]+)</Key>")
START_PATTERN = re.compile(r"_s(\d{4})(\d{3})(\d{2})(\d{2})(\d{2})")

SATELLITES = {
    "goes16": "noaa-goes16", "goes17": "noaa-goes17",
    "goes18": "noaa-goes18", "goes19": "noaa-goes19",
}


def _bucket_of(satellite):
    key = str(satellite).lower().replace("-", "")
    if key in SATELLITES:
        return SATELLITES[key]
    if key.startswith("noaa-"):
        return key
    raise ValueError(f"Unknown satellite {satellite!r}. Try one of: "
                     + ", ".join(sorted(SATELLITES)))


def _parse_time(text):
    if text is None:
        return None
    if isinstance(text, datetime):
        return text
    return datetime.strptime(str(text), "%Y%m%d-%H%M%S")


def key_start_time(key):
    """Scan start time encoded in a NOAA file name, or None."""
    match = START_PATTERN.search(key)
    if not match:
        return None
    year, day_of_year, hour, minute, second = (int(p) for p in match.groups())
    return datetime(year, 1, 1, hour, minute, second) + timedelta(days=day_of_year - 1)


def list_keys(satellite, product, moment):
    """Every key published in the hour containing ``moment``."""
    bucket = _bucket_of(satellite)
    prefix = f"{product}/{moment.year}/{moment.timetuple().tm_yday:03d}/{moment:%H}/"
    url = f"{BUCKET.format(bucket=bucket)}/?list-type=2&prefix={prefix}&max-keys=1000"
    with urlopen(url, timeout=60) as response:
        return KEY_PATTERN.findall(response.read().decode("utf-8", "replace"))


def download(Satellite, Product, DateTimeIni, DateTimeFin=None, channel=None,
             path_out="", show_progress=True, overwrite=False):
    """Download files and return their paths.

    Satellite
        ``"goes16"`` ... ``"goes19"``.
    Product
        For example ``"ABI-L1b-RadF"``, ``"ABI-L1b-RadC"``, ``"ABI-L1b-RadM"``
        or ``"GLM-L2-LCFA"``.
    DateTimeIni, DateTimeFin
        ``"YYYYMMDD-HHMMSS"`` UTC. Leaving ``DateTimeFin`` out takes the single
        scan starting in the same minute as ``DateTimeIni``.
    channel
        ABI channels to keep, as ``["13"]`` or ``["01", "02", "03"]``. Ignored
        for products without channels, such as GLM.
    path_out
        Folder to write into; it is created if needed. Files already there are
        reused rather than downloaded again.
    """
    start = _parse_time(DateTimeIni)
    end = _parse_time(DateTimeFin)
    single_scan = end is None
    if single_scan:
        end = start + timedelta(minutes=1)

    channels = None
    if channel:
        channels = [f"C{int(c):02d}" for c in channel]

    folder = Path(path_out) if path_out else Path.cwd()
    folder.mkdir(parents=True, exist_ok=True)

    wanted = []
    seen = set()
    hour = start.replace(minute=0, second=0, microsecond=0)
    while hour <= end:
        for key in list_keys(Satellite, Product, hour):
            if key in seen:
                continue
            moment = key_start_time(key)
            if moment is None or not (start <= moment < end):
                continue
            if channels and not any(f"{c}_" in key for c in channels):
                continue
            seen.add(key)
            wanted.append(key)
        hour += timedelta(hours=1)

    if not wanted:
        raise FileNotFoundError(
            f"No {Product} files for {Satellite} between "
            f"{start:%Y-%m-%d %H:%M} and {end:%H:%M} UTC."
        )

    base = BUCKET.format(bucket=_bucket_of(Satellite))
    paths = []
    for key in sorted(wanted):
        target = folder / Path(key).name
        if overwrite or not target.exists() or target.stat().st_size == 0:
            if show_progress:
                print(f"downloading {target.name}")
            urlretrieve(f"{base}/{key}", target)
        elif show_progress:
            print(f"already here  {target.name}")
        paths.append(str(target))
    return paths


def read_glm_flashes(files, domain=None):
    """Flash longitudes and latitudes from GLM-L2-LCFA files.

    ``domain`` is ``[LonMin, LonMax, LatMin, LatMax]``; leave it out to keep
    every flash in the files.
    """
    import numpy as np
    import netCDF4

    longitudes, latitudes = [], []
    for name in files:
        with netCDF4.Dataset(name, "r") as data:
            if "flash_lat" not in data.variables:
                continue
            latitudes.append(np.asarray(data.variables["flash_lat"][:], dtype="float64"))
            longitudes.append(np.asarray(data.variables["flash_lon"][:], dtype="float64"))

    if not latitudes:
        return np.array([]), np.array([])

    lon = np.concatenate(longitudes)
    lat = np.concatenate(latitudes)
    keep = np.isfinite(lon) & np.isfinite(lat)
    if domain is not None:
        lon_min, lon_max, lat_min, lat_max = (float(v) for v in domain)
        keep &= (lon >= lon_min) & (lon <= lon_max)
        keep &= (lat >= lat_min) & (lat <= lat_max)
    return lon[keep], lat[keep]
