# JupyterLab tutorials

These notebooks are executed examples. GitHub shows the code and the exact
satellite image produced by the cells in the same document:

- [`01_GOES_true_color.ipynb`](01_GOES_true_color.ipynb): GOES ABI True Color;
- [`02_VIIRS_true_color.ipynb`](02_VIIRS_true_color.ipynb): JPSS VIIRS True Color;
- [`03_GOES_ash_rgb.ipynb`](03_GOES_ash_rgb.ipynb): GOES-18 ABI Ash RGB;
- [`04_GOES_so2_rgb.ipynb`](04_GOES_so2_rgb.ipynb): GOES-18 ABI SO₂ /
  Volcanic Emissions RGB;
- [`05_GOES_day_night.ipynb`](05_GOES_day_night.ipynb): GOES-18 ABI Day/Night
  True Color — real color by day, clouds from C13 at night.

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

## What each notebook produces

Each notebook is deliberately simple: it produces **one image** over Shishaldin
and embeds it, so GitHub shows the code and the exact result together.

- The four GOES notebooks download the GOES-18 ABI Full Disk channels they need
  from the 3 October 2023 19:00 UTC scan (17:00 UTC as well for the night side
  of the day/night notebook), build the composite, crop to the **Shishaldin**
  domain, and save one image.
- The VIIRS notebook downloads one Suomi NPP granule with the I/M bands and
  geolocation and renders one image over the granule.

The GOES images keep the **GOES (geostationary) projection** — the satellite's
own projection, with longitude/latitude drawn as reference gridlines rather than
reprojected. Away from the sub-satellite point (as over Alaska) that frame is
slightly tilted, which is expected. VIIRS is an orbital swath with no fixed
projection, so it is placed on a regular lon/lat grid.

Every image includes a longitude/latitude grid and Natural Earth coastlines. The
PNG is embedded in the notebook, so it is visible on GitHub without running
JupyterLab.

## Use your own domain

The GOES notebooks pick a named domain from
[`examples/domains.py`](../examples/domains.py):

```python
DOMAIN_NAME = "shishaldin"
DOMAIN = DOMAINS[DOMAIN_NAME]
```

Change `DOMAIN_NAME` to any name listed by
`python examples/render_satellite.py --list-domains`, or set `DOMAIN` directly to
your own `(MIN_LON, MIN_LAT, MAX_LON, MAX_LAT)` box in decimal degrees. The same
names work on the command line, for example `--domain shishaldin`.

The first mapped output may download 10 m Natural Earth coastlines to
`output/.cartopy/`. Both `data/` and `output/` are excluded from Git; the
executed PNG remains embedded in the notebook.
