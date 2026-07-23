from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from examples.render_satellite import (
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
    def test_missing_domain_keeps_source_extent(self):
        self.assertIsNone(resolve_bbox(None))

    def test_user_domain_is_returned(self):
        custom = (-166.5, 54.0, -162.0, 56.5)
        self.assertEqual(resolve_bbox(custom), custom)

    def test_domain_order_is_validated(self):
        with self.assertRaisesRegex(ValueError, "invalid longitude limits"):
            validate_bbox((10.0, 30.0, -10.0, 40.0))
