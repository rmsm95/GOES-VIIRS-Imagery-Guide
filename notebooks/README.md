# JupyterLab tutorials

These notebooks show the code and display the rendered satellite image in the
same document:

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

## Required input

The notebooks use files downloaded by the user:

- GOES: place matching ABI channels in `data/goes/`;
- VIIRS: place matching spectral bands and geolocation files in `data/viirs/`.

The domain is always entered by the user in decimal degrees:

```python
DOMAIN = (-166.0, 54.0, -162.0, 56.0)
```

The order is `MIN_LON, MIN_LAT, MAX_LON, MAX_LAT`. Use `.0` for whole degrees
and values such as `.5` when needed. The coordinates must intersect the GOES
source coverage or VIIRS swath.

The final cell displays the generated PNG directly inside JupyterLab.
