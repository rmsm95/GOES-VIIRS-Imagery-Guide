# GOES and VIIRS Imagery

A practical guide to turning NOAA GOES ABI and JPSS VIIRS files into satellite images and RGB composites.

This repository complements the [GOES & JPSS Data Downloader](https://rmsm95.github.io/GOES-NESDIS_downlaoder/). Preview GOES data in Google Earth Engine, download the files you need, and render the imagery locally.

## Quick start

### 1. Preview GOES before downloading

Open the [GOES viewer in Google Earth Engine](https://ruimota16.users.earthengine.app/view/testapp). The viewer lets you inspect the satellite, source coverage, date, time, and visualization before downloading large files.

The viewer is still being tested and developed.

### 2. Prepare Python

Python 3.11 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Create a GOES True Color image

Download ABI channels `C01`, `C02`, and `C03` from the same observation. Then
choose an area with `--domain`, using either a **named domain** or **four
numbers**.

List the named domains (they live in `examples/domains.py` and are yours to
edit):

```bash
python examples/render_satellite.py --list-domains
```

Render using a name:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "data/goes/*.nc" \
  --composite true_color \
  --domain shishaldin \
  --output output/goes_shishaldin_true_color.png
```

Or pass the four limits directly, in `MIN_LON MIN_LAT MAX_LON MAX_LAT` order and
decimal degrees:

```bash
  --domain -166.0 54.0 -162.0 56.0
```

The named domains are only **examples**. Open `examples/domains.py` to add or
change boxes for your own study areas.

Cropped output is placed on a regular lon/lat grid and drawn as a plain
rectangular map: degree ticks, a graticule, coastlines, and the scan time in the
header. Add `--native-projection` only if you want the satellite's own
geostationary frame instead. See
[Choosing source coverage and a domain](docs/DOMAINS.md).

To render the entire extent of the downloaded GOES file, omit `--domain`. For a true Full Disk image, the input files themselves must be ABI `F` products such as `ABI-L1b-RadF`.

GOES ABI does not have a pure green channel. True Color synthesizes green from the blue, red, and vegetation channels.

Saved images include longitude/latitude grid lines, coordinate labels, and
Natural Earth coastlines by default. The first mapped output may download the
coastline dataset to `output/.cartopy/`, which is excluded from Git. Use
`--plain-image` only when a borderless image is required.

### 4. Create a VIIRS True Color image

Keep the required spectral bands and matching geolocation files in the same directory:

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "data/viirs/*.h5" \
  --composite true_color \
  --domain -166.0 54.0 -162.0 56.0 \
  --output output/viirs_shishaldin_true_color.png
```

The user defines the VIIRS domain with the same longitude/latitude order. The downloaded swath must intersect the requested box.

For recent SDR products, prefer terrain-corrected geolocation: `GITCO` for I bands and `GMTCO` for M bands.

### 5. Create a Day/Night True Color image

Plain True Color is black at night. The `day_night` composite keeps real color
by day and shows clouds at night, blending across twilight by the sun's angle:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "data/goes/*.nc" \
  --composite day_night \
  --domain shishaldin \
  --output output/goes_day_night.png
```

At night the clouds come from the clean infrared window band `C13` (10.3 µm) for
GOES, or the Day/Night Band (`dynamic_dnb`, needs `SVDNB` + `GDNBO`) for VIIRS,
falling back to an infrared band (`I05`/`M15`) when the DNB is absent. So for
GOES download `C13` alongside `C01`/`C02`/`C03`. See
[How RGB composites work](docs/RGB.md#daynight-true-color) for the recipe and
tunable limits.

## Source coverage versus output domain

These are separate decisions:

- GOES source coverage comes from the downloaded product: `F` for Full Disk, `C` for CONUS, or `M` for Mesoscale.
- The output domain is always entered by the user with `--domain MIN_LON MIN_LAT MAX_LON MAX_LAT`.
- Omitting `--domain` keeps the complete extent available in the source files.
- Cropping cannot create observations outside the original GOES coverage or VIIRS swath.

See [Choosing source coverage and a domain](docs/DOMAINS.md) for examples.

## Discover available RGB composites

Available RGBs depend on the channels found in the input files:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "data/goes/*.nc" \
  --list-composites
```

Common examples include:

- `true_color`: a daytime view close to human vision;
- `natural_color`: emphasizes vegetation, soil, snow, and cloud types;
- `airmass`: supports interpretation of air masses and upper-level dynamics;
- `night_microphysics`: separates fog, low clouds, and ice clouds at night.
- `ash`: GOES ABI Ash RGB using C11, C13, C14, and C15;
- `volcanic_emissions`: the current Satpy name for the GOES SO₂ RGB using C09,
  C10, C11, and C13.

Read [How RGB composites work](docs/RGB.md) for channel recipes, brightness-temperature differences, normalization, and gamma.

## Complete runnable examples

If you do not have prepared files, these scripts download public demonstration data and create an image:

- [GOES ABI True Color](examples/demo_goes_true_color.py)
- [Suomi NPP VIIRS True Color](examples/demo_viirs_true_color.py)
- [Commands and step-by-step explanation](examples/README.md)

```bash
python examples/demo_goes_true_color.py
python examples/demo_viirs_true_color.py
```

Demo downloads can be several hundred megabytes. Files are stored under `data/demo-*` and are excluded from Git.

## JupyterLab tutorials

The notebooks are executed examples that keep the explanation, editable code,
and the exact resulting satellite image together:

- [Full Disk, one band (10.3 µm)](notebooks/01_full_disk_band.ipynb)
- [CONUS sector](notebooks/02_conus.ipynb)
- [Mesoscale sector](notebooks/03_mesoscale.ipynb)
- [True Color](notebooks/04_true_color.ipynb)
- [Ash RGB](notebooks/05_ash_rgb.ipynb)
- [SO₂ / Volcanic Emissions RGB](notebooks/06_so2_rgb.ipynb)
- [GLM lightning over True Color](notebooks/07_glm_true_color.ipynb)
- [VIIRS True Color](notebooks/08_viirs_true_color.ipynb)
- [JupyterLab setup and input guide](notebooks/README.md)

Install and start JupyterLab from the repository root:

```bash
python -m pip install -r requirements-notebooks.txt
python -m jupyter lab
```

GitHub displays every saved result without requiring JupyterLab. Each notebook
follows the same four steps: get the data from a folder, plot the **complete**
product, choose a **domain**, then plot that domain. The GOES notebooks use
public GOES-18 data from **3 October 2023 at 19:00 UTC**; the GLM notebook uses
GOES-16 at 20:00 UTC over a line of thunderstorms in the central United States.

The whole stack is pinned in [`environment.yml`](environment.yml):

```bash
conda env create -f environment.yml
conda activate goes-viirs
```

## Repository structure

```text
.
├── docs/
│   ├── RGB.md
│   ├── DOMAINS.md
│   └── WORKFLOW.md
├── examples/
│   ├── README.md
│   ├── day_night.py            # day/night True Color blend
│   ├── demo_goes_true_color.py
│   ├── demo_viirs_true_color.py
│   ├── domains.py              # named, editable geographic domains
│   ├── glm.py                  # GLM lightning flashes
│   ├── goes18_coverage_data.py
│   └── render_satellite.py
├── notebooks/
│   ├── README.md
│   ├── 01_full_disk_band.ipynb
│   ├── 02_conus.ipynb
│   ├── 03_mesoscale.ipynb
│   ├── 04_true_color.ipynb
│   ├── 05_ash_rgb.ipynb
│   ├── 06_so2_rgb.ipynb
│   ├── 07_glm_true_color.ipynb
│   └── 08_viirs_true_color.ipynb
├── tests/
│   ├── test_goes18_coverage_data.py
│   ├── test_notebooks.py
│   └── test_render_satellite.py
├── environment.yml
├── requirements-notebooks.txt
└── requirements.txt
```

## Technical sources

- [Satpy: remote reading for GOES ABI](https://satpy.readthedocs.io/en/stable/remote_reading.html)
- [Satpy: VIIRS SDR reader](https://satpy.readthedocs.io/en/stable/api/satpy.readers.viirs_sdr.html)
- [Satpy Scene cropping](https://satpy.readthedocs.io/en/stable/api/satpy.scene.html)
- [NOAA: CIMSS Natural True Color guide](https://www.star.nesdis.noaa.gov/GOES/documents/ABIQuickGuide_CIMSSRGB_v2.pdf)
- [NOAA: Day Land Cloud RGB guide](https://www.star.nesdis.noaa.gov/goes/documents/QuickGuide_GOESR_daylandcloudRGB_final.pdf)
- [CIRA: GOES Ash RGB guide](https://rammb.cira.colostate.edu/training/visit/quick_guides/GOES_Ash_RGB.pdf)
- [CIRA: GOES SO₂ RGB guide](https://rammb.cira.colostate.edu/training/rmtc/docs/QuickGuides/Quick_Guide_SO2_RGB.pdf)
- [USGS/AVO: Shishaldin update for 3 October 2023](https://volcanoes.usgs.gov/hans-public/notice/DOI-USGS-AVO-2023-10-03T11%3A47%3A46-08%3A00)
- [NOAA CLASS: VIIRS SDR and geolocation](https://www.class.noaa.gov/search/VIIRS_SDR)

Data remains the property of its respective producer. Always review the source terms and operational notices.

## License

Code is available under the [MIT License](LICENSE). This license does not change the terms of external data, images, or documentation.
