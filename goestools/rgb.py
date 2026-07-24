"""RGB composites from ABI channels, ready for ``pcolormesh``.

    RGB, LonCor, LatCor = true_color(files, domain=[-166, -162, 53, 56])
    ax.pcolormesh(LonCor.data, LatCor.data, RGB.data[..., 0] * 0,  # dummy
                  color=RGB.data.reshape(-1, 3))

In practice use :func:`pcolormesh_rgb`, which handles that last step:

    pcolormesh_rgb(ax, LonCor.data, LatCor.data, RGB.data)

Channels come at different resolutions (0.5, 1 and 2 km). They are aligned by
averaging the finer channel down to the coarser grid by an exact integer
factor, so no interpolation is involved and the pixels stay where they were.

Recipes follow the NOAA/CIMSS and CIRA quick guides; see ``docs/RGB.md``.
"""

from __future__ import annotations

import numpy as np

from .dataset import Field, open_dataset


# --------------------------------------------------------------------------
# Solar geometry, so daytime composites can be normalised for sun angle.
# --------------------------------------------------------------------------
def solar_zenith_angle(when, longitude, latitude):
    """Solar zenith angle in degrees (NOAA's low-precision equations)."""
    day_of_year = when.timetuple().tm_yday
    hour = when.hour + when.minute / 60.0 + when.second / 3600.0

    gamma = 2.0 * np.pi / 365.0 * (day_of_year - 1 + (hour - 12) / 24.0)
    equation_of_time = 229.18 * (
        0.000075 + 0.001868 * np.cos(gamma) - 0.032077 * np.sin(gamma)
        - 0.014615 * np.cos(2 * gamma) - 0.040849 * np.sin(2 * gamma)
    )
    declination = (
        0.006918 - 0.399912 * np.cos(gamma) + 0.070257 * np.sin(gamma)
        - 0.006758 * np.cos(2 * gamma) + 0.000907 * np.sin(2 * gamma)
        - 0.002697 * np.cos(3 * gamma) + 0.00148 * np.sin(3 * gamma)
    )

    time_offset = equation_of_time + 4.0 * np.asarray(longitude, dtype="float64")
    true_solar_time = hour * 60.0 + time_offset
    hour_angle = np.radians(true_solar_time / 4.0 - 180.0)

    lat = np.radians(np.asarray(latitude, dtype="float64"))
    cosine = (np.sin(lat) * np.sin(declination)
              + np.cos(lat) * np.cos(declination) * np.cos(hour_angle))
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))


# --------------------------------------------------------------------------
# Reading several channels onto one grid
# --------------------------------------------------------------------------
def _by_channel(files):
    """Open files and key them by channel name, e.g. ``{"C01": ds}``."""
    datasets = {}
    for name in files:
        dataset = open_dataset(name)
        if dataset.band is None:
            dataset.close()
            continue
        datasets[f"C{dataset.band:02d}"] = dataset
    return datasets


def _aggregate(values, factor):
    """Average blocks of ``factor`` x ``factor`` pixels."""
    if factor == 1:
        return values
    rows = values.shape[0] // factor * factor
    cols = values.shape[1] // factor * factor
    block = values[:rows, :cols].reshape(
        rows // factor, factor, cols // factor, factor
    )
    with np.errstate(invalid="ignore"):
        return np.nanmean(block, axis=(1, 3))


def read_aligned(files, channels, parameter="BT", domain=None, lonlat="corner"):
    """Read several channels onto the coarsest of their grids.

    Returns ``(arrays, longitude, latitude, start_time)`` where ``arrays`` maps
    the channel name to a 2-D array. ``parameter`` is passed through to
    :meth:`ABIDataset.image`, so use ``"BT"`` for infrared and ``"Ref"`` for
    the visible channels.
    """
    datasets = _by_channel(files)
    missing = [c for c in channels if c not in datasets]
    if missing:
        found = ", ".join(sorted(datasets)) or "none"
        for dataset in datasets.values():
            dataset.close()
        raise FileNotFoundError(
            f"Missing channel(s) {', '.join(missing)}. Found: {found}. "
            "Download every channel this composite needs, from the same scan."
        )

    try:
        # The coarsest channel sets the output grid.
        reference_name = min(channels, key=lambda c: datasets[c].x.size)
        reference = datasets[reference_name]
        if domain is None:
            window = (0, reference.x.size - 1, 0, reference.y.size - 1)
        else:
            window = reference.pixels_of_domain(domain)
        xmin, xmax, ymin, ymax = window

        arrays = {}
        for channel in channels:
            dataset = datasets[channel]
            factor = dataset.x.size // reference.x.size
            if factor * reference.x.size != dataset.x.size:
                raise ValueError(
                    f"{channel} does not sit on an integer multiple of the "
                    f"{reference_name} grid; cannot align them exactly."
                )
            field, _, _ = dataset.image(
                parameter,
                lonlat=None,
                domain_in_pixels=[
                    xmin * factor, (xmax + 1) * factor - 1,
                    ymin * factor, (ymax + 1) * factor - 1,
                ],
            )
            arrays[channel] = _aggregate(field.data, factor)

        _, longitude, latitude = reference.image(
            "Rad", lonlat=lonlat, domain_in_pixels=[xmin, xmax, ymin, ymax]
        )
        return arrays, longitude, latitude, reference.start_time
    finally:
        for dataset in datasets.values():
            dataset.close()


