"""Day/night True Color: real color by day, cloud detail by night.

True Color needs sunlight, so a plain True Color image is black at night. This
module blends two views with the solar angle so a single image works at any
time of day:

* daytime pixels   -> the normal True Color RGB;
* twilight pixels  -> a smooth mix of the two;
* nighttime pixels -> clouds from a thermal / low-light source.

Night source, in order of preference:

1. ``night_microphysics`` — the standard colour infrared night RGB
   (R = 12.3-10.3 um, G = 10.3-3.9 um, B = 10.3 um). This is what CIRA/RAMMB
   style day/night products show at night: fog and low water clouds separate
   from thick high ice cloud by colour, instead of a flat grey. Needs C07, C13
   and C15 on ABI.
2. ``dynamic_dnb`` (VIIRS only) — the Day/Night Band, moonlit clouds and city
   lights, when SVDNB and its GDNBO geolocation are present.
3. A single infrared window band (``C13``, or ``I05``/``M15`` on VIIRS) shaded
   grey as a last resort when the bands above are missing.

The three functions ``day_weight``, ``ir_cloud_gray`` and ``blend_day_night``
are plain array math with no Satpy dependency, so they can be unit tested
directly. ``compose_day_night_image`` glues them onto a resampled Satpy Scene.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np


# Solar zenith angle (degrees) marking the day/twilight/night transition.
# The sun is at the horizon at 90 deg. Below DAY_LIMIT it is full daylight;
# above NIGHT_LIMIT it is full night; in between the two views cross-fade.
# The night side must take over slightly *before* the sun reaches the horizon:
# by 88 deg the visible channels carry almost no signal, so letting the day
# view contribute past that only drags a dark band across the terminator.
DAY_LIMIT = 85.0
NIGHT_LIMIT = 88.0

# Brightness-temperature stretch (Kelvin) for infrared cloud shading.
# Cold cloud tops -> bright (1.0); warm surface -> dark (0.0).
IR_COLD_KELVIN = 190.0
IR_WARM_KELVIN = 300.0

# Candidate night sources, in order of preference, per sensor.
NIGHT_RGB_COMPOSITE = "night_microphysics"  # colour IR night RGB (CIRA style)
GOES_NIGHT_IR = "C13"
VIIRS_DNB_COMPOSITE = "dynamic_dnb"
VIIRS_NIGHT_IR = ("I05", "M15")
# Night sources that are already three-band images rather than a single band.
RGB_NIGHT_SOURCES = frozenset({NIGHT_RGB_COMPOSITE})


def day_weight(
    sun_zenith: np.ndarray,
    *,
    day_limit: float = DAY_LIMIT,
    night_limit: float = NIGHT_LIMIT,
) -> np.ndarray:
    """Weight for the daytime view from the solar zenith angle in degrees.

    Returns 1.0 in full daylight, 0.0 at full night, and a linear ramp across
    the twilight band between ``day_limit`` and ``night_limit``.
    """
    if night_limit <= day_limit:
        raise ValueError("night_limit must be greater than day_limit")
    zenith = np.asarray(sun_zenith, dtype="float64")
    weight = (night_limit - zenith) / (night_limit - day_limit)
    return np.clip(weight, 0.0, 1.0)


def ir_cloud_gray(
    brightness_temperature: np.ndarray,
    *,
    cold_kelvin: float = IR_COLD_KELVIN,
    warm_kelvin: float = IR_WARM_KELVIN,
) -> np.ndarray:
    """Grayscale clouds from an infrared window band (values in Kelvin).

    Cold cloud tops become bright, warm surface becomes dark, so clouds stay
    visible where there is no sunlight.
    """
    if warm_kelvin <= cold_kelvin:
        raise ValueError("warm_kelvin must be greater than cold_kelvin")
    temperature = np.asarray(brightness_temperature, dtype="float64")
    gray = (warm_kelvin - temperature) / (warm_kelvin - cold_kelvin)
    return np.clip(gray, 0.0, 1.0)


def blend_day_night(
    day_rgb: np.ndarray,
    night: np.ndarray,
    weight: np.ndarray,
) -> np.ndarray:
    """Blend a day RGB (3, H, W) with a night image by ``weight``.

    ``night`` may be a colour RGB shaped (3, H, W) — for example the night
    microphysics composite — or a single grayscale band shaped (H, W), which is
    repeated across the three channels.

    ``weight`` is the daytime fraction (see :func:`day_weight`) shaped (H, W).
    Returns an array shaped (3, H, W) clipped to 0..1.
    """
    day = np.nan_to_num(np.asarray(day_rgb, dtype="float64"), nan=0.0)
    if day.ndim != 3 or day.shape[0] != 3:
        raise ValueError("day_rgb must have shape (3, H, W)")
    night = np.nan_to_num(np.asarray(night, dtype="float64"), nan=0.0)
    if night.ndim == 2:
        night_rgb = np.repeat(night[np.newaxis, ...], 3, axis=0)
    elif night.ndim == 3 and night.shape[0] == 3:
        night_rgb = night
    else:
        raise ValueError("night must have shape (H, W) or (3, H, W)")
    day_fraction = np.asarray(weight, dtype="float64")[np.newaxis, ...]
    blended = day_fraction * day + (1.0 - day_fraction) * night_rgb
    return np.clip(blended, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Satpy glue (needs a loaded, resampled Scene). Not exercised by unit tests.
# ---------------------------------------------------------------------------

def _enhanced_rgb(scene, name: str) -> np.ndarray:
    """Return an enhanced RGB composite as a (3, H, W) float array in 0..1."""
    from satpy.enhancements.enhancer import get_enhanced_image

    data = get_enhanced_image(scene[name]).data  # dims: (bands, y, x), 0..1
    bands = list(data["bands"].values) if "bands" in data.coords else []
    if {"R", "G", "B"}.issubset(set(bands)):
        data = data.sel(bands=["R", "G", "B"])
    else:
        data = data.isel(bands=slice(0, 3))
    return np.asarray(data.values, dtype="float64")


def _enhanced_gray(scene, name: str) -> np.ndarray:
    """Return an enhanced single-band composite as a (H, W) float array in 0..1."""
    from satpy.enhancements.enhancer import get_enhanced_image

    data = get_enhanced_image(scene[name]).data
    if "bands" in data.coords and data.sizes.get("bands", 1) > 1:
        data = data.isel(bands=0)
    elif "bands" in data.coords:
        data = data.isel(bands=0)
    return np.asarray(data.values, dtype="float64")


def night_source_names(sensor: str, available: Iterable[str] = ()) -> list[str]:
    """Night-side datasets/composites to try, in order of preference.

    The caller loads them in order and keeps the first that actually yields
    data, so this returns the full preference list rather than pre-filtering
    (``I05``/``M15`` are channels, not composites, and would not appear in a
    composite-name list). ``available`` is accepted for compatibility but not
    required.
    """
    if sensor == "goes":
        return [NIGHT_RGB_COMPOSITE, GOES_NIGHT_IR]
    # VIIRS: colour night RGB first, then the Day/Night Band, then plain IR.
    return [NIGHT_RGB_COMPOSITE, VIIRS_DNB_COMPOSITE, *VIIRS_NIGHT_IR]


def compose_day_night_image(scene, sensor: str, *, day_composite: str = "true_color"):
    """Build a day/night True Color PIL image from a resampled Scene.

    The Scene must already contain ``day_composite`` and a night source, all on
    one common area (for example after ``crop_and_resample_scene``).
    """
    from PIL import Image
    from pyorbital.astronomy import sun_zenith_angle

    day_rgb = _enhanced_rgb(scene, day_composite)

    # Pick the first night source that is actually present in the scene.
    night_image = None
    used_night = None
    for name in night_source_names(sensor, scene.keys()):
        try:
            dataset = scene[name]
        except KeyError:
            continue
        used_night = name
        if name in RGB_NIGHT_SOURCES:
            # Colour infrared night RGB: low cloud and fog separate from high
            # ice cloud by colour, as in CIRA/RAMMB day/night products.
            night_image = _enhanced_rgb(scene, name)
        elif name == VIIRS_DNB_COMPOSITE:
            night_image = _enhanced_gray(scene, name)
        else:
            night_image = ir_cloud_gray(np.asarray(dataset.values, dtype="float64"))
        break
    if night_image is None:
        raise ValueError(
            f"No night source found for sensor '{sensor}'. Expected one of: "
            f"{', '.join(night_source_names(sensor, scene.keys()))}."
        )

    reference = scene[day_composite]
    area = reference.attrs.get("area")
    if area is None:
        raise ValueError("The day composite has no area information.")
    lons, lats = area.get_lonlats()
    start_time = reference.attrs.get("start_time")
    if start_time is None:
        raise ValueError("The day composite has no start_time for solar geometry.")

    zenith = sun_zenith_angle(start_time, np.asarray(lons), np.asarray(lats))
    # Off-disk / invalid geometry -> treat as night so nothing turns into NaN.
    weight = np.nan_to_num(day_weight(zenith), nan=0.0)
    blended = blend_day_night(day_rgb, night_image, weight)

    rgb_uint8 = (np.transpose(blended, (1, 2, 0)) * 255.0).round().astype("uint8")
    image = Image.fromarray(rgb_uint8, mode="RGB")
    return image, used_night
