# Runnable examples

The three scripts cover different situations:

| Example | Data | Result |
|---|---|---|
| `demo_goes_true_color.py` | Automatically downloads an official Satpy GOES ABI demo dataset | `output/demo_goes_true_color.png` |
| `demo_viirs_true_color.py` | Automatically downloads a Suomi NPP pass with I/M bands and geolocation | `output/demo_viirs_true_color.png` |
| `render_satellite.py` | Uses your own NOAA files | A mapped PNG with the selected composite |

Mapped PNGs include longitude/latitude labels, grid lines, and coastlines by
default. Use `--plain-image` to omit these map elements.

The executed GOES notebooks use
[`goes18_coverage_data.py`](goes18_coverage_data.py) to identify separate
Full Disk, CONUS, and Mesoscale 1 NOAA files from the 3 October 2023 19:00 UTC
window. The source lists are explicit so a coverage name can never silently
become a crop of another product.

## Demo 1 — GOES True Color

```bash
python examples/demo_goes_true_color.py
```

The example:

1. downloads GOES-16 ABI data from March 14, 2019;
2. opens the files with the `abi_l1b` reader;
3. creates `true_color` or `true_color_raw`, depending on the Satpy version;
4. resamples channels to a common grid;
5. writes `output/demo_goes_true_color.png`.

You can select other directories and enter your own domain:

```bash
python examples/demo_goes_true_color.py \
  --data-dir data/goes-cyclone \
  --domain -102.0 25.0 -84.0 38.0 \
  --output output/goes_cyclone.png
```

The demo source is CONUS. The four domain values must intersect that source.

## Demo 2 — Suomi NPP VIIRS True Color

```bash
python examples/demo_viirs_true_color.py
```

The example downloads one granule and the required channels:

- `M03`, `M04`, `M05`: blue, green, and red;
- `I01`, `I02`: higher-resolution detail for ratio sharpening;
- terrain-corrected geolocation included with the demo dataset.

It then combines the bands with the `viirs_sdr` reader, resamples I/M resolutions, and writes `output/demo_viirs_true_color.png`.

The user can crop the result by entering longitude and latitude limits:

```bash
python examples/demo_viirs_true_color.py \
  --domain -95.0 26.0 -80.0 36.0 \
  --output output/viirs_domain.png
```

The entered box must intersect the downloaded demo swath.

## Example 3 — user-downloaded files

### GOES True Color for a user-defined Shishaldin domain

In the downloader, select `C01`, `C02`, and `C03` from the same scan. Then
enter the domain as `MIN_LON MIN_LAT MAX_LON MAX_LAT`. Write every value in
decimal degrees, including `.0` for whole degrees:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "data/goes/OR_ABI-L1b-RadF-M6C0[123]*.nc" \
  --composite true_color \
  --domain -166.0 54.0 -162.0 56.0 \
  --output output/goes_shishaldin_true_color.png
```

The Shishaldin values are an example typed by the user, not a named or automatic preset.

### GOES Full Disk

Use ABI `F` source files and omit `--domain`:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "data/goes/OR_ABI-L1b-RadF-M6C0[123]*.nc" \
  --composite true_color \
  --output output/goes_full_disk_true_color.png
```

### GOES Day Land Cloud

Download `C02`, `C03`, and `C05`:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "data/goes/OR_ABI-L1b-RadF-M6C0[235]*.nc" \
  --composite natural_color \
  --domain -166.0 54.0 -162.0 56.0 \
  --output output/goes_day_land_cloud.png
```

### GOES Nighttime Microphysics

Download `C07`, `C13`, and `C15`:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "data/goes/*.nc" \
  --composite night_microphysics \
  --domain -166.0 54.0 -162.0 56.0 \
  --output output/goes_night_microphysics.png
```

### GOES Ash RGB

Download C11, C13, C14, and C15 from the same scan:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "data/goes/*.nc" \
  --composite ash \
  --domain -170.0 53.0 -160.0 58.0 \
  --output output/goes_ash_rgb.png
```

### GOES SO₂ / Volcanic Emissions RGB

Download C09, C10, C11, and C13 from the same scan. `volcanic_emissions` is
the current Satpy name; the older `so2` composite is deprecated.

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "data/goes/*.nc" \
  --composite volcanic_emissions \
  --domain -170.0 53.0 -160.0 58.0 \
  --output output/goes_so2_rgb.png
```

### VIIRS True Color

Keep bands and matching geolocation from the same pass together:

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "data/viirs/*.h5" \
  --composite true_color \
  --domain -166.0 54.0 -162.0 56.0 \
  --output output/viirs_shishaldin_true_color.png
```

If the composite is absent:

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "data/viirs/*.h5" \
  --list-composites
```

This distinguishes an incorrect composite name from missing bands or geolocation.
