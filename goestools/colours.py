"""Colour scales for single-band images.

Two things are usually wanted from an infrared image:

* the plain grey scale, stretched to whatever the data actually contains, so
  nothing is clipped away;
* the forecaster's "enhanced" scale, where everything warmer than a threshold
  stays grey and the cold cloud tops above it are picked out in colour. That is
  what makes deep convection and volcanic ash jump out of the background.

    limits = data_limits(bt)                       # from the data
    limits = data_limits(bt, vmin=200, vmax=290)   # or fix them yourself

    cmap, norm = enhanced_scale(vmin=180, vmax=300, threshold=240)
"""

from __future__ import annotations

import numpy as np


def data_limits(values, vmin=None, vmax=None, percentiles=(0.5, 99.5)):
    """Colour limits for an array: from the data, unless you give them.

    The default trims the extreme half percent at each end, so a handful of
    stray pixels cannot flatten the whole image. Pass ``percentiles=None`` to
    use the true minimum and maximum.
    """
    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return (0.0, 1.0) if vmin is None or vmax is None else (vmin, vmax)

    if percentiles is None:
        low, high = float(np.min(finite)), float(np.max(finite))
    else:
        low, high = (float(v) for v in np.percentile(finite, percentiles))

    low = float(vmin) if vmin is not None else low
    high = float(vmax) if vmax is not None else high
    if high <= low:
        high = low + 1.0
    return low, high


def enhanced_scale(vmin, vmax, threshold, warm_cmap="Greys", cold_cmap="turbo",
                   name="enhanced"):
    """A grey scale for the warm side and a colour scale for the cold side.

    Values from ``threshold`` up to ``vmax`` are grey; values from ``vmin`` up
    to ``threshold`` take the colour map. Written for brightness temperature,
    where cold means high cloud, but it works for any quantity where one end
    deserves the attention.

    Returns ``(cmap, norm)`` ready to hand to ``pcolormesh`` or ``imshow``.
    """
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    from matplotlib import colormaps

    vmin, vmax, threshold = float(vmin), float(vmax), float(threshold)
    if not vmin < threshold < vmax:
        raise ValueError("threshold must lie between vmin and vmax")

    # How much of the bar the cold half takes up.
    split = (threshold - vmin) / (vmax - vmin)
    steps = 256
    cold_steps = max(1, int(round(steps * split)))
    warm_steps = max(1, steps - cold_steps)

    cold = colormaps[cold_cmap](np.linspace(0.0, 1.0, cold_steps))
    # Grey from dark at the threshold to light at the warm end, so warm
    # surface stays light and the colours mark the cold tops.
    warm = colormaps[warm_cmap](np.linspace(1.0, 0.0, warm_steps))

    colours = np.vstack([cold, warm])
    return (LinearSegmentedColormap.from_list(name, colours),
            Normalize(vmin=vmin, vmax=vmax))


def degree_ticks(ax, west, east, south, north, crs=None, nbins=(7, 6)):
    """Longitude/latitude ticks on a PlateCarree map, as 164W / 54N.

    Cartopy's own ``gridlines(draw_labels=True)`` confuses the tight bounding
    box that notebooks use when they save a figure, and the map can vanish from
    the output. Plain axis ticks avoid that and match the usual figure style.
    """
    import cartopy.crs as ccrs
    from matplotlib.ticker import FuncFormatter, MaxNLocator

    crs = crs or ccrs.PlateCarree()
    lon_ticks = MaxNLocator(nbins=nbins[0]).tick_values(west, east)
    lat_ticks = MaxNLocator(nbins=nbins[1]).tick_values(south, north)
    ax.set_xticks([t for t in lon_ticks if west <= t <= east], crs=crs)
    ax.set_yticks([t for t in lat_ticks if south <= t <= north], crs=crs)

    ax.xaxis.set_major_formatter(FuncFormatter(
        lambda v, _: f"{abs(((v + 180) % 360) - 180):g}°"
                     f"{'E' if ((v + 180) % 360) - 180 >= 0 else 'W'}"))
    ax.yaxis.set_major_formatter(FuncFormatter(
        lambda v, _: f"{abs(v):g}°{'N' if v >= 0 else 'S'}"))
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
