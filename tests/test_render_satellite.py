from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from examples.render_satellite import (
    DOMAIN_BBOXES,
    expand_inputs,
    has_viirs_geolocation,
    resolve_bbox,
    validate_bbox,
)


class InputExpansionTests(TestCase):
    def test_directory_filters_and_sorts_supported_files(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "b.h5").touch()
            (root / "a.nc").touch()
            (root / "notes.txt").touch()

            result = expand_inputs([str(root)])

            self.assertEqual(
                result,
                [str((root / "a.nc").resolve()), str((root / "b.h5").resolve())],
            )

    def test_glob_pattern_is_expanded(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "one.nc").touch()
            (root / "two.h5").touch()

            result = expand_inputs([str(root / "*.nc")])

            self.assertEqual(result, [str((root / "one.nc").resolve())])

    def test_viirs_terrain_corrected_geolocation_is_detected(self):
        files = [
            "/data/SVI01_npp_example.h5",
            "/data/GITCO_npp_example.h5",
        ]

        self.assertTrue(has_viirs_geolocation(files))
        self.assertFalse(has_viirs_geolocation(files[:1]))


class DomainTests(TestCase):
    def test_named_domain_returns_expected_bbox(self):
        self.assertEqual(resolve_bbox("azores", None), DOMAIN_BBOXES["azores"])

    def test_full_disk_keeps_source_extent(self):
        self.assertIsNone(resolve_bbox("full-disk", None))

    def test_custom_bbox_overrides_named_domain(self):
        custom = (-30, 35, -20, 43)
        self.assertEqual(resolve_bbox("conus", custom), custom)

    def test_custom_domain_requires_bbox(self):
        with self.assertRaisesRegex(ValueError, "requer --bbox"):
            resolve_bbox("custom", None)

    def test_bbox_order_is_validated(self):
        with self.assertRaisesRegex(ValueError, "longitude inválida"):
            validate_bbox((10, 30, -10, 40))
