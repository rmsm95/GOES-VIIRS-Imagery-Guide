"""Read, crop and plot GOES ABI and GLM files you already have.

Download the files first with the
`GOES & JPSS Data Downloader <https://rmsm95.github.io/GOES-NESDIS_downlaoder/>`_,
then point this at the folder they landed in. Nothing is downloaded here.

The style follows the widely used ``GOES`` package by Joao Henry Huaman Chinchay
(https://github.com/joaohenry23/GOES), but this is a separate, self-contained
implementation with no dependency on it.

    import goestools as goes

    ds = goes.open_dataset("data/OR_ABI-L1b-RadF-M6C13_G18_....nc")
    BT, LonCor, LatCor = ds.image("BT", lonlat="corner",
                                  domain=[-166, -162, 53, 56])

    ax.pcolormesh(LonCor.data, LatCor.data, BT.data)

Domains are ``[LonMin, LonMax, LatMin, LatMax]``. Nothing is resampled: the
pixels are drawn where the satellite actually saw them.
"""

from .dataset import ABIDataset, Field, open_dataset
from .geolocation import cell_edges, corner_lonlat, lonlat_to_scan, scan_to_lonlat
from .glm import read_glm_flashes
from .rgb import (
    ash,
    pcolormesh_rgb,
    read_aligned,
    solar_zenith_angle,
    true_color,
    volcanic_emissions,
)

__all__ = [
    "open_dataset", "ABIDataset", "Field",
    "read_glm_flashes",
    "true_color", "ash", "volcanic_emissions",
    "pcolormesh_rgb", "read_aligned", "solar_zenith_angle",
    "scan_to_lonlat", "lonlat_to_scan", "corner_lonlat", "cell_edges",
]
__version__ = "0.1.0"
