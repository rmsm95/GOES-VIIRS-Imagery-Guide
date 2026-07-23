"""Public GOES-18 files for the 3 October 2023 coverage examples."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve


NOAA_BASE = "https://noaa-goes18.s3.amazonaws.com"
SCAN_LABELS = {
    "full_disk": "2023-10-03 19:00 UTC",
    "full_disk_night": "2023-10-03 17:00 UTC",
    "conus": "2023-10-03 19:01 UTC",
    "mesoscale": "2023-10-03 19:00 UTC",
}
PRODUCT_PATHS = {
    "full_disk": "ABI-L1b-RadF/2023/276/19",
    "full_disk_night": "ABI-L1b-RadF/2023/276/17",
    "conus": "ABI-L1b-RadC/2023/276/19",
    "mesoscale": "ABI-L1b-RadM/2023/276/19",
}
FILES = {
    "full_disk": {
        "C01": "OR_ABI-L1b-RadF-M6C01_G18_s20232761900206_e20232761909514_c20232761909554.nc",
        "C02": "OR_ABI-L1b-RadF-M6C02_G18_s20232761900206_e20232761909514_c20232761909546.nc",
        "C03": "OR_ABI-L1b-RadF-M6C03_G18_s20232761900206_e20232761909514_c20232761909559.nc",
        "C07": "OR_ABI-L1b-RadF-M6C07_G18_s20232761900206_e20232761909526_c20232761909567.nc",
        "C09": "OR_ABI-L1b-RadF-M6C09_G18_s20232761900206_e20232761909520_c20232761909561.nc",
        "C10": "OR_ABI-L1b-RadF-M6C10_G18_s20232761900206_e20232761909526_c20232761909548.nc",
        "C11": "OR_ABI-L1b-RadF-M6C11_G18_s20232761900206_e20232761909514_c20232761909558.nc",
        "C13": "OR_ABI-L1b-RadF-M6C13_G18_s20232761900206_e20232761909526_c20232761909572.nc",
        "C14": "OR_ABI-L1b-RadF-M6C14_G18_s20232761900206_e20232761909514_c20232761909569.nc",
        "C15": "OR_ABI-L1b-RadF-M6C15_G18_s20232761900206_e20232761909520_c20232761909555.nc",
    },
    "full_disk_night": {
        # 17:00 UTC scan (~06:00 local): Shishaldin is in darkness, so True
        # Color is black and the day/night blend shows clouds from C13.
        "C01": "OR_ABI-L1b-RadF-M6C01_G18_s20232761700206_e20232761709514_c20232761709555.nc",
        "C02": "OR_ABI-L1b-RadF-M6C02_G18_s20232761700206_e20232761709514_c20232761709535.nc",
        "C03": "OR_ABI-L1b-RadF-M6C03_G18_s20232761700206_e20232761709514_c20232761709560.nc",
        "C07": "OR_ABI-L1b-RadF-M6C07_G18_s20232761700206_e20232761709526_c20232761709566.nc",
        "C13": "OR_ABI-L1b-RadF-M6C13_G18_s20232761700206_e20232761709525_c20232761709561.nc",
        "C15": "OR_ABI-L1b-RadF-M6C15_G18_s20232761700206_e20232761709520_c20232761709549.nc",
    },
    "conus": {
        "C01": "OR_ABI-L1b-RadC-M6C01_G18_s20232761901171_e20232761903544_c20232761903586.nc",
        "C02": "OR_ABI-L1b-RadC-M6C02_G18_s20232761901171_e20232761903545_c20232761903565.nc",
        "C03": "OR_ABI-L1b-RadC-M6C03_G18_s20232761901171_e20232761903544_c20232761903579.nc",
        "C09": "OR_ABI-L1b-RadC-M6C09_G18_s20232761901171_e20232761903550_c20232761904001.nc",
        "C10": "OR_ABI-L1b-RadC-M6C10_G18_s20232761901171_e20232761903556_c20232761903593.nc",
        "C11": "OR_ABI-L1b-RadC-M6C11_G18_s20232761901171_e20232761903545_c20232761903596.nc",
        "C13": "OR_ABI-L1b-RadC-M6C13_G18_s20232761901171_e20232761903556_c20232761904010.nc",
        "C14": "OR_ABI-L1b-RadC-M6C14_G18_s20232761901171_e20232761903545_c20232761904005.nc",
        "C15": "OR_ABI-L1b-RadC-M6C15_G18_s20232761901171_e20232761903550_c20232761904031.nc",
    },
    "mesoscale": {
        "C01": "OR_ABI-L1b-RadM1-M6C01_G18_s20232761900279_e20232761900337_c20232761900364.nc",
        "C02": "OR_ABI-L1b-RadM1-M6C02_G18_s20232761900279_e20232761900337_c20232761900361.nc",
        "C03": "OR_ABI-L1b-RadM1-M6C03_G18_s20232761900279_e20232761900337_c20232761900371.nc",
        "C09": "OR_ABI-L1b-RadM1-M6C09_G18_s20232761900279_e20232761900343_c20232761900379.nc",
        "C10": "OR_ABI-L1b-RadM1-M6C10_G18_s20232761900279_e20232761900350_c20232761900374.nc",
        "C11": "OR_ABI-L1b-RadM1-M6C11_G18_s20232761900279_e20232761900337_c20232761900377.nc",
        "C13": "OR_ABI-L1b-RadM1-M6C13_G18_s20232761900279_e20232761900348_c20232761900391.nc",
        "C14": "OR_ABI-L1b-RadM1-M6C14_G18_s20232761900279_e20232761900337_c20232761900387.nc",
        "C15": "OR_ABI-L1b-RadM1-M6C15_G18_s20232761900279_e20232761900343_c20232761900369.nc",
    },
}


def source_url(coverage: str, channel: str) -> str:
    """Return the public NOAA URL for one coverage and ABI channel."""
    try:
        filename = FILES[coverage][channel]
        product_path = PRODUCT_PATHS[coverage]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported coverage/channel: {coverage!r}/{channel!r}"
        ) from exc
    return f"{NOAA_BASE}/{product_path}/{filename}"


def download_coverage(
    base_dir: str | Path,
    coverage: str,
    channels: tuple[str, ...],
) -> list[str]:
    """Download selected channels for one coverage and reuse existing files."""
    coverage_dir = Path(base_dir) / coverage
    coverage_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[str] = []

    for channel in channels:
        try:
            filename = FILES[coverage][channel]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported coverage/channel: {coverage!r}/{channel!r}"
            ) from exc

        destination = coverage_dir / filename
        if not destination.exists() or destination.stat().st_size == 0:
            partial = destination.with_suffix(destination.suffix + ".part")
            print(f"Downloading {coverage} {channel}: {filename}")
            urlretrieve(source_url(coverage, channel), partial)
            partial.replace(destination)
        downloaded.append(str(destination))

    return downloaded
