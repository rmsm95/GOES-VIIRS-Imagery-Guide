# Recommended workflow

## 1. Preview first

Use the [GOES viewer in Google Earth Engine](https://ruimota16.users.earthengine.app/view/testapp) to inspect:

- GOES-18 or GOES-19;
- Full Disk or Mesoscale source coverage;
- UTC date and time;
- visualization or product.

The viewer is still being tested and developed. Its purpose is to confirm the area, time, and phenomenon before downloading large files.

## 2. Download only what you need

Open the [GOES & JPSS Data Downloader](https://rmsm95.github.io/GOES-NESDIS_downlaoder/).

For GOES:

- select the same satellite, source coverage, date, and hour;
- download every channel required by the RGB;
- confirm that filenames have the same scan start time (`_s...`).

For VIIRS:

- choose Suomi NPP, NOAA-20, or NOAA-21;
- download the required spectral bands;
- add the matching geolocation files.

## 3. Define the output domain

The user must enter the geographic limits. The code does not choose a region automatically:

```text
--domain MIN_LON MIN_LAT MAX_LON MAX_LAT
```

Enter all four values in decimal degrees, including `.0` for whole degrees.

For example, a box around Shishaldin can be entered as:

```bash
--domain -166.0 54.0 -162.0 56.0
```

Change these four values for every study area. Omit `--domain` only when you want the complete extent contained in the source file.

## 4. Include VIIRS geolocation

VIIRS SDR data consists of swaths. Coordinates are not necessarily stored in the same file as the spectral band.

For recent data, prefer:

- `GITCO`: terrain-corrected geolocation for I bands;
- `GMTCO`: terrain-corrected geolocation for M bands;
- `GDNBO`: Day/Night Band geolocation.

NOAA directs users toward terrain-corrected `GITCO` and `GMTCO` geolocation for operational distribution. See the [NOAA CLASS VIIRS SDR page](https://www.class.noaa.gov/search/VIIRS_SDR).

Keep the band and geolocation files from the same pass in one directory. Satpy's `viirs_sdr` reader associates them through metadata.

## 5. Check available composites

Before rendering:

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "data/viirs/*.h5" \
  --list-composites
```

If an RGB is absent, at least one required band, geolocation file, or auxiliary file is missing.

## 6. Render and validate

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "data/viirs/*.h5" \
  --composite true_color \
  --domain -166.0 54.0 -162.0 56.0 \
  --output output/viirs_true_color.png
```

Validate:

- UTC date and time;
- satellite and sensor;
- geographic extent;
- scan lines, offsets, or missing areas;
- physical meaning of the colors;
- units and enhancements.
