#!/usr/bin/env python3
"""Render GOES ABI or VIIRS SDR files with Satpy."""

from __future__ import annotations

import argparse
import glob
import math
import os
import sys
from pathlib import Path
from typing import Iterable

try:
    from .domains import DOMAINS, list_domains
except ImportError:
    from domains import DOMAINS, list_domains


SUPPORTED_SUFFIXES = {".nc", ".nc4", ".h5", ".hdf5"}
DEFAULT_DOMAIN_RESOLUTION = 0.02
READERS = {
    "goes": "abi_l1b",
    "viirs": "viirs_sdr",
}
VIIRS_GEO_PREFIXES = ("GITCO_", "GMTCO_", "GDNBO_", "GIMGO_", "GMODO_")

# Composite names that trigger the day/night True Color blend (see day_night.py).
DAY_NIGHT_COMPOSITES = {"day_night", "true_color_night", "true_color_day_night"}


def expand_inputs(values: Iterable[str]) -> list[str]:
    """Expand files, directories, and quoted glob patterns deterministically."""
    files: set[Path] = set()

    for value in values:
        path = Path(value).expanduser()
        if path.is_dir():
            files.update(
                candidate.resolve()
                for candidate in path.rglob("*")
                if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_SUFFIXES
            )
            continue

        for match in glob.glob(str(path), recursive=True):
            candidate = Path(match)
            if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_SUFFIXES:
                files.add(candidate.resolve())

    return [str(path) for path in sorted(files)]


def has_viirs_geolocation(files: Iterable[str]) -> bool:
    """Return whether a VIIRS geolocation file is present."""
    return any(Path(filename).name.startswith(VIIRS_GEO_PREFIXES) for filename in files)


def create_scene(sensor: str, files: list[str]):
    """Create a Satpy Scene while keeping Satpy an optional import for --help/tests."""
    try:
        from satpy import Scene
    except ImportError as exc:
        raise SystemExit(
            "Satpy is not installed. Run: python -m pip install -r requirements.txt"
        ) from exc

    return Scene(reader=READERS[sensor], filenames=files)


def available_composites(scene) -> list[str]:
    """Return sorted composite names from a Satpy Scene."""
    return sorted(str(name) for name in scene.available_composite_names())


def validate_bbox(values: Iterable[float]) -> tuple[float, float, float, float]:
    """Validate a min_lon, min_lat, max_lon, max_lat bounding box."""
    min_lon, min_lat, max_lon, max_lat = (float(value) for value in values)
    if not (-180 <= min_lon < max_lon <= 180):
        raise ValueError(
            "invalid longitude limits: use -180 <= MIN_LON < MAX_LON <= 180"
        )
    if not (-90 <= min_lat < max_lat <= 90):
        raise ValueError(
            "invalid latitude limits: use -90 <= MIN_LAT < MAX_LAT <= 90"
        )
    return min_lon, min_lat, max_lon, max_lat


def resolve_bbox(
    domain: Iterable[float] | None,
) -> tuple[float, float, float, float] | None:
    """Validate a user-provided geographic domain (four numbers)."""
    return validate_bbox(domain) if domain is not None else None


def resolve_domain_tokens(
    tokens: Iterable[str] | None,
) -> tuple[float, float, float, float] | None:
    """Resolve ``--domain`` input that is a named domain OR four numbers.

    Accepts either a single name from ``domains.py`` (for example
    ``shishaldin``) or four decimal-degree values ``MIN_LON MIN_LAT MAX_LON
    MAX_LAT``. Returns ``None`` when nothing was supplied.
    """
    if tokens is None:
        return None
    tokens = list(tokens)
    if len(tokens) == 1:
        name = tokens[0]
        if name in DOMAINS:
            return validate_bbox(DOMAINS[name])
        known = ", ".join(sorted(DOMAINS)) or "none defined"
        raise ValueError(
            f"unknown domain '{name}'. Named domains: {known}. "
            "Or pass four numbers: MIN_LON MIN_LAT MAX_LON MAX_LAT."
        )
    if len(tokens) == 4:
        return validate_bbox([float(value) for value in tokens])
    raise ValueError(
        "--domain expects a single domain name or four numbers "
        "MIN_LON MIN_LAT MAX_LON MAX_LAT."
    )


