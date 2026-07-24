"""Read, crop and plot GOES ABI and GLM data.

The style follows the widely used ``GOES`` package by Joao Henry Huaman Chinchay
(https://github.com/joaohenry23/GOES), but this is a separate, self-contained
implementation with no dependency on it.

    import goestools as goes

    files = goes.download("goes18", "ABI-L1b-RadF",
                          DateTimeIni="20231003-190000",
                          channel=["13"], path_out="data/")

    ds = goes.open_dataset(files[0])
    BT, LonCor, LatCor = ds.image("BT", lonlat="corner",
                                  domain=[-166, -162, 53, 56])

    ax.pcolormesh(LonCor.data, LatCor.data, BT.data)

Domains are ``[LonMin, LonMax, LatMin, LatMax]``. Nothing is resampled: the
pixels are drawn where the satellite actually saw them.
"""

from .dataset import ABIDataset, Field, open_dataset
from .download import download, key_start_time, list_keys, read_glm_flashes
from .geolocation import cell_edges, corner_lonlat, lonlat_to_scan, scan_to_lonlat

__all__ = [
    "download", "list_keys", "key_start_time", "read_glm_flashes",
    "open_dataset", "ABIDataset", "Field",
    "scan_to_lonlat", "lonlat_to_scan", "corner_lonlat", "cell_edges",
]
__version__ = "0.1.0"
