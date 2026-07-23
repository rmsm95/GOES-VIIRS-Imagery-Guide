#!/usr/bin/env python3
"""Download Satpy's GOES ABI demo data and create a True Color PNG."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .render_satellite import (
        add_domain_argument,
        crop_and_resample_scene,
        resolve_domain_tokens,
        save_dataset_with_lonlat_grid,
    )
except ImportError:
    from render_satellite import (
        add_domain_argument,
        crop_and_resample_scene,
        resolve_domain_tokens,
        save_dataset_with_lonlat_grid,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        default="data/demo-goes",
        help="Directory used to store the demo data.",
    )
    parser.add_argument(
        "--output",
        default="output/demo_goes_true_color.png",
        help="Output PNG image.",
    )
    add_domain_argument(parser)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        bbox = resolve_domain_tokens(args.domain)
    except ValueError as exc:
        parser.error(str(exc))

    try:
        from satpy import Scene
        from satpy.demo.abi_l1b import get_us_midlatitude_cyclone_abi
    except ImportError as exc:
        raise SystemExit(
            "Install the dependencies first: python -m pip install -r requirements.txt"
        ) from exc

    print("Downloading the GOES ABI demo dataset...")
    files = get_us_midlatitude_cyclone_abi(base_dir=args.data_dir)
    scene = Scene(reader="abi_l1b", filenames=files)
    available = {str(name) for name in scene.available_composite_names()}

    if "true_color" in available:
        composite = "true_color"
    elif "true_color_raw" in available:
        composite = "true_color_raw"
    else:
        raise SystemExit(
            "The demo files provide neither true_color nor true_color_raw."
        )

    scene.load([composite], generate=True)
    resampled = crop_and_resample_scene(
        scene,
        domain=bbox,
    )

    output = Path(args.output)
    save_dataset_with_lonlat_grid(
        resampled,
        composite,
        output,
        title="GOES ABI True Color",
    )
    print(f"Image created: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
