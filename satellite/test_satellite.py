
import unittest

from satellite_analysis import (
    point_in_geometry,
    is_valid_location,
    assess_location
)


class TestSatelliteAnalysis(unittest.TestCase):

    # Artificial polygon used only for testing the algorithm.
    # It is NOT a real Odisha flood boundary.
    test_polygon = {
        "type": "Polygon",
        "coordinates": [[
            [85.0, 20.0],
            [86.0, 20.0],
            [86.0, 21.0],
            [85.0, 21.0],
            [85.0, 20.0]
        ]]
    }

    def test_location_inside_polygon(self):
        result = point_in_geometry(
            20.5, 85.5, self.test_polygon
        )
        self.assertTrue(result)

    def test_location_outside_polygon(self):
        result = point_in_geometry(
            22.0, 88.0, self.test_polygon
        )
        self.assertFalse(result)

    def test_valid_coordinates(self):
        self.assertTrue(is_valid_location(20.5, 85.5))

    def test_invalid_coordinates(self):
        self.assertFalse(is_valid_location(100, 85.5))
        self.assertFalse(is_valid_location(20.5, 200))

    def test_empty_flood_zones(self):
        result = assess_location(20.2961, 85.8245)

        self.assertEqual(
            result["assessment_status"],
            "data_unavailable"
        )


if __name__ == "__main__":
    unittest.main()