def create_lonlat_area(
    domain: Iterable[float],
    *,
    resolution: float = DEFAULT_DOMAIN_RESOLUTION,
    area_id: str = "user_lonlat_domain",
):
    """Create a regular WGS84 longitude/latitude grid for a user domain."""
    bounds = validate_bbox(domain)
    resolution = float(resolution)
    if resolution <= 0:
        raise ValueError("resolution must be greater than zero decimal degrees")

    try:
        from pyresample import create_area_def
    except ImportError as exc:
        raise SystemExit(
            "Pyresample is not installed. Run: python -m pip install -r requirements.txt"
        ) from exc

    return create_area_def(
        area_id,
        {"proj": "longlat", "datum": "WGS84"},
        area_extent=bounds,
        resolution=(resolution, resolution),
        units="degrees",
        description="User-defined longitude/latitude domain",
    )


def add_domain_argument(parser: argparse.ArgumentParser) -> None:
    """Add the geographic domain: a named domain or four numbers."""
    parser.add_argument(
        "--domain",
        nargs="+",
        metavar="DOMAIN",
        help=(
            "Named domain from domains.py (for example 'shishaldin'), or four "
            "decimal-degree values MIN_LON MIN_LAT MAX_LON MAX_LAT (for example "
            "-166.0 54.0 -162.0 56.0). Use --list-domains to see the names. "
            "Omit it to keep the full source extent."
        ),
    )


def crop_and_resample_scene(
    scene,
    *,
    domain: Iterable[float] | None,
    area: str | None = None,
    resolution: float = DEFAULT_DOMAIN_RESOLUTION,
    native_projection: bool = False,
):
    """Crop to a domain and put the result on the output grid.

    ``domain`` is an already-resolved bounding box ``(min_lon, min_lat,
    max_lon, max_lat)`` or ``None``.

    By default a cropped scene is placed on a regular (flat) WGS84 lon/lat
    grid, so every image uses the same rectangular projection with straight
    gridlines, whatever the sensor or crop.

    * ``area`` — resample to an explicit Satpy area (advanced override).
    * ``native_projection`` — keep the satellite's own projection instead
      (geostationary for GOES). Ignored for VIIRS, an orbital swath with no
      single fixed projection.
    """
    bounds = resolve_bbox(domain)

    if area:
        return scene.resample(area)

    if bounds is None:
        # No crop: keep every dataset on its native grid.
        return scene.resample(resampler="native")

    if native_projection:
        try:
            # Geostationary sources (GOES ABI) crop in-place and keep their
            # native projection; only the extent shrinks to the domain.
            cropped = scene.crop(ll_bbox=bounds)
            return cropped.resample(resampler="native")
        except (NotImplementedError, KeyError):
            # Swath sources (VIIRS) fall through to the regular lon/lat grid.
            pass

    # Default: regular flat lon/lat grid limited to the user domain.
    lonlat_area = create_lonlat_area(bounds, resolution=resolution)
    return scene.resample(lonlat_area)


def resample_to_max_size(scene, composite: str, *, max_size: int = 1600):
    """Resample one source coverage and generate its composite at a bounded size."""
    if max_size <= 0:
        raise ValueError("max_size must be greater than zero pixels")

    try:
        dataset = scene[composite]
    except KeyError:
        # Multi-resolution composites such as ABI True Color are put on the
        # wishlist by Scene.load(), but Satpy can only create them after their
        # prerequisite channels share one area. Use the coarsest prerequisite
        # grid as the native target; Scene.resample() then generates the
        # requested composite.
        area = scene.coarsest_area()
    else:
        area = dataset.attrs.get("area")
    if area is None:
        raise ValueError(f"Dataset '{composite}' has no area information.")

    factor = max(1, math.ceil(max(area.width, area.height) / max_size))
    target_area = area.aggregate(x=factor, y=factor) if factor > 1 else area
    try:
        resampled = scene.resample(target_area, resampler="native")
    except ValueError:
        # Native aggregation requires integer scale factors. Fall back to the
        # general resampler for unusual source dimensions.
        resampled = scene.resample(target_area)

    try:
        resampled[composite]
    except KeyError:
        resampled.load([composite], generate=True)
        try:
            resampled[composite]
        except KeyError as exc:
            raise ValueError(
                f"Composite '{composite}' could not be generated after resampling."
            ) from exc
    return resampled


