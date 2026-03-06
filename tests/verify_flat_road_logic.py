import asyncio
import numpy as np
from app.core.services.yakit_tahmin_service import YakitTahminService


async def test_flat_road_impact():
    print("🚀 Yakıt Tahmin - Düz Yol Mesafesi Etki Testi")

    service = YakitTahminService()

    # 5 Parametreli Model Eğit (Mock)
    # mesafe_km, ton, ascent_m, zorluk_val, flat_dist_km
    X = np.array(
        [
            [100, 20, 0, 0, 100],  # Tamamı Düz
            [100, 20, 500, 1, 50],  # Yarı Düz, Yarı Rampa
            [100, 20, 1000, 2, 0],  # Tamamı Dağlık
            [100, 20, 100, 0, 90],
            [100, 20, 600, 1, 40],
            [100, 20, 1200, 2, 10],
        ]
    )
    y = np.array([24, 32, 48, 26, 35, 52])

    service.model.fit(X, y)
    service.model._is_fitted = True

    # Mock AnalizRepo
    params = {
        "coefficients": {
            "weights": service.model.coefficients.tolist(),
            "intercept": float(service.model.intercept),
        },
        "r_squared": service.model.r_squared_score,
        "scaling": service.model.get_scaling_params(),
        "sample_count": 6,
        "updated_at": "2026-02-05",
    }

    class MockRepo:
        async def get_model_params(self, id):
            return params

    service._analiz_repo = MockRepo()

    print("\n[Senaryo Karşılaştırması - 100km, 20 Ton]")

    scenarios = [
        {"ascent": 0, "flat": 100, "zorluk": "Normal", "label": "Full Düz"},
        {"ascent": 200, "flat": 80, "zorluk": "Orta", "label": "Hafif Eğimli"},
        {"ascent": 500, "flat": 20, "zorluk": "Zor", "label": "Zor/Dağlık"},
    ]

    for s in scenarios:
        res = await service.predict(
            arac_id=1,
            mesafe_km=100,
            ton=20,
            ascent_m=s["ascent"],
            flat_distance_km=s["flat"],
            zorluk=s["zorluk"],
        )
        tahmin = res.get("tahmin_litre", 0)
        print(
            f"🔹 {s['label']:12} -> Düz Yol: {s['flat']}km, Tahmin: {tahmin:.1f} Litre"
        )


if __name__ == "__main__":
    asyncio.run(test_flat_road_impact())
