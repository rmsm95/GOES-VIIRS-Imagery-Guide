# Choosing source coverage and a domain

There are two separate spatial decisions:

1. choose the coverage of the source file;
2. enter the geographic domain to crop from that source.

A crop cannot create data that is absent from the source file.

## Two ways to give a domain

You can pass either a **named domain** or **four numbers**.

### Named domains (shortcut)

`examples/domains.py` holds a small, editable list of named boxes. List them:

```bash
python examples/render_satellite.py --list-domains
```

Then use a name instead of typing coordinates:

```text
--domain shishaldin
```

These names are only examples — open `examples/domains.py` and add, edit, or
remove entries for your own study areas. Each entry is
`"name": (MIN_LON, MIN_LAT, MAX_LON, MAX_LAT)`.

### Raw coordinates

You can always enter four longitude/latitude limits in decimal degrees instead:

```text
--domain MIN_LON MIN_LAT MAX_LON MAX_LAT
```

The limits must follow these rules:

```text
-180.0 <= MIN_LON < MAX_LON <= 180.0
 -90.0 <= MIN_LAT < MAX_LAT <= 90.0
```

Use negative longitude for locations west of Greenwich and negative latitude
for locations south of the equator. Write all four values as decimals, including
`.0` for whole degrees; half degrees can be written as `.5`.

### Example around Shishaldin

This is an example box entered directly by the user:

```bash
--domain -166.0 54.0 -162.0 56.0
```

It means:

| Argument | Value |
|---|---:|
| minimum longitude | `-166.0` |
| minimum latitude | `54.0` |
| maximum longitude | `-162.0` |
| maximum latitude | `56.0` |

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

Each source can still have its own independent user-defined domain. For
example, the notebooks use a `DOMAINS` dictionary:

```python
DOMAINS = {
    "full_disk": (-165.97, 52.76, -161.97, 56.76),
    "conus": (-125.0, 32.0, -115.0, 42.0),
    "mesoscale": (-112.0, 10.0, -104.0, 17.0),
}
```

The Full Disk box is centered on Shishaldin. The CONUS and Mesoscale boxes are
separate examples inside their own source extents. They cannot be centered on
Shishaldin when those source products do not cover Alaska.

To crop a GOES source to the user-defined Shishaldin example:

```bash
python examples/render_satellite.py \
  --sensor goes \
  --files "data/goes/*.nc" \
  --composite true_color \
  --domain -166.0 54.0 -162.0 56.0 \
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
  --domain -166.0 54.0 -162.0 56.0 \
  --output output/viirs_shishaldin.png
```

The crop reduces processing and output image size. It does not reduce bytes already downloaded. Inspect the orbit or granule geolocation first to avoid downloading VIIRS passes that do not cover the requested domain.

## Projection: flat lon/lat, by default

Cropping to a domain places the imagery on a regular (flat) WGS84 lon/lat grid,
so every image is a rectangular map with straight gridlines, whatever the sensor
or crop. This is the usual, consistent output.

Add `--native-projection` only if you want to keep the satellite's own
projection instead — geostationary for GOES (a slightly tilted frame away from
the sub-satellite point). VIIRS is an orbital swath with no single fixed
projection, so it always uses the flat lon/lat grid.

## Coordinate checklist

- Enter longitude first and latitude second.
- Enter the minimum corner before the maximum corner.
- Keep all four values in decimal degrees, for example `-166.0` or `-166.5`.
- Confirm that the box does not cross the antimeridian. A single `MIN_LON < MAX_LON` box cannot cross it.
- Confirm that all GOES channels come from the same scan.
- Confirm that VIIRS spectral and geolocation files come from the same granule.
