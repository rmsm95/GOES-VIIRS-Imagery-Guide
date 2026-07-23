from unittest import TestCase

from examples.domains import DOMAINS, domain_names, list_domains
from examples.render_satellite import resolve_domain_tokens


class DomainRegistryTests(TestCase):
    def test_every_named_domain_is_a_valid_box(self):
        for name, box in DOMAINS.items():
            min_lon, min_lat, max_lon, max_lat = box
            self.assertLess(min_lon, max_lon, name)
            self.assertLess(min_lat, max_lat, name)
            self.assertGreaterEqual(min_lon, -180.0, name)
            self.assertLessEqual(max_lon, 180.0, name)
            self.assertGreaterEqual(min_lat, -90.0, name)
            self.assertLessEqual(max_lat, 90.0, name)

    def test_shishaldin_example_is_present(self):
        self.assertIn("shishaldin", domain_names())
        self.assertIn("shishaldin", list_domains())


class ResolveDomainTokensTests(TestCase):
    def test_missing_domain_returns_none(self):
        self.assertIsNone(resolve_domain_tokens(None))

    def test_named_domain_resolves_to_its_box(self):
        self.assertEqual(resolve_domain_tokens(["shishaldin"]), DOMAINS["shishaldin"])

    def test_four_numbers_resolve_to_a_box(self):
        self.assertEqual(
            resolve_domain_tokens(["-166.0", "54.0", "-162.0", "56.0"]),
            (-166.0, 54.0, -162.0, 56.0),
        )

    def test_unknown_name_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown domain"):
            resolve_domain_tokens(["atlantis"])

    def test_wrong_number_of_values_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "name or four numbers"):
            resolve_domain_tokens(["1.0", "2.0", "3.0"])

    def test_reversed_longitude_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid longitude"):
            resolve_domain_tokens(["10.0", "30.0", "-10.0", "40.0"])
