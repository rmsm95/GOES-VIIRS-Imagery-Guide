"""Named geographic domains you can reuse instead of typing four numbers.

Each entry maps a short name to a bounding box in the same order the CLI uses:

    (MIN_LON, MIN_LAT, MAX_LON, MAX_LAT)   # decimal degrees, WGS 84

These are only *examples*. Add, remove, or edit them freely for your own
study areas. Longitude is negative west of Greenwich; latitude is negative
south of the equator. Keep MIN_LON < MAX_LON and MIN_LAT < MAX_LAT, and do not
cross the antimeridian (a single box cannot span from +179 to -179).

Once a name is here you can run, for example:

    python examples/render_satellite.py --sensor goes --files "data/*.nc" \
        --composite true_color --domain shishaldin

Raw coordinates still work too:

    --domain -166.0 54.0 -162.0 56.0
"""

from __future__ import annotations

# name -> (min_lon, min_lat, max_lon, max_lat)
DOMAINS: dict[str, tuple[float, float, float, float]] = {
    # --- Alaska examples (edit these for your own work) --------------------
    "shishaldin": (-166.0, 54.0, -162.0, 56.0),        # tight box on the volcano
    "shishaldin_wide": (-170.0, 52.0, -158.0, 58.0),   # regional context
    "alaska_peninsula": (-165.0, 54.0, -153.0, 60.0),  # broader peninsula view
    # --- Generic examples --------------------------------------------------
    "conus": (-125.0, 24.0, -66.0, 50.0),              # continental United States
}


def list_domains() -> str:
    """Return a human-readable table of the named domains."""
    if not DOMAINS:
        return "No named domains are defined. Edit examples/domains.py to add some."
    width = max(len(name) for name in DOMAINS)
    header = f"{'name'.ljust(width)}   MIN_LON  MIN_LAT  MAX_LON  MAX_LAT"
    lines = [header, "-" * len(header)]
    for name in sorted(DOMAINS):
        lon0, lat0, lon1, lat1 = DOMAINS[name]
        lines.append(
            f"{name.ljust(width)}   {lon0:7.2f}  {lat0:7.2f}  {lon1:7.2f}  {lat1:7.2f}"
        )
    return "\n".join(lines)


def domain_names() -> list[str]:
    """Return the sorted list of known domain names."""
    return sorted(DOMAINS)