# --------------------------------------------------------------------------
# The composites
# --------------------------------------------------------------------------
def _stretch(values, low, high, gamma=1.0):
    """Clip to a physical range, scale to 0..1, then apply gamma."""
    scaled = (np.asarray(values, dtype="float64") - low) / (high - low)
    scaled = np.clip(scaled, 0.0, 1.0)
    return scaled ** (1.0 / gamma) if gamma != 1.0 else scaled


def true_color(files, domain=None, lonlat="corner", gamma=2.2,
               sun_correction=True):
    """ABI True Color: real colour, daylight only.

    ABI has no green band, so green is synthesised from the blue, red and
    vegetation channels (NOAA/CIMSS):

        R = C02,  G = 0.45*C02 + 0.10*C03 + 0.45*C01,  B = C01

    With ``sun_correction`` the reflectances are divided by the cosine of the
    solar zenith angle, which evens out the brightness across the scene. No
    Rayleigh (atmospheric scattering) correction is applied, so distant parts
    of the disk look hazier than in an operational product.
    """
    arrays, longitude, latitude, start_time = read_aligned(
        files, ["C01", "C02", "C03"], parameter="Ref",
        domain=domain, lonlat=lonlat,
    )
    blue, red, veggie = arrays["C01"], arrays["C02"], arrays["C03"]

    if sun_correction and start_time is not None:
        centre_lon = np.nanmean(longitude.data)
        centre_lat = np.nanmean(latitude.data)
        zenith = solar_zenith_angle(start_time, centre_lon, centre_lat)
        cosine = max(np.cos(np.radians(min(zenith, 80.0))), 0.15)
        blue, red, veggie = blue / cosine, red / cosine, veggie / cosine

    green = 0.45 * red + 0.10 * veggie + 0.45 * blue
    stack = np.dstack([
        _stretch(red, 0.0, 1.0, gamma),
        _stretch(green, 0.0, 1.0, gamma),
        _stretch(blue, 0.0, 1.0, gamma),
    ])
    return (Field(stack, "true_color", "1", "True Color", start_time),
            longitude, latitude)


def ash(files, domain=None, lonlat="corner"):
    """CIRA Ash RGB. Works day and night; ash tends to red/magenta."""
    arrays, longitude, latitude, start_time = read_aligned(
        files, ["C11", "C13", "C14", "C15"], parameter="BT",
        domain=domain, lonlat=lonlat,
    )
    stack = np.dstack([
        _stretch(arrays["C15"] - arrays["C13"], -6.7, 2.6),
        _stretch(arrays["C14"] - arrays["C11"], -6.0, 6.3),
        _stretch(arrays["C13"], 243.6, 302.4),
    ])
    return (Field(stack, "ash", "1", "Ash RGB", start_time),
            longitude, latitude)


def volcanic_emissions(files, domain=None, lonlat="corner"):
    """CIRA SO2 / Volcanic Emissions RGB. Qualitative, not a retrieval."""
    arrays, longitude, latitude, start_time = read_aligned(
        files, ["C09", "C10", "C11", "C13"], parameter="BT",
        domain=domain, lonlat=lonlat,
    )
    stack = np.dstack([
        _stretch(arrays["C09"] - arrays["C10"], -4.0, 2.0),
        _stretch(arrays["C13"] - arrays["C11"], -4.0, 5.0),
        _stretch(arrays["C13"], 243.05, 302.95),
    ])
    return (Field(stack, "volcanic_emissions", "1",
                  "SO2 / Volcanic Emissions RGB", start_time),
            longitude, latitude)


# --------------------------------------------------------------------------
# Drawing
# --------------------------------------------------------------------------
def pcolormesh_rgb(ax, longitude, latitude, rgb, **kwargs):
    """Draw an (M, N, 3) RGB image with ``pcolormesh`` corner coordinates.

    ``pcolormesh`` colours cells from a 2-D array, so the RGB is passed as a
    per-cell colour list. Pixels with no data are left transparent.
    """
    rgb = np.asarray(rgb, dtype="float64")
    colours = rgb.reshape(-1, 3)
    good = np.isfinite(colours).all(axis=1)
    colours = np.clip(np.where(good[:, None], colours, 0.0), 0.0, 1.0)
    alpha = good.astype("float64")
    rgba = np.column_stack([colours, alpha])

    placeholder = np.ma.masked_invalid(rgb[..., 0])
    mesh = ax.pcolormesh(longitude, latitude, placeholder, **kwargs)
    mesh.set_facecolor(rgba)
    mesh.set_array(None)
    return mesh