def save_dataset_with_lonlat_grid(
    scene,
    composite: str,
    output: str | Path,
    *,
    title: str | None = None,
    dpi: int = 150,
    coastline_resolution: str = "10m",
    image=None,
) -> Path:
    """Save a dataset with projected lon/lat grid lines and coastlines.

    ``image`` may be a ready PIL image (for example a day/night blend). When
    given it is drawn as-is with no Satpy enhancement, and ``composite`` is
    used only to read the area and geometry.
    """
    output_path = Path(output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from cartopy import config as cartopy_config
        import cartopy.crs as ccrs
        import matplotlib.pyplot as plt
        from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter
        from matplotlib.ticker import MaxNLocator
        import numpy as np
        from satpy.enhancements.enhancer import get_enhanced_image
    except ImportError as exc:
        raise SystemExit(
            "Map plotting dependencies are missing. Run: "
            "python -m pip install -r requirements.txt"
        ) from exc

    cartopy_data_dir = Path(
        os.environ.get("CARTOPY_DATA_DIR", output_path.parent / ".cartopy")
    )
    cartopy_data_dir.mkdir(parents=True, exist_ok=True)
    cartopy_config["data_dir"] = str(cartopy_data_dir)

    dataset = scene[composite]
    area = dataset.attrs.get("area")
    if area is None:
        raise ValueError(
            f"Dataset '{composite}' has no area information for a longitude/latitude grid."
        )

    enhanced = image if image is not None else get_enhanced_image(dataset).pil_image()
    projection = area.to_cartopy_crs()
    width, height = enhanced.size
    aspect = width / max(height, 1)
    figure_width = min(14.0, max(8.0, 8.0 * aspect))
    figure_height = min(11.0, max(5.0, figure_width / max(aspect, 0.5)))

    figure = plt.figure(figsize=(figure_width, figure_height), facecolor="white")
    if area.crs.is_geographic:
        min_lon, min_lat, max_lon, max_lat = area.area_extent
        plate_carree = ccrs.PlateCarree()
        axis = figure.add_subplot(1, 1, 1, projection=plate_carree)
        axis.imshow(
            enhanced,
            transform=plate_carree,
            extent=(min_lon, max_lon, min_lat, max_lat),
            origin="upper",
            zorder=0,
        )
        axis.set_extent(
            (min_lon, max_lon, min_lat, max_lat),
            crs=plate_carree,
        )
        longitude_ticks = MaxNLocator(nbins=8).tick_values(min_lon, max_lon)
        latitude_ticks = MaxNLocator(nbins=6).tick_values(min_lat, max_lat)
        longitude_ticks = longitude_ticks[
            (longitude_ticks >= min_lon) & (longitude_ticks <= max_lon)
        ]
        latitude_ticks = latitude_ticks[
            (latitude_ticks >= min_lat) & (latitude_ticks <= max_lat)
        ]
        axis.set_xticks(longitude_ticks, crs=plate_carree)
        axis.set_yticks(latitude_ticks, crs=plate_carree)
        axis.xaxis.set_major_formatter(LongitudeFormatter())
        axis.yaxis.set_major_formatter(LatitudeFormatter())
        axis.tick_params(labelsize=9)
        axis.grid(
            visible=True,
            linewidth=0.65,
            color="white",
            alpha=0.8,
            linestyle="--",
            zorder=2,
        )
    else:
        axis = figure.add_subplot(1, 1, 1, projection=projection)
        axis.imshow(
            enhanced,
            transform=projection,
            extent=projection.bounds,
            origin="upper",
            zorder=0,
        )
        x_lo, x_hi = projection.bounds[0], projection.bounds[1]
        y_lo, y_hi = projection.bounds[2], projection.bounds[3]
        axis.set_xlim(x_lo, x_hi)
        axis.set_ylim(y_lo, y_hi)

        # Dashed lon/lat graticule, curved in the satellite projection. Cartopy
        # cannot cleanly label a skewed geostationary frame, so draw the lines
        # unlabeled and place labels on the edges manually below.
        axis.gridlines(
            crs=ccrs.PlateCarree(),
            draw_labels=False,
            linewidth=0.65,
            color="white",
            alpha=0.8,
            linestyle="--",
        )

        # Latitude labels where nice parallels cross the left edge; longitude
        # labels where nice meridians cross the bottom edge.
        geodetic = ccrs.PlateCarree()
        samples = 400
        left_y = np.linspace(y_lo, y_hi, samples)
        left_lat = geodetic.transform_points(
            projection, np.full(samples, x_lo), left_y
        )[:, 1]
        bottom_x = np.linspace(x_lo, x_hi, samples)
        bottom_lon = geodetic.transform_points(
            projection, bottom_x, np.full(samples, y_lo)
        )[:, 0]

        def _format_lat(value: float) -> str:
            return f"{abs(value):g}°{'N' if value >= 0 else 'S'}"

        def _format_lon(value: float) -> str:
            return f"{abs(value):g}°{'E' if value >= 0 else 'W'}"

        lat_order = np.argsort(left_lat)
        lat_sorted, y_sorted = left_lat[lat_order], left_y[lat_order]
        lat_values = [
            value
            for value in MaxNLocator(nbins=6).tick_values(lat_sorted[0], lat_sorted[-1])
            if lat_sorted[0] <= value <= lat_sorted[-1]
        ]
        axis.set_yticks(np.interp(lat_values, lat_sorted, y_sorted))
        axis.set_yticklabels([_format_lat(value) for value in lat_values])

        lon_order = np.argsort(bottom_lon)
        lon_sorted, x_sorted = bottom_lon[lon_order], bottom_x[lon_order]
        lon_values = [
            value
            for value in MaxNLocator(nbins=8).tick_values(lon_sorted[0], lon_sorted[-1])
            if lon_sorted[0] <= value <= lon_sorted[-1]
        ]
        axis.set_xticks(np.interp(lon_values, lon_sorted, x_sorted))
        axis.set_xticklabels([_format_lon(value) for value in lon_values])
        axis.tick_params(labelsize=9)

    axis.coastlines(
        resolution=coastline_resolution,
        color="#1a1a1a",
        linewidth=0.75,
        zorder=3,
    )

    if title:
        figure.suptitle(title, fontsize=13, y=0.975)
    figure.text(
        0.5,
        0.015,
        "Longitude / Latitude grid (WGS 84)",
        ha="center",
        fontsize=8,
        color="#333333",
    )

    figure.subplots_adjust(left=0.08, right=0.98, bottom=0.09, top=0.91)
    figure.savefig(
        output_path,
        dpi=dpi,
        facecolor="white",
    )
    plt.close(figure)
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render GOES ABI or VIIRS SDR files as a PNG image."
    )
    parser.add_argument("--sensor", choices=sorted(READERS))
    parser.add_argument(
        "--files",
        nargs="+",
        help="Files, directories, or glob patterns. Quote glob patterns.",
    )
    parser.add_argument(
        "--composite",
        default="true_color",
        help=(
            "Satpy composite name (default: true_color). Use 'day_night' for a "
            "True Color image that also shows clouds at night."
        ),
    )
    parser.add_argument(
        "--output",
        default="output/satellite.png",
        help="Output PNG path.",
    )
    parser.add_argument(
        "--area",
        help="Optional Satpy area for resampling, for example 'eurol'.",
    )
    add_domain_argument(parser)
    parser.add_argument(
        "--resolution",
        type=float,
        default=DEFAULT_DOMAIN_RESOLUTION,
        help=(
            "Output grid spacing in decimal degrees when --domain is used "
            f"(default: {DEFAULT_DOMAIN_RESOLUTION})."
        ),
    )
    parser.add_argument(
        "--native-projection",
        action="store_true",
        help=(
            "Keep the satellite's own projection (geostationary for GOES) "
            "instead of the default flat WGS84 lon/lat grid."
        ),
    )
    parser.add_argument(
        "--plain-image",
        action="store_true",
        help="Save without longitude/latitude grid lines or coordinate labels.",
    )
    parser.add_argument(
        "--list-composites",
        action="store_true",
        help="List available composites and exit without creating an image.",
    )
    parser.add_argument(
        "--list-domains",
        action="store_true",
        help="List the named domains from domains.py and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_domains:
        print(list_domains())
        return 0

    if not args.sensor:
        parser.error("--sensor is required (choose from goes, viirs).")
    if not args.files:
        parser.error("--files is required.")

    files = expand_inputs(args.files)

    if not files:
        parser.error("No NetCDF/HDF5 files matched --files.")

    try:
        bbox = resolve_domain_tokens(args.domain)
        if args.resolution <= 0:
            raise ValueError("resolution must be greater than zero decimal degrees")
    except ValueError as exc:
        parser.error(str(exc))

    if args.sensor == "viirs" and not has_viirs_geolocation(files):
        print(
            "Warning: no GITCO, GMTCO, GDNBO, GIMGO, or GMODO file was found. "
            "Most VIIRS products require a matching geolocation file.",
            file=sys.stderr,
        )

    scene = create_scene(args.sensor, files)
    composites = available_composites(scene)

    if args.list_composites:
        print("\n".join(composites))
        return 0

    if args.composite in DAY_NIGHT_COMPOSITES:
        return _render_day_night(args, scene, composites, bbox)

    composite = args.composite
    if composite not in composites and composite == "true_color" and "true_color_raw" in composites:
        composite = "true_color_raw"
        print("The reader provides true_color_raw; using it as a fallback.")

    if composite not in composites:
        preview = ", ".join(composites[:20]) or "none"
        raise SystemExit(
            f"Composite '{args.composite}' cannot be created from these files. "
            f"Available: {preview}. Use --list-composites for the complete list."
        )

    scene.load([composite], generate=True)
    output_scene = crop_and_resample_scene(
        scene,
        domain=bbox,
        area=args.area,
        resolution=args.resolution,
        native_projection=args.native_projection,
    )

    output = Path(args.output).expanduser()
    if args.plain_image:
        output.parent.mkdir(parents=True, exist_ok=True)
        output_scene.save_dataset(composite, filename=str(output), writer="simple_image")
    else:
        save_dataset_with_lonlat_grid(
            output_scene,
            composite,
            output,
            title=f"{args.sensor.upper()} {composite.replace('_', ' ').title()}",
        )
    print(f"Image created: {output.resolve()}")
    return 0


def _render_day_night(args, scene, composites, bbox) -> int:
    """Render a day/night True Color image (real color by day, clouds by night)."""
    try:
        from .day_night import compose_day_night_image, night_source_names
    except ImportError:
        from day_night import compose_day_night_image, night_source_names

    if "true_color" not in composites:
        raise SystemExit(
            "day_night needs the 'true_color' composite, which cannot be built "
            "from these files. Download the True Color channels first "
            "(GOES C01/C02/C03, or VIIRS M03/M04/M05)."
        )

    # Load the daytime composite plus the first night source that actually
    # loads from these files (a channel like C13, or the DNB composite).
    scene.load(["true_color"], generate=True)
    night_candidates = night_source_names(args.sensor, composites)
    night_loaded = None
    for name in night_candidates:
        scene.load([name])
        try:
            scene[name]
        except KeyError:
            continue
        night_loaded = name
        break
    if night_loaded is None:
        raise SystemExit(
            "No night source could be loaded for the day/night blend. Expected "
            f"one of: {', '.join(night_candidates)}. For GOES download C13; for "
            "VIIRS download the Day/Night Band (SVDNB + GDNBO) or an infrared "
            "band (I05 or M15)."
        )

    output_scene = crop_and_resample_scene(
        scene,
        domain=bbox,
        area=args.area,
        resolution=args.resolution,
        native_projection=args.native_projection,
    )

    image, used_night = compose_day_night_image(output_scene, args.sensor)
    print(f"Day/night blend: day='true_color', night source='{used_night}'.")

    output = Path(args.output).expanduser()
    if args.plain_image:
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(output))
    else:
        save_dataset_with_lonlat_grid(
            output_scene,
            "true_color",
            output,
            title=f"{args.sensor.upper()} True Color (Day/Night)",
            image=image,
        )
    print(f"Image created: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
