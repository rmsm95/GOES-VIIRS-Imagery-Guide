# JupyterLab tutorials

These notebooks are executed examples. GitHub shows the code and the exact
satellite image produced by the cells in the same document:

- [`01_GOES_true_color.ipynb`](01_GOES_true_color.ipynb): GOES ABI True Color;
- [`02_VIIRS_true_color.ipynb`](02_VIIRS_true_color.ipynb): JPSS VIIRS True Color.

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

On the first local execution, the notebooks download public Satpy demonstration
data:

- GOES: an official GOES-16 ABI CONUS example;
- VIIRS: one Suomi NPP granule with I/M bands and geolocation.

The executed demo domains are written in decimal degrees and intersect their
respective source files. The resulting PNG is embedded in the notebook, so it
is visible without running JupyterLab.

## Use your own domain

For Shishaldin, replace the demo input with matching downloaded files and enter:

```python
DOMAIN = (-166.0, 54.0, -162.0, 56.0)
```

The order is `MIN_LON, MIN_LAT, MAX_LON, MAX_LAT`. Use `.0` for whole degrees
and values such as `.5` when needed. The coordinates must intersect the GOES
source coverage or VIIRS swath.

The final cells regenerate and display the PNG directly inside JupyterLab.
