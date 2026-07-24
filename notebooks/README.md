# JupyterLab tutorials

Executed examples. GitHub shows the code and the exact image it produced in the
same document.

**Every notebook is self-contained.** The folder you read from, the domain you
choose, and the whole plotting code are written out in the notebook itself —
nothing important is hidden in a library, so you can change any of it and re-run.

Each one follows the same four steps:

1. **Your files** — point `DATA_DIR` at the folder holding your NetCDF files.
   (If the folder is empty a small block downloads the example scan so the
   notebook still runs; delete it once you use your own data.)
2. **Plot the complete scan** — the whole Full Disk, CONUS or Mesoscale product.
3. **Your domain** — you type the four numbers:
   `DOMAIN = (min_lon, min_lat, max_lon, max_lat)`.
4. **Plot that domain** — the full drawing code: resampling to a lon/lat grid,
   coastlines, graticule, tick labels, marker and colour bar.

A `STYLE` cell near the top collects the things you are most likely to change:

```python
COAST_COLOUR = "red"        # coastline colour
COAST_WIDTH = 0.8
COAST_RES = "10m"           # "10m", "50m" or "110m"
GRID_COLOUR = "white"       # graticule
GRID_ALPHA = 0.45
GRID_STYLE = "--"
MARKER_LON, MARKER_LAT = -163.9711, 54.7554   # None to hide
FIG_WIDTH = 13.5
DPI = 160
```

## The notebooks

| Notebook | What it shows |
|---|---|
| [`01_full_disk_band.ipynb`](01_full_disk_band.ipynb) | Full Disk, one band (`C13`, 10.3 µm), then a domain with a colour bar |
| [`02_conus.ipynb`](02_conus.ipynb) | CONUS sector: full extent, then a domain inside it |
| [`03_mesoscale.ipynb`](03_mesoscale.ipynb) | Mesoscale 1 sector: full extent, then a domain inside it |
| [`04_true_color.ipynb`](04_true_color.ipynb) | True Color: whole Full Disk, then the Shishaldin domain |
| [`05_ash_rgb.ipynb`](05_ash_rgb.ipynb) | Ash RGB, same order |
| [`06_so2_rgb.ipynb`](06_so2_rgb.ipynb) | SO₂ / Volcanic Emissions RGB, same order |
| [`07_glm_true_color.ipynb`](07_glm_true_color.ipynb) | GLM lightning flashes drawn over True Color |
| [`08_viirs_true_color.ipynb`](08_viirs_true_color.ipynb) | A complete VIIRS granule (not Shishaldin — see the notebook) |

## Environment

```bash
conda env create -f environment.yml
conda activate goes-viirs
python -m jupyter lab
```

## Data used by the examples

GOES-18 ABI, 3 October 2023: Full Disk and Mesoscale 1 at 19:00 UTC, the nearest
CONUS scan at 19:01 UTC. The GLM notebook uses GOES-16 at 20:00 UTC over
thunderstorms in the central United States, where there is both lightning and
daylight.

On that date the **Full Disk is the only product that covers Shishaldin**: the
GOES-18 CONUS sector stops short of Alaska and Mesoscale 1 sits off western
Mexico. The CONUS and Mesoscale notebooks therefore use a domain inside their
own coverage.

Both `data/` and `output/` are excluded from Git; the executed PNG stays
embedded in the notebook.
