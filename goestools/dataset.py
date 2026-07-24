"""Read an ABI file and pull out an image, optionally cropped to a domain.

Usage follows the shape of the well-known ``GOES`` package:

    ds = open_dataset("OR_ABI-L1b-RadF-M6C13_G18_....nc")
    BT, LonCor, LatCor = ds.image("BT", lonlat="corner",
                                  domain=[-166, -162, 53, 56])
    ax.pcolormesh(LonCor.data, LatCor.data, BT.data)

The domain is ``[LonMin, LonMax, LatMin, LatMax]``.

Nothing is resampled: the pixels stay exactly as the satellite recorded them
and are drawn in longitude/latitude space through their corner coordinates.
Only the pixels inside the domain are read from disk.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .geolocation import corner_lonlat, lonlat_to_scan, scan_to_lonlat


class Field:
    """An array with the metadata needed to label a plot."""

    def __init__(self, data, standard_name="", units="", long_name="",
                 time_bounds=None, undimensional=None):
        self.data = data
        self.standard_name = standard_name
        self.units = units
        self.long_name = long_name
        self.time_bounds = time_bounds
        self.undimensional = undimensional

    @property
    def shape(self):
        return np.shape(self.data)

    def __repr__(self):
        return (f"<Field {self.standard_name or 'data'} {self.shape} "
                f"[{self.units}]>")


class ABIDataset:
    """One ABI file, opened lazily."""

    def __init__(self, path):
        import netCDF4

        self.path = str(path)
        self._nc = netCDF4.Dataset(self.path, "r")

        projection = self._nc.variables["goes_imager_projection"]
        self.satellite_height = float(projection.perspective_point_height)
        self.satellite_longitude = float(projection.longitude_of_projection_origin)
        self.sweep = str(projection.sweep_angle_axis)

        self.x = np.asarray(self._nc.variables["x"][:], dtype="float64")
        self.y = np.asarray(self._nc.variables["y"][:], dtype="float64")

        self.platform = getattr(self._nc, "platform_ID", "")
        self.scene = getattr(self._nc, "scene_id", "")
        self.band = int(self._nc.variables["band_id"][0]) if "band_id" in self._nc.variables else None
        self.time_bounds = self._read_time_bounds()

    # -- housekeeping ------------------------------------------------------
    def close(self):
        self._nc.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def __repr__(self):
        band = f" C{self.band:02d}" if self.band else ""
        return f"<ABIDataset {self.platform}{band} {self.scene} {Path(self.path).name}>"

    def _read_time_bounds(self):
        import netCDF4

        if "time_bounds" not in self._nc.variables:
            return None
        variable = self._nc.variables["time_bounds"]
        # time_bounds carries no units of its own; they live on "t".
        units = getattr(variable, "units", None)
        if units is None and "t" in self._nc.variables:
            units = getattr(self._nc.variables["t"], "units", None)
        if units is None:
            return None
        return netCDF4.num2date(
            variable[:], units,
            only_use_cftime_datetimes=False, only_use_python_datetimes=True,
        )

    @property
    def start_time(self):
        return self.time_bounds[0] if self.time_bounds is not None else None

    # -- domain to pixel window -------------------------------------------
    def pixels_of_domain(self, domain, margin=2):
        """Index window ``(xmin, xmax, ymin, ymax)`` covering a domain.

        ``domain`` is ``[LonMin, LonMax, LatMin, LatMax]``. The domain edges are
        sampled and converted to scan angles, so the whole grid never has to be
        geolocated.
        """
        lon_min, lon_max, lat_min, lat_max = (float(v) for v in domain)
        if lon_min >= lon_max or lat_min >= lat_max:
            raise ValueError(
                "domain must be [LonMin, LonMax, LatMin, LatMax] with "
                "LonMin < LonMax and LatMin < LatMax"
            )

        # Sample the whole box, not just its outline. On a geostationary grid
        # the scan-angle extremes can fall inside the box rather than on its
        # edge, and sampling only the edges then grabs a much larger window.
        edge = np.linspace(0.0, 1.0, 101)
        grid_lon, grid_lat = np.meshgrid(
            lon_min + edge * (lon_max - lon_min),
            lat_min + edge * (lat_max - lat_min),
        )
        lons, lats = grid_lon.ravel(), grid_lat.ravel()

        scan_x, scan_y = lonlat_to_scan(
            lons, lats, self.satellite_height, self.satellite_longitude, self.sweep
        )
        if not np.any(np.isfinite(scan_x)):
            raise ValueError(
                "The domain does not intersect what this satellite can see."
            )

        x_index = np.searchsorted(self.x, np.nanmin(scan_x)), np.searchsorted(self.x, np.nanmax(scan_x))
        # y decreases with index on the ABI grid, so search on a reversed copy.
        descending = self.y[0] > self.y[-1]
        reference = self.y[::-1] if descending else self.y
        low = np.searchsorted(reference, np.nanmin(scan_y))
        high = np.searchsorted(reference, np.nanmax(scan_y))
        if descending:
            size = self.y.size
            y_index = size - high - 1, size - low - 1
        else:
            y_index = low, high

        xmin = max(0, min(x_index) - margin)
        xmax = min(self.x.size - 1, max(x_index) + margin)
        ymin = max(0, min(y_index) - margin)
        ymax = min(self.y.size - 1, max(y_index) + margin)
        if xmin >= xmax or ymin >= ymax:
            raise ValueError("The domain falls outside this file's coverage.")
        return xmin, xmax, ymin, ymax

    # -- the image ---------------------------------------------------------
    def image(self, parameter="Rad", lonlat="center", domain=None,
              domain_in_pixels=None, stride=1):
        """Read a parameter, optionally cropped, with its coordinates.

        parameter
            A variable in the file (``Rad``, ``CMI`` ...), or one of the
            derived names ``BT`` (brightness temperature, kelvin) and ``Ref``
            (reflectance factor), computed from ``Rad`` with the calibration
            coefficients stored in the file.
        lonlat
            ``"center"`` for pixel centres, ``"corner"`` for pixel corners
            (what ``pcolormesh`` wants), or ``None`` to skip the coordinates.
        domain
            ``[LonMin, LonMax, LatMin, LatMax]``, or ``None`` for everything.
        domain_in_pixels
            ``[XMIN, XMAX, YMIN, YMAX]`` if you would rather give indices.
        stride
            Take every n-th pixel. Useful for a quick look at a Full Disk.

        Returns ``(field, longitude, latitude)``; the coordinates are ``None``
        when ``lonlat`` is ``None``.
        """
        if domain is not None and domain_in_pixels is not None:
            raise ValueError("Give either domain or domain_in_pixels, not both.")

        if domain is not None:
            xmin, xmax, ymin, ymax = self.pixels_of_domain(domain)
        elif domain_in_pixels is not None:
            xmin, xmax, ymin, ymax = (int(v) for v in domain_in_pixels)
        else:
            xmin, xmax, ymin, ymax = 0, self.x.size - 1, 0, self.y.size - 1

        x_slice = slice(xmin, xmax + 1, stride)
        y_slice = slice(ymin, ymax + 1, stride)
        x = self.x[x_slice]
        y = self.y[y_slice]

        values, standard_name, units, long_name = self._read_parameter(
            parameter, y_slice, x_slice
        )
        field = Field(values, standard_name, units, long_name, self.time_bounds)

        if lonlat is None:
            return field, None, None
        if lonlat == "center":
            longitude, latitude = scan_to_lonlat(
                x, y, self.satellite_height, self.satellite_longitude, self.sweep
            )
        elif lonlat == "corner":
            longitude, latitude = corner_lonlat(
                x, y, self.satellite_height, self.satellite_longitude, self.sweep
            )
        else:
            raise ValueError("lonlat must be 'center', 'corner' or None")

        return (field,
                Field(longitude, "longitude", "degrees_east"),
                Field(latitude, "latitude", "degrees_north"))

    def _read_parameter(self, parameter, y_slice, x_slice):
        """Read a stored variable, or derive BT / reflectance from Rad."""
        derived = parameter in ("BT", "Ref")
        name = "Rad" if derived else parameter
        if name not in self._nc.variables:
            available = ", ".join(sorted(self._nc.variables))
            raise KeyError(f"'{parameter}' is not in this file. Available: {available}")

        variable = self._nc.variables[name]
        values = np.asarray(variable[y_slice, x_slice], dtype="float32")
        values = np.where(np.isfinite(values), values, np.nan)

        if not derived:
            return (values,
                    getattr(variable, "standard_name", name),
                    getattr(variable, "units", ""),
                    getattr(variable, "long_name", ""))

        if parameter == "BT":
            fk1 = float(self._nc.variables["planck_fk1"][0])
            fk2 = float(self._nc.variables["planck_fk2"][0])
            bc1 = float(self._nc.variables["planck_bc1"][0])
            bc2 = float(self._nc.variables["planck_bc2"][0])
            with np.errstate(invalid="ignore", divide="ignore"):
                brightness = (fk2 / np.log((fk1 / values) + 1.0) - bc1) / bc2
            return brightness, "brightness_temperature", "K", "Brightness temperature"

        kappa = float(self._nc.variables["kappa0"][0])
        return values * kappa, "reflectance", "1", "Reflectance factor"


def open_dataset(path):
    """Open one ABI file. See :class:`ABIDataset`."""
    return ABIDataset(path)
