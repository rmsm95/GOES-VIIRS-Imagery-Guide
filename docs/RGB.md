# How RGB composites work

An RGB composite places three normalized arrays into the red, green, and blue channels of an image:

```text
rgb_image = stack(red, green, blue)
```

Each component can be:

- reflectance from a visible or near-infrared band;
- brightness temperature from a thermal band;
- a difference between two brightness temperatures;
- a synthetic combination of multiple bands.

## Core processing steps

1. Gather files from the same observation.
2. Read physical values and remove fill or invalid pixels.
3. Resample every channel to a common grid.
4. Apply the recipe: single band, combination, or difference.
5. Clip each component to its selected physical range.
6. Normalize each component to `0–1`.
7. Invert components when required by the recipe.
8. Apply gamma correction and combine red, green, and blue.

For a value `x` and limits `minimum` and `maximum`, basic normalization is:

```python
normalized = clip((x - minimum) / (maximum - minimum), 0, 1)
```

Gamma correction is:

```python
corrected = normalized ** (1 / gamma)
```

Satpy already provides recipes, calibration, resampling, and enhancements. The example code therefore accepts a composite name instead of manually repeating every operation.

## GOES ABI True Color with synthetic green

ABI has blue (`C01`, 0.47 µm), red (`C02`, 0.64 µm), and vegetation (`C03`, 0.86 µm), but no pure green band.

The CIMSS recipe approximates green as:

```text
R = C02
G = 0.45 × C02 + 0.10 × C03 + 0.45 × C01
B = C01
```

This is a daytime composite and depends on sunlight. Complete processing can also apply Rayleigh-scattering correction and enhancements.

Source: [NOAA/CIMSS Natural True Color Quick Guide](https://www.star.nesdis.noaa.gov/GOES/documents/ABIQuickGuide_CIMSSRGB_v2.pdf).

## GOES ABI Day Land Cloud / Natural Color

This recipe uses:

```text
R = C05 (1.6 µm)
G = C03 (0.86 µm)
B = C02 (0.64 µm)
```

Typical interpretation:

- vegetation: green;
- dry soil or inactive vegetation: brown;
- water clouds: gray or white;
- ice, snow, and high clouds: cyan.

This is also a daytime composite. The 1.6 µm band absorbs strongly in ice, helping separate water clouds from ice.

Source: [NOAA Day Land Cloud RGB Quick Guide](https://www.star.nesdis.noaa.gov/goes/documents/QuickGuide_GOESR_daylandcloudRGB_final.pdf).

## GOES ABI Nighttime Microphysics

This composite uses brightness-temperature differences:

```text
R = C15 (12.4 µm) − C13 (10.3 µm)
G = C13 (10.3 µm) − C07 (3.9 µm)
B = C13 (10.3 µm)
```

It helps separate fog, low clouds, water clouds, and ice clouds at night. Limits, inversions, and enhancements are essential parts of the recipe; use Satpy's `night_microphysics` composite.

Source: [NOAA Nighttime Microphysics RGB Quick Guide](https://www.star.nesdis.noaa.gov/goes/documents/QuickGuide_GOESR_NtMicroRGB_final.pdf).

## GOES ABI Air Mass RGB

This composite combines water-vapor and ozone differences with a water-vapor band:

```text
R = C08 (6.2 µm) − C10 (7.3 µm)
G = C12 (9.6 µm) − C13 (10.3 µm)
B = C08 (6.2 µm)
```

It supports analysis of upper-tropospheric features, dry-air intrusions, and differences between air masses. Use Satpy's `airmass` composite to retain standardized limits and inversions.

Source: [NOAA Air Mass RGB Quick Guide](https://www.star.nesdis.noaa.gov/goes/documents/QuickGuide_GOESR_AirMassRGB_final.pdf).

## VIIRS True Color

VIIRS moderate-resolution bands provide channels near red, green, and blue:

```text
R = M05 (0.67 µm)
G = M04 (0.55 µm)
B = M03 (0.49 µm)
```

Unlike ABI, VIIRS does not require synthetic green. Satpy can apply atmospheric correction and create the `true_color` composite.

## VIIRS false color for vegetation, snow, and clouds

Using 375 m imagery bands:

```text
R = I03 (1.61 µm)
G = I02 (0.87 µm)
B = I01 (0.64 µm)
```

This is false color: displayed colors do not match human vision. The 1.61 µm band helps distinguish liquid water, ice, and snow.

## Common mistakes

- Mixing bands from different times or scans.
- Processing VIIRS without the matching geolocation file.
- Combining reflectance and temperature without the correct recipe.
- Ignoring fill values or invalid pixels.
- Treating Full Disk, CONUS, and Mesoscale as the same grid.
- Applying True Color at night.
- Comparing images that use different limits or gamma.
- Entering latitude before longitude in `--domain`.

Run `render_satellite.py --list-composites` to see what can be created from the available files.
