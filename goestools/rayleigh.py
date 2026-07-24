"""Rayleigh (molecular) scattering correction for the visible ABI channels.

Sunlight scattered by air molecules never reaches the ground: it adds a bluish
veil on top of the real scene. The veil grows with the length of the air path,
so it is worst where the sun is low or the satellite looks in at a slant --
exactly the case for Alaska seen from a satellite parked over the equator at
137 W. Removing it is what turns a milky True Color into a crisp one.

The correction here is single-scattering: the atmosphere is treated as one thin
layer that scatters once. That captures nearly all of the effect for the short
ABI channels and needs no lookup tables.

    corrected = correct_rayleigh(reflectance, wavelength_um,
                                 solar_zenith, view_zenith, relative_azimuth)
"""

from __future__ import annotations

import numpy as np

# Central wavelengths (um) of the ABI channels this applies to.
CHANNEL_WAVELENGTH = {"C01": 0.47, "C02": 0.64, "C03": 0.86}


def optical_depth(wavelength_um, surface_pressure_hpa=1013.25):
    """Rayleigh optical depth of the whole atmosphere at one wavelength.

    Hansen and Travis (1974), scaled by surface pressure so high ground gets
    less atmosphere above it.
    """
    w = float(wavelength_um)
    depth = 0.008569 * w ** -4 * (1.0 + 0.0113 * w ** -2 + 0.00013 * w ** -4)
    return depth * (surface_pressure_hpa / 1013.25)


def phase_function(scattering_angle_deg):
    """Rayleigh phase function: scattering is strongest forward and backward."""
    cosine = np.cos(np.radians(scattering_angle_deg))
    return 0.75 * (1.0 + cosine ** 2)


def scattering_angle(solar_zenith, view_zenith, relative_azimuth):
    """Angle between the incoming sunlight and the direction to the satellite."""
    sun = np.radians(np.asarray(solar_zenith, dtype=float))
    view = np.radians(np.asarray(view_zenith, dtype=float))
    azimuth = np.radians(np.asarray(relative_azimuth, dtype=float))
    # Backscatter convention: light comes down and is scattered back up, so a
    # nadir view with the sun overhead is a 180 degree turn.
    cosine = (-np.cos(sun) * np.cos(view)
              + np.sin(sun) * np.sin(view) * np.cos(azimuth))
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))


def rayleigh_reflectance(wavelength_um, solar_zenith, view_zenith,
                         relative_azimuth, surface_pressure_hpa=1013.25):
    """The reflectance the air itself contributes, with nothing below it.

    Single scattering, so the light is scattered once on its way in or out.
    """
    sun = np.radians(np.clip(np.asarray(solar_zenith, dtype=float), 0.0, 89.0))
    view = np.radians(np.clip(np.asarray(view_zenith, dtype=float), 0.0, 89.0))

    depth = optical_depth(wavelength_um, surface_pressure_hpa)
    angle = scattering_angle(np.degrees(sun), np.degrees(view), relative_azimuth)

    mu_sun, mu_view = np.cos(sun), np.cos(view)
    # Single-scattering path reflectance. It is not attenuated by the full
    # path: the scattered light is produced all the way through the column.
    return depth * phase_function(angle) / (4.0 * mu_sun * mu_view)


def correct_rayleigh(reflectance, wavelength_um, solar_zenith, view_zenith,
                     relative_azimuth, surface_pressure_hpa=1013.25):
    """Take the molecular haze out of a reflectance.

    Subtracts what the air scattered and divides out what it absorbed on the
    way through, so what is left is the scene itself.
    """
    haze = rayleigh_reflectance(wavelength_um, solar_zenith, view_zenith,
                                relative_azimuth, surface_pressure_hpa)
    sun = np.radians(np.clip(np.asarray(solar_zenith, dtype=float), 0.0, 89.0))
    view = np.radians(np.clip(np.asarray(view_zenith, dtype=float), 0.0, 89.0))

    depth = optical_depth(wavelength_um, surface_pressure_hpa)
    transmission = np.exp(-depth * (1.0 / np.cos(sun) + 1.0 / np.cos(view)) * 0.5)

    corrected = (np.asarray(reflectance, dtype=float) - haze) / np.maximum(
        transmission, 1e-3
    )
    return np.clip(corrected, 0.0, None)


def solar_azimuth(when, lon, lat):
    """Solar azimuth in degrees clockwise from north."""
    from .rgb import solar_zenith as _zenith

    day = when.timetuple().tm_yday
    hour = when.hour + when.minute / 60.0 + when.second / 3600.0
    gamma = 2.0 * np.pi / 365.0 * (day - 1 + (hour - 12) / 24.0)
    declination = (
        0.006918 - 0.399912 * np.cos(gamma) + 0.070257 * np.sin(gamma)
        - 0.006758 * np.cos(2 * gamma) + 0.000907 * np.sin(2 * gamma)
        - 0.002697 * np.cos(3 * gamma) + 0.00148 * np.sin(3 * gamma)
    )
    equation_of_time = 229.18 * (
        0.000075 + 0.001868 * np.cos(gamma) - 0.032077 * np.sin(gamma)
        - 0.014615 * np.cos(2 * gamma) - 0.040849 * np.sin(2 * gamma)
    )
    offset = equation_of_time + 4.0 * np.asarray(lon, dtype=float)
    hour_angle = np.radians((hour * 60.0 + offset) / 4.0 - 180.0)

    latitude = np.radians(np.asarray(lat, dtype=float))
    zenith = np.radians(_zenith(when, lon, lat))
    with np.errstate(invalid="ignore", divide="ignore"):
        cosine = ((np.sin(declination) - np.sin(latitude) * np.cos(zenith))
                  / (np.cos(latitude) * np.sin(zenith)))
    azimuth = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
    return np.where(hour_angle > 0, 360.0 - azimuth, azimuth)


def satellite_azimuth(lon, lat, satellite_lon):
    """Azimuth from each point towards the satellite, clockwise from north."""
    latitude = np.radians(np.asarray(lat, dtype=float))
    delta = np.radians(satellite_lon - np.asarray(lon, dtype=float))
    y = np.sin(delta)
    x = -np.sin(latitude) * np.cos(delta)
    return np.degrees(np.arctan2(y, x)) % 360.0
