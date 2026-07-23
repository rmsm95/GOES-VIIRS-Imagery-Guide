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

Each GOES notebook embeds six separate results:

1. Full Disk (`RadF`), then a Shishaldin-centered Full Disk domain;
2. the nearest CONUS (`RadC`) scan, then a domain inside CONUS;
3. Mesoscale 1 (`RadM1`), then a domain inside that Mesoscale sector.

The Full Disk and Mesoscale scans start at 19:00 UTC. The nearest CONUS scan
starts at 19:01 UTC.

The first three results retain the complete extent of their own NOAA product.
They are not repeated crops of Full Disk. CONUS does not cover Alaska and the
operational Mesoscale 1 sector at this time does not cover Shishaldin, so the
Shishaldin domain is correctly produced from Full Disk. CONUS and Mesoscale
still have their own editable domain values, but those values must stay inside
their respective sources.

The executed demo domains are written in decimal degrees and intersect their
source files. The PNGs are embedded in the notebooks, so they are visible
without running JupyterLab. Every saved PNG includes a WGS84 longitude/latitude
grid and Natural Earth coastlines.

## Use your own domain

The GOES notebooks define one domain for each source:

```python
DOMAINS = {
    "full_disk": (-165.97, 52.76, -161.97, 56.76),
    "conus": (-125.0, 32.0, -115.0, 42.0),
    "mesoscale": (-112.0, 10.0, -104.0, 17.0),
}
```

The order is `MIN_LON, MIN_LAT, MAX_LON, MAX_LAT`. Use `.0` for whole degrees
and values such as `.5` when needed. The Full Disk example is symmetric around
approximately 163.97°W, 54.76°N so Shishaldin appears at the center. Each
coordinate box must intersect the GOES source with the same key. VIIRS keeps
its separate swath domain.

The final cells regenerate and display the PNGs directly inside JupyterLab.

The first mapped output may download 10 m Natural Earth coastlines to
`output/.cartopy/`. Both `data/` and `output/` are excluded from Git; the
executed PNG remains embedded in the notebook.
