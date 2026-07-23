#!/usr/bin/env python3
"""Download Satpy's GOES ABI demo data and create a True Color PNG."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .render_satellite import (
        add_domain_arguments,
        crop_and_resample_scene,
        resolve_bbox,
    )
except ImportError:
    from render_satellite import add_domain_arguments, crop_and_resample_scene, resolve_bbox


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        default="data/demo-goes",
        help="Diretório usado para guardar os dados de demonstração.",
    )
    parser.add_argument(
        "--output",
        default="output/demo_goes_true_color.png",
        help="Imagem PNG de saída.",
    )
    add_domain_arguments(parser, default="conus")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        resolve_bbox(args.domain, args.bbox)
    except ValueError as exc:
        parser.error(str(exc))

    if args.domain in {"full-disk", "mesoscale"}:
        raise SystemExit(
            "Este conjunto de demonstração é CONUS. Para Full Disk ou Mesoscale, "
            "descarregue ficheiros F/M e use render_satellite.py."
        )

    try:
        from satpy import Scene
        from satpy.demo.abi_l1b import get_us_midlatitude_cyclone_abi
    except ImportError as exc:
        raise SystemExit(
            "Instale primeiro as dependências: python -m pip install -r requirements.txt"
        ) from exc

    print("A obter o conjunto GOES ABI de demonstração…")
    files = get_us_midlatitude_cyclone_abi(base_dir=args.data_dir)
    scene = Scene(reader="abi_l1b", filenames=files)
    available = {str(name) for name in scene.available_composite_names()}

    if "true_color" in available:
        composite = "true_color"
    elif "true_color_raw" in available:
        composite = "true_color_raw"
    else:
        raise SystemExit(
            "Os ficheiros de demonstração não disponibilizam true_color nem true_color_raw."
        )

    scene.load([composite], generate=True)
    resampled = crop_and_resample_scene(
        scene,
        domain=args.domain,
        bbox=args.bbox,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    resampled.save_dataset(composite, filename=str(output), writer="simple_image")
    print(f"Imagem criada: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
