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
DOMAIN_BBOXES = {
    "conus": (-125.0, 24.0, -66.0, 50.0),
    "azores": (-33.5, 34.0, -21.0, 42.5),
    "iberia": (-11.0, 35.0, 5.0, 45.0),
    "north-atlantic": (-70.0, 10.0, 20.0, 70.0),
}
DOMAIN_CHOICES = (
    "source",
    "full-disk",
    "conus",
    "mesoscale",
    "azores",
    "iberia",
    "north-atlantic",
    "custom",
)


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
            "Satpy não está instalado. Execute: python -m pip install -r requirements.txt"
        ) from exc

    return Scene(reader=READERS[sensor], filenames=files)


def available_composites(scene) -> list[str]:
    """Return sorted composite names from a Satpy Scene."""
    return sorted(str(name) for name in scene.available_composite_names())


def validate_bbox(values: Iterable[float]) -> tuple[float, float, float, float]:
    """Validate and normalize a west, south, east, north bounding box."""
    west, south, east, north = (float(value) for value in values)
    if not (-180 <= west < east <= 180):
        raise ValueError("longitude inválida: use -180 ≤ oeste < este ≤ 180")
    if not (-90 <= south < north <= 90):
        raise ValueError("latitude inválida: use -90 ≤ sul < norte ≤ 90")
    return west, south, east, north


def resolve_bbox(
    domain: str,
    custom_bbox: Iterable[float] | None,
) -> tuple[float, float, float, float] | None:
    """Resolve a named domain or custom bounding box to lon/lat limits."""
    if custom_bbox is not None:
        return validate_bbox(custom_bbox)
    if domain == "custom":
        raise ValueError("--domain custom requer --bbox OESTE SUL ESTE NORTE")
    return DOMAIN_BBOXES.get(domain)


def add_domain_arguments(
    parser: argparse.ArgumentParser,
    *,
    default: str = "source",
) -> None:
    """Add common spatial-domain arguments to a parser."""
    parser.add_argument(
        "--domain",
        choices=DOMAIN_CHOICES,
        default=default,
        help=(
            "Extensão de saída: source, full-disk, conus, mesoscale, "
            "azores, iberia, north-atlantic ou custom."
        ),
    )
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
        help="Recorte personalizado em longitude/latitude; substitui --domain.",
    )


def crop_and_resample_scene(
    scene,
    *,
    domain: str,
    bbox: Iterable[float] | None,
    area: str | None = None,
):
    """Crop a Scene geographically, then put all datasets on one grid."""
    bounds = resolve_bbox(domain, bbox)
    working_scene = scene.crop(ll_bbox=bounds) if bounds else scene
    return (
        working_scene.resample(area)
        if area
        else working_scene.resample(resampler="native")
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transforma ficheiros GOES ABI ou VIIRS SDR numa imagem PNG."
    )
    parser.add_argument("--sensor", choices=sorted(READERS), required=True)
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Ficheiros, diretórios ou padrões glob. Coloque padrões entre aspas.",
    )
    parser.add_argument(
        "--composite",
        default="true_color",
        help="Nome do composite Satpy (predefinição: true_color).",
    )
    parser.add_argument(
        "--output",
        default="output/satellite.png",
        help="Caminho do PNG de saída.",
    )
    parser.add_argument(
        "--area",
        help="Área Satpy para reamostragem, por exemplo 'eurol'.",
    )
    add_domain_arguments(parser)
    parser.add_argument(
        "--list-composites",
        action="store_true",
        help="Lista os composites possíveis e termina sem criar imagem.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    files = expand_inputs(args.files)

    if not files:
        parser.error("Nenhum ficheiro NetCDF/HDF5 corresponde a --files.")

    try:
        resolve_bbox(args.domain, args.bbox)
    except ValueError as exc:
        parser.error(str(exc))

    if args.sensor == "viirs" and not has_viirs_geolocation(files):
        print(
            "Aviso: não foi detetado GITCO, GMTCO, GDNBO, GIMGO ou GMODO. "
            "A maioria dos produtos VIIRS precisa de geolocalização.",
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
        print("O leitor disponibiliza true_color_raw; será usado como alternativa.")

    if composite not in composites:
        preview = ", ".join(composites[:20]) or "nenhum"
        raise SystemExit(
            f"O composite '{args.composite}' não pode ser criado com estes ficheiros. "
            f"Disponíveis: {preview}. Use --list-composites para a lista completa."
        )

    scene.load([composite], generate=True)
    output_scene = crop_and_resample_scene(
        scene,
        domain=args.domain,
        bbox=args.bbox,
        area=args.area,
    )

    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output_scene.save_dataset(composite, filename=str(output), writer="simple_image")
    print(f"Imagem criada: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
