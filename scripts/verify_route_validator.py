import sys
import os
import unittest

sys.path.append(os.getcwd())

from app.core.services.route_validator import RouteValidator


class TestRouteValidator(unittest.TestCase):
    def test_normal_route(self):
        # 100km, 500m ascent (0.5%) -> Should be OK
        data = {"distance_km": 100.0, "ascent_m": 500.0, "descent_m": 500.0}
        corrected = RouteValidator.validate_and_correct(data)
        self.assertEqual(corrected["ascent_m"], 500.0)
        self.assertNotIn("is_corrected", corrected)

    def test_anomalous_route(self):
        # 100km, 5000m ascent (5.0%) -> Should be corrected
        # Threshold is 2.5% (0.025). 5.0% > 2.5%
        # Correction cap is 1.5% (0.015) -> 100km * 1000 * 0.015 = 1500m
        data = {"distance_km": 100.0, "ascent_m": 5000.0, "descent_m": 500.0}
        corrected = RouteValidator.validate_and_correct(data)

        print(f"\nAnomalous Input: {data}")
        print(f"Corrected Output: {corrected}")

        self.assertTrue(corrected.get("is_corrected"))
        self.assertEqual(corrected["ascent_m"], 1500.0)

    def test_tekirdag_case(self):
        # 177km, 2146m ascent (1.2%) -> Should PASS (below 2.5%)
        # Unless we lower threshold.
        data = {"distance_km": 177.0, "ascent_m": 2146.0, "descent_m": 0.0}
        corrected = RouteValidator.validate_and_correct(data)

        print(f"\nTekirdag Case: {data}")
        print(f"Output: {corrected}")

        if corrected.get("is_corrected"):
            print("Tekirdag was CORRECTED (Threshold strict)")
        else:
            print("Tekirdag was ACCEPTED (Threshold loose)")


if __name__ == "__main__":
    unittest.main()
