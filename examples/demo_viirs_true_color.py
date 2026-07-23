#!/usr/bin/env python3
"""Download a small Suomi NPP VIIRS demo scene and create a True Color PNG."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .render_satellite import (
        add_domain_argument,
        crop_and_resample_scene,
        resolve_bbox,
        save_dataset_with_lonlat_grid,
    )
except ImportError:
    from render_satellite import (
        add_domain_argument,
        crop_and_resample_scene,
        resolve_bbox,
        save_dataset_with_lonlat_grid,
    )


DEMO_CHANNELS = ("I01", "I02", "M03", "M04", "M05")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        default="data/demo-viirs",
        help="Directory used to store the demo data.",
    )
    parser.add_argument(
        "--output",
        default="output/demo_viirs_true_color.png",
        help="Output PNG image.",
    )
    add_domain_argument(parser)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        resolve_bbox(args.domain)
    except ValueError as exc:
        parser.error(str(exc))

    try:
        from satpy import Scene
        from satpy.demo.viirs_sdr import get_viirs_sdr_20170128_1229
    except ImportError as exc:
        raise SystemExit(
            "Install the dependencies first: python -m pip install -r requirements.txt"
        ) from exc

    print("Downloading a Suomi NPP VIIRS granule with I/M bands and geolocation...")
    files = get_viirs_sdr_20170128_1229(
        base_dir=args.data_dir,
        channels=DEMO_CHANNELS,
        granules=(1,),
    )
    scene = Scene(reader="viirs_sdr", filenames=files)
    available = {str(name) for name in scene.available_composite_names()}
    if "true_color" not in available:
        raise SystemExit(
            "The demo dataset does not provide true_color. "
            "Check the Satpy version and downloaded files."
        )

    scene.load(["true_color"], generate=True)
    resampled = crop_and_resample_scene(
        scene,
        domain=args.domain,
    )

    output = Path(args.output)
    save_dataset_with_lonlat_grid(
        resampled,
        "true_color",
        output,
        title="Suomi NPP VIIRS True Color",
    )
    print(f"Image created: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
