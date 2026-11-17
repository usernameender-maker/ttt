import unittest

from ievf.phrase_communication import build_navigation_catalog, determine_phrase


class PhraseCommunicationNavigationTests(unittest.TestCase):
    def test_basic_english_navigation(self):
        catalog = build_navigation_catalog()
        result = catalog.determine("turn left", "en")
        self.assertEqual(result["template_id"], "basic_turn_left")
        self.assertEqual(result["stage"], "basic")
        self.assertEqual(result["slots"], {})

    def test_travel_expression_with_slots(self):
        catalog = build_navigation_catalog()
        result = catalog.determine("travel to docking bay 3", "en")
        self.assertEqual(result["template_id"], "travel_to_place")
        self.assertEqual(result["slots"], {"destination": "docking bay 3"})

    def test_space_route_expression(self):
        catalog = build_navigation_catalog()
        result = catalog.determine("move to sector gamma", "en")
        self.assertEqual(result["template_id"], "space_sector")
        self.assertEqual(result["slots"], {"sector": "gamma"})

    def test_spanish_navigation_phrase(self):
        catalog = build_navigation_catalog()
        result = catalog.determine("viaja hacia puerta 7", "es")
        self.assertEqual(result["template_id"], "travel_to_place_es")
        self.assertEqual(result["slots"], {"destination": "puerta 7"})

    def test_ambiguous_phrase_raises(self):
        catalog = build_navigation_catalog()
        with self.assertRaisesRegex(ValueError, "Ambiguous phrase match"):
            catalog.determine("move forward", "en")

    def test_missing_phrase_raises(self):
        catalog = build_navigation_catalog()
        with self.assertRaisesRegex(ValueError, "No template matched"):
            catalog.determine("recalibrate engine", "en")

    def test_default_factory(self):
        result = determine_phrase("land on luna station", "en")
        self.assertEqual(result["template_id"], "space_land")
        self.assertEqual(result["slots"], {"location": "luna station"})


if __name__ == "__main__":
    unittest.main()
