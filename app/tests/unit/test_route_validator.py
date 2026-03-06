from app.core.services.route_validator import RouteValidator


class TestRouteValidator:
    def test_validate_and_correct_normal_data(self):
        """Should not modify reasonable data"""
        data = {
            "distance_km": 100.0,
            "ascent_m": 500.0,  # 0.5% grade - Normal
            "descent_m": 500.0,
            "is_corrected": False,
        }

        result = RouteValidator.validate_and_correct(data)

        assert result["ascent_m"] == 500.0
        assert result.get("is_corrected") is False

    def test_validate_and_correct_high_ascent(self):
        """Should correct excessively high ascent"""
        # 5000m ascent for 100km -> 5% average grade (Unlikely for highway)
        data = {
            "distance_km": 100.0,
            "ascent_m": 5000.0,
            "descent_m": 0.0,
        }

        result = RouteValidator.validate_and_correct(data)

        # Expected: Capped at 1.5% -> 100km * 1000 * 0.015 = 1500m
        assert result["ascent_m"] == 1500.0
        assert result["is_corrected"] is True
        assert "High Incline" in result["correction_reason"]

    def test_validate_and_correct_high_descent(self):
        """Should correct excessively high descent"""
        data = {
            "distance_km": 100.0,
            "ascent_m": 0.0,
            "descent_m": 5000.0,
        }

        result = RouteValidator.validate_and_correct(data)

        assert result["descent_m"] == 1500.0
        assert result["is_corrected"] is True

    def test_zero_distance(self):
        """Should handle zero distance gracefully"""
        data = {
            "distance_km": 0.0,
            "ascent_m": 100.0,
            "descent_m": 100.0,
        }

        result = RouteValidator.validate_and_correct(data)

        # Should not divide by zero, just return as is or handle safe
        # Current logic: avg_incline = ascent / (dist * 1000) -> DivisionByZero?
        # Let's ensure Validator handles this.
        assert result["ascent_m"] == 100.0
