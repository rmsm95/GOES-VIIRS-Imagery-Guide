"""Read, crop and plot GOES ABI and GLM files.

Download the files with the GOES & JPSS Data Downloader
(https://rmsm95.github.io/GOES-NESDIS_downlaoder/), then point this at the
folder they landed in. Nothing is downloaded here.

    import goestools as gt

    sub = gt.read_subset("data/OR_ABI-L1b-RadF-M6C13_G18_....nc",
                         -166, -162, 53, 56)
    ax.pcolormesh(sub.lon_corners, sub.lat_corners, sub.bt)

    rgb = gt.true_color(files, -166, -162, 53, 56)
    gt.draw_rgb(ax, rgb)

Boxes are ``lon_min, lon_max, lat_min, lat_max`` (west, east, south, north).
Nothing is resampled: the pixels are drawn where the satellite saw them, using
the fixed-grid equations of the GOES-R Product User Guide.
"""

from .glm import read_glm_flashes
from .grid import (
    GridSpec,
    cartopy_crs,
    clean_mesh,
    corner_lonlat,
    edges,
    grid_spec,
    lonlat_to_xy,
    projection_extent,
    viewing_zenith,
    xy_to_lonlat,
)
from .read import Subset, channel_of, find_channels, read_subset
from .viirs import ViirsSubset, read_viirs, viirs_true_color
from .rgb import (
    Composite,
    ash,
    draw_rgb,
    read_channels,
    solar_zenith,
    true_color,
    volcanic_emissions,
)

__all__ = [
    # reading
    "read_subset", "Subset", "find_channels", "channel_of",
    # composites
    "true_color", "ash", "volcanic_emissions", "Composite",
    "read_channels", "draw_rgb", "solar_zenith",
    # VIIRS
    "read_viirs", "viirs_true_color", "ViirsSubset",
    # lightning
    "read_glm_flashes",
    # the fixed grid
    "GridSpec", "grid_spec", "xy_to_lonlat", "lonlat_to_xy",
    "corner_lonlat", "edges", "viewing_zenith", "clean_mesh",
    "cartopy_crs", "projection_extent",
]
__version__ = "0.1.0"
