from unittest import TestCase

from examples.goes18_coverage_data import source_url


class Goes18CoverageDataTests(TestCase):
    def test_full_disk_uses_the_3_october_1900_scan(self):
        url = source_url("full_disk", "C09")

        self.assertIn("/ABI-L1b-RadF/2023/276/19/", url)
        self.assertIn("s20232761900206", url)

    def test_conus_uses_the_nearest_1901_scan(self):
        url = source_url("conus", "C09")

        self.assertIn("/ABI-L1b-RadC/2023/276/19/", url)
        self.assertIn("s20232761901171", url)

    def test_mesoscale_uses_mesoscale_1_at_1900(self):
        url = source_url("mesoscale", "C09")

        self.assertIn("/ABI-L1b-RadM/2023/276/19/", url)
        self.assertIn("RadM1", url)
        self.assertIn("s20232761900279", url)

    def test_unknown_coverage_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported coverage/channel"):
            source_url("unknown", "C09")
