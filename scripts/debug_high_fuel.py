import sys
import os

# Add project root
sys.path.append(os.getcwd())

from app.core.ml.physics_fuel_predictor import (
    PhysicsBasedFuelPredictor,
    RouteConditions,
    VehicleSpecs,
)


def debug_physics_model():
    print("--- Physics Model Deep Dive ---")

    # 1. Initialize Predictor
    vehicle = VehicleSpecs()  # Defaults: 7500kg empty, 0.42 efficiency
    predictor = PhysicsBasedFuelPredictor(vehicle)

    print(
        f"Vehicle: Empty={vehicle.empty_weight_kg}kg, Eff={vehicle.engine_efficiency}"
    )

    # 2. Scenarios
    scenarios = [
        {"km": 177.0, "ton": 0, "ascent": 0, "descent": 0},
        {"km": 177.0, "ton": 24, "ascent": 0, "descent": 0},
        {"km": 177.0, "ton": 24, "ascent": 500, "descent": 500},  # Hilly
    ]

    for s in scenarios:
        print(f"\nScanning Route: {s['km']}km, {s['ton']} tons")

        route = RouteConditions(
            distance_km=s["km"],
            load_ton=float(s["ton"]),
            ascent_m=s["ascent"],
            descent_m=s["descent"],
            avg_speed_kmh=70,
            road_quality=1.0,
            weather_factor=1.0,  # 1.15 for weather test
        )

        # Predict
        res = predictor.predict(route)

        print(f"  -> Total Liters: {res.total_liters}")
        print(f"  -> L/100km: {res.consumption_l_100km}")
        print(f"  -> Breakdown: {res.energy_breakdown}")
        print(f"  -> Factors: {res.factors_used}")

    print("\n--- Weather Impact Test (24 ton, 177km) ---")
    route_w = RouteConditions(distance_km=177.0, load_ton=24.0, weather_factor=1.15)
    res_w = predictor.predict(route_w)
    print(f"  -> Weather 1.15 => {res_w.total_liters} Liters")

    print("\n--- Round Trip Hypothesis (177km Full + 177km Empty) ---")
    # 1. Going Full
    route_go = RouteConditions(distance_km=177.0, load_ton=24.0, weather_factor=1.15)
    res_go = predictor.predict(route_go)

    # 2. Return Empty
    route_back = RouteConditions(
        distance_km=177.0, load_ton=0.0, is_empty_trip=True, weather_factor=1.15
    )
    res_back = predictor.predict(route_back)

    total = res_go.total_liters + res_back.total_liters
    print(f"  Going (Full): {res_go.total_liters} L")
    print(f"  Back (Empty): {res_back.total_liters} L")
    print(f"  Total: {total} L")

    print("\n--- Ensemble Model Test ---")
    try:
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        ensemble = EnsembleFuelPredictor(vehicle)
        # Mocking untrained state first
        print(f"Ensemble Trained: {ensemble.is_trained}")

        route_ens = {"mesafe_km": 177.0, "ton": 24.0, "weather_factor": 1.15}
        res_ens = ensemble.predict(route_ens)
        print(
            f"Ensemble Prediction: {res_ens.tahmin_l_100km} L/100km -> {res_ens.tahmin_l_100km * 1.77:.1f} Liters"
        )
        print(
            f"Breakdown: Physics={res_ens.physics_only}, ML_Correction={res_ens.ml_correction}"
        )

    except Exception as e:
        print(f"Ensemble Test Failed: {e}")

    print("\n--- Specific Route Test (Tekirdag -> Istanbul) ---")
    # 177.6 km, Ascent: 2146m, Descent: 2185m
    route_tekirdag = RouteConditions(
        distance_km=177.6,
        load_ton=24.0,  # Assuming full load
        ascent_m=2146.6,
        descent_m=2185.6,
        weather_factor=1.0,  # Baseline first
    )
    res_tek = predictor.predict(route_tekirdag)
    print(
        f"  Tekirdag (24t, Normal Weather) -> {res_tek.total_liters} L ({res_tek.consumption_l_100km} L/100km)"
    )
    print(f"  Breakdown: {res_tek.energy_breakdown}")

    # With Weather
    route_tek_w = RouteConditions(
        distance_km=177.6,
        load_ton=24.0,
        ascent_m=2146.6,
        descent_m=2185.6,
        weather_factor=1.15,
    )
    res_tek_w = predictor.predict(route_tek_w)
    print(f"  Tekirdag (24t, Bad Weather 1.15) -> {res_tek_w.total_liters} L")

    print("\n--- Tekirdag Round Trip Hypothesis (Full + Empty) ---")
    # Going: Tekirdag -> Istanbul (Ascent 2146m)
    route_go = RouteConditions(
        distance_km=177.6,
        load_ton=24.0,
        ascent_m=2146.6,
        descent_m=2185.6,
        weather_factor=1.15,
    )
    res_go = predictor.predict(route_go)

    # Return: Istanbul -> Tekirdag (Ascent 2185m)
    route_back = RouteConditions(
        distance_km=177.6,
        load_ton=0.0,
        is_empty_trip=True,
        ascent_m=2185.6,  # Reverse ascent/descent
        descent_m=2146.6,
        weather_factor=1.15,
    )
    res_back = predictor.predict(route_back)

    total = res_go.total_liters + res_back.total_liters
    print(f"  Going (24t): {res_go.total_liters} L")
    print(f"  Return (0t): {res_back.total_liters} L")
    print(f"  Total Round Trip: {total} L")


if __name__ == "__main__":
    debug_physics_model()
