# JupyterLab tutorials

Executed examples: GitHub shows the code and the exact image produced by it in
the same document.

Every notebook follows the same four steps:

1. **Get the data** — which folder the files are in, and download what is
   missing from the public NOAA bucket;
2. **Plot the complete product** — the whole Full Disk, CONUS or Mesoscale scan;
3. **Choose a domain** — a named box from
   [`examples/domains.py`](../examples/domains.py), or your own four numbers;
4. **Plot that domain** — cropped, on a regular lon/lat grid with coastlines,
   graticule and (for single bands) a colour bar.

## The notebooks

| Notebook | What it shows |
|---|---|
| [`01_full_disk_band.ipynb`](01_full_disk_band.ipynb) | Full Disk, one band (`C13`, 10.3 µm) in grey scale, then a domain with a colour bar |
| [`02_conus.ipynb`](02_conus.ipynb) | The CONUS sector: full extent, then a domain inside it |
| [`03_mesoscale.ipynb`](03_mesoscale.ipynb) | The Mesoscale 1 sector: full extent, then a domain inside it |
| [`04_true_color.ipynb`](04_true_color.ipynb) | True Color from the Full Disk, then the Shishaldin domain |
| [`05_ash_rgb.ipynb`](05_ash_rgb.ipynb) | Ash RGB from the Full Disk, then the Shishaldin domain |
| [`06_so2_rgb.ipynb`](06_so2_rgb.ipynb) | SO₂ / Volcanic Emissions RGB, same order |
| [`07_glm_true_color.ipynb`](07_glm_true_color.ipynb) | GLM lightning flashes drawn over a True Color image |
| [`08_viirs_true_color.ipynb`](08_viirs_true_color.ipynb) | A complete Suomi NPP VIIRS granule (not Shishaldin — see the notebook) |

## Environment

Create the environment once from
[`environment.yml`](../environment.yml) at the repository root:

```bash
conda env create -f environment.yml
conda activate goes-viirs
python -m jupyter lab
```

Then open the `notebooks` directory and run the cells top to bottom.

## Data

The GOES notebooks use GOES-18 ABI from **3 October 2023, 19:00 UTC** (the
nearest CONUS scan is 19:01 UTC). `download_coverage()` fetches only the files
that are missing, so re-running costs nothing.

The GLM notebook uses GOES-16 for **3 October 2023, 20:00 UTC**, over a line of
afternoon thunderstorms in the central United States, because that is where the
lightning is and there is daylight for True Color.

Which coverage contains what, on this date:

- **Full Disk** is the only product that covers Shishaldin, so the volcano
  domains come from it;
- **CONUS** for GOES-18 covers the western United States and does not reach
  Alaska;
- **Mesoscale 1** is a small sector, at this time off western Mexico.

Both `data/` and `output/` are excluded from Git; the executed PNG stays
embedded in the notebook.
