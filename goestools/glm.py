"""Read GLM lightning flashes from GLM-L2-LCFA files.

The files come from your own download; nothing is fetched here.
"""

from __future__ import annotations

import numpy as np


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
