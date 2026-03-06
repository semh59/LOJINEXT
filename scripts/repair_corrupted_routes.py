import asyncio
import sys
import os

# Root dizini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.unit_of_work import get_uow
from app.services.prediction_service import get_prediction_service
from app.core.services.route_validator import RouteValidator
from app.infrastructure.logging.logger import get_logger

logger = get_logger("repair_script")


async def repair_all():
    """
    Hem seferleri hem de lokasyon özetlerini düzelt.
    """
    print("--- Fuel Prediction: Deep Smoothing & Repair Script ---")
    SMOOTHING_FACTOR = 0.6

    async with get_uow() as uow:
        # 1. Önce Lokasyonları düzelt (Cache root cause)
        locations = await uow.lokasyon_repo.get_all(limit=2000)
        loc_count = 0
        for loc in locations:
            # Sadece legacy veya gürültülü verileri düzelt (ascent > 0)
            if loc.get("ascent_m", 0) > 0:
                old_ascent = loc["ascent_m"]
                old_descent = loc["descent_m"]

                # Apply Smoothing
                new_ascent = round(old_ascent * SMOOTHING_FACTOR, 1)
                new_descent = round(old_descent * SMOOTHING_FACTOR, 1)

                # Apply Validator (Cap)
                original_data = {
                    "distance_km": loc["mesafe_km"],
                    "ascent_m": new_ascent,
                    "descent_m": new_descent,
                }
                corrected_data = RouteValidator.validate_and_correct(original_data)

                final_ascent = corrected_data["ascent_m"]
                final_descent = corrected_data["descent_m"]

                if final_ascent != old_ascent:
                    await uow.lokasyon_repo.update(
                        loc["id"],
                        ascent_m=final_ascent,
                        descent_m=final_descent,
                        is_corrected=True,
                        correction_reason="Phase 9 Smoothing",
                    )
                    loc_count += 1

        print(f"Repaired {loc_count} cached locations.")

        # 2. Seferleri düzelt
        trips = await uow.sefer_repo.get_all(limit=1000)
        trip_count = 0
        pred_service = get_prediction_service()

        for trip in trips:
            dist = trip.get("mesafe_km", 0)
            ascent = trip.get("ascent_m", 0)

            if not dist or not ascent:
                continue

            # Sefer verisine de smoothing uygula (Eğer daha önce uygulanmadıysa)
            # Not: Eğer ascent bariz gürültülüyse (%1'den fazlaysa) düzelt
            # FORCE: Phase 9 parameter calibration requires a full recalculation
            if ascent > 0:
                final_ascent = ascent
                final_descent = trip.get("descent_m", 0)

                # Sadece orjinal (ham) veri gibi duruyorsa smoothing yap
                if ascent / (dist * 1000) > 0.010:
                    final_ascent = round(ascent * SMOOTHING_FACTOR, 1)
                    final_descent = round(final_descent * SMOOTHING_FACTOR, 1)

                # Tahmini baştan hesapla
                prediction = await pred_service.predict_consumption(
                    arac_id=trip["arac_id"],
                    mesafe_km=dist,
                    ton=trip.get("ton", 0) or 0.0,
                    ascent_m=final_ascent,
                    descent_m=final_descent,
                    flat_distance_km=trip.get("flat_distance_km", 0),
                    sofor_id=trip.get("sofor_id"),
                    target_date=trip.get("tarih"),
                )

                new_tuk = prediction.get("prediction_liters")

                await uow.sefer_repo.update_sefer(
                    id=trip["id"],
                    ascent_m=final_ascent,
                    descent_m=final_descent,
                    tahmini_tuketim=new_tuk,
                )
                trip_count += 1

        await uow.commit()
        print(f"Repaired {trip_count} trips.")


if __name__ == "__main__":
    asyncio.run(repair_all())
