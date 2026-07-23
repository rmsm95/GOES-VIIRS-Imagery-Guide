# JupyterLab tutorials

These notebooks are executed examples. GitHub shows the code and the exact
satellite image produced by the cells in the same document:

- [`01_GOES_true_color.ipynb`](01_GOES_true_color.ipynb): GOES ABI True Color;
- [`02_VIIRS_true_color.ipynb`](02_VIIRS_true_color.ipynb): JPSS VIIRS True Color;
- [`03_GOES_ash_rgb.ipynb`](03_GOES_ash_rgb.ipynb): GOES-18 ABI Ash RGB;
- [`04_GOES_so2_rgb.ipynb`](04_GOES_so2_rgb.ipynb): GOES-18 ABI SO₂ /
  Volcanic Emissions RGB.

## Start JupyterLab

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-notebooks.txt
python -m jupyter lab
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Open the `notebooks` directory in JupyterLab and run every cell from top to
bottom.

## Included demonstration data

On the first local execution, the notebooks download public data:

- GOES: GOES-18 ABI Full Disk, CONUS, and Mesoscale 1 source products from the
  3 October 2023 19:00 UTC window;
- VIIRS: one Suomi NPP granule with I/M bands and geolocation.

Each GOES notebook embeds four separate results in order:

1. Full Disk (`RadF`), scan start 19:00 UTC;
2. the nearest CONUS (`RadC`) scan, start 19:01 UTC;
3. Mesoscale 1 (`RadM1`), scan start 19:00 UTC;
4. a user-defined domain created from Full Disk.

The first three results retain the complete extent of their own NOAA product.
They are not repeated crops of Full Disk. CONUS does not cover Alaska and the
operational Mesoscale 1 sector at this time does not cover Shishaldin, so the
Shishaldin domain is correctly produced from Full Disk.

The executed demo domains are written in decimal degrees and intersect their
source files. The PNGs are embedded in the notebooks, so they are visible
without running JupyterLab. Every saved PNG includes a WGS84 longitude/latitude
grid and Natural Earth coastlines.

## Use your own domain

For Shishaldin, replace the demo input with matching downloaded files and enter:

```python
DOMAIN = (-170.0, 53.0, -160.0, 58.0)
```

The order is `MIN_LON, MIN_LAT, MAX_LON, MAX_LAT`. Use `.0` for whole degrees
and values such as `.5` when needed. The coordinates must intersect the GOES
source coverage or VIIRS swath.

The final cells regenerate and display the PNGs directly inside JupyterLab.

The first mapped output may download 10 m Natural Earth coastlines to
`output/.cartopy/`. Both `data/` and `output/` are excluded from Git; the
executed PNG remains embedded in the notebook.
