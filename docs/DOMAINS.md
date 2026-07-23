# Choosing source coverage and a domain

There are two separate spatial decisions:

1. choose the coverage of the source file;
2. enter the geographic domain to crop from that source.

A crop cannot create data that is absent from the source file.

## The domain is always user-defined

The code contains no named geographic presets. Enter four longitude/latitude limits:

```text
--domain MIN_LON MIN_LAT MAX_LON MAX_LAT
```

The limits must follow these rules:

```text
-180 <= MIN_LON < MAX_LON <= 180
 -90 <= MIN_LAT < MAX_LAT <= 90
```

Use negative longitude for locations west of Greenwich and negative latitude for locations south of the equator.

### Example around Shishaldin

This is an example box entered directly by the user:

```bash
--domain -166 54 -162 56
```

It means:

| Argument | Value |
|---|---:|
| minimum longitude | `-166` |
| minimum latitude | `54` |
| maximum longitude | `-162` |
| maximum latitude | `56` |

Change the four values to match the exact study area and desired context. The command does not select Shishaldin or any other region automatically.

## GOES source coverage

ABI product names normally end with:

| Suffix | Source coverage | Example |
|---|---|---|
| `F` | Full Disk | `ABI-L1b-RadF` |
| `C` | CONUS | `ABI-L1b-RadC` |
| `M` | Mesoscale | `ABI-L1b-RadM` |

To render a real Full Disk image, download an `F` product and omit `--domain`:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "data/goes/full-disk/*.nc" \
  --composite true_color \
  --output output/goes_full_disk.png
```

A CONUS or Mesoscale file cannot be converted into Full Disk.

To crop a GOES source to the user-defined Shishaldin example:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "data/goes/*.nc" \
  --composite true_color \
  --domain -166 54 -162 56 \
  --output output/goes_shishaldin.png
```

The requested coordinates must intersect the selected satellite's source coverage.

## VIIRS swaths

VIIRS observes orbital swaths rather than a geostationary disk. The downloaded swath must intersect the domain, and its matching geolocation files must be present.

```bash
python examples/render_satellite.py \
  --sensor viirs \
  --files "data/viirs/*.h5" \
  --composite true_color \
  --domain -166 54 -162 56 \
  --output output/viirs_shishaldin.png
```

The crop reduces processing and output image size. It does not reduce bytes already downloaded. Inspect the orbit or granule geolocation first to avoid downloading VIIRS passes that do not cover the requested domain.

## Coordinate checklist

- Enter longitude first and latitude second.
- Enter the minimum corner before the maximum corner.
- Keep all four values in decimal degrees.
- Confirm that the box does not cross the antimeridian. A single `MIN_LON < MAX_LON` box cannot cross it.
- Confirm that all GOES channels come from the same scan.
- Confirm that VIIRS spectral and geolocation files come from the same granule.
