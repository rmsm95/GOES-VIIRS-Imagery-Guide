#!/usr/bin/env python3
"""Download a small Suomi NPP VIIRS demo scene and create a True Color PNG."""

from __future__ import annotations

import argparse
from pathlib import Path


DEMO_CHANNELS = ("I01", "I02", "M03", "M04", "M05")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        default="data/demo-viirs",
        help="Diretório usado para guardar os dados de demonstração.",
    )
    parser.add_argument(
        "--output",
        default="output/demo_viirs_true_color.png",
        help="Imagem PNG de saída.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        from satpy import Scene
        from satpy.demo.viirs_sdr import get_viirs_sdr_20170128_1229
    except ImportError as exc:
        raise SystemExit(
            "Instale primeiro as dependências: python -m pip install -r requirements.txt"
        ) from exc

    print("A obter uma granule Suomi NPP VIIRS com bandas I/M e geolocalização…")
    files = get_viirs_sdr_20170128_1229(
        base_dir=args.data_dir,
        channels=DEMO_CHANNELS,
        granules=(1,),
    )
    scene = Scene(reader="viirs_sdr", filenames=files)
    available = {str(name) for name in scene.available_composite_names()}
    if "true_color" not in available:
        raise SystemExit(
            "O conjunto de demonstração não disponibiliza true_color. "
            "Verifique a versão do Satpy e os ficheiros descarregados."
        )

    scene.load(["true_color"], generate=True)
    resampled = scene.resample(resampler="native")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    resampled.save_dataset("true_color", filename=str(output), writer="simple_image")
    print(f"Imagem criada: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
