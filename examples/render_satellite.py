#!/usr/bin/env python3
"""Render GOES ABI or VIIRS SDR files with Satpy."""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path
from typing import Iterable


SUPPORTED_SUFFIXES = {".nc", ".nc4", ".h5", ".hdf5"}
READERS = {
    "goes": "abi_l1b",
    "viirs": "viirs_sdr",
}
VIIRS_GEO_PREFIXES = ("GITCO_", "GMTCO_", "GDNBO_", "GIMGO_", "GMODO_")


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
    """Validate a user-provided geographic domain."""
    return validate_bbox(domain) if domain is not None else None


def add_domain_argument(parser: argparse.ArgumentParser) -> None:
    """Add a geographic domain that must be entered by the user."""
    parser.add_argument(
        "--domain",
        nargs=4,
        type=float,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help=(
            "User-defined crop in longitude/latitude order: "
            "MIN_LON MIN_LAT MAX_LON MAX_LAT. Omit it to keep the source extent."
        ),
    )


def crop_and_resample_scene(
    scene,
    *,
    domain: Iterable[float] | None,
    area: str | None = None,
):
    """Crop a Scene geographically, then put all datasets on one grid."""
    bounds = resolve_bbox(domain)
    working_scene = scene.crop(ll_bbox=bounds) if bounds else scene
    return (
        working_scene.resample(area)
        if area
        else working_scene.resample(resampler="native")
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render GOES ABI or VIIRS SDR files as a PNG image."
    )
    parser.add_argument("--sensor", choices=sorted(READERS), required=True)
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Files, directories, or glob patterns. Quote glob patterns.",
    )
    parser.add_argument(
        "--composite",
        default="true_color",
        help="Satpy composite name (default: true_color).",
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
        "--list-composites",
        action="store_true",
        help="List available composites and exit without creating an image.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    files = expand_inputs(args.files)

    if not files:
        parser.error("No NetCDF/HDF5 files matched --files.")

    try:
        resolve_bbox(args.domain)
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
        domain=args.domain,
        area=args.area,
    )

    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output_scene.save_dataset(composite, filename=str(output), writer="simple_image")
    print(f"Image created: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
