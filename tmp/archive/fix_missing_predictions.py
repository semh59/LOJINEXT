import sys
import os
import asyncio

sys.path.append(os.getcwd())

from app.database.unit_of_work import UnitOfWork
from app.services.prediction_service import get_prediction_service
from app.database.models import Sefer
from sqlalchemy import select


async def fix_predictions():
    print("Starting prediction backfill...")
    pred_service = get_prediction_service()

    async with UnitOfWork() as uow:
        # Find trips with missing prediction but valid route
        stmt = select(Sefer).where(
            Sefer.tahmini_tuketim.is_(None), Sefer.guzergah_id.is_not(None)
        )
        result = await uow.session.execute(stmt)
        trips = result.scalars().all()

        print(f"Found {len(trips)} trips needing prediction.")

        for t in trips:
            print(f"Processing Trip {t.id} (Route {t.guzergah_id})...")

            # Get route details
            route_dict = await uow.lokasyon_repo.get_by_id(t.guzergah_id)
            if not route_dict:
                print(f"  Route {t.guzergah_id} not found, skipping.")
                continue

            try:
                # Ascent/Descent might be in trip or route
                ascent = t.ascent_m or route_dict.get("ascent_m", 0.0)
                descent = t.descent_m or route_dict.get("descent_m", 0.0)

                # Predict
                pred = await pred_service.predict_consumption(
                    arac_id=t.arac_id,
                    mesafe_km=t.mesafe_km,
                    ton=t.ton or (t.net_kg / 1000 if t.net_kg else 0.0),
                    ascent_m=ascent,
                    descent_m=descent,
                    flat_distance_km=t.flat_distance_km or 0.0,
                    sofor_id=t.sofor_id,
                    target_date=t.tarih,
                    bos_sefer=t.bos_sefer,
                    route_analysis={
                        "weather_factor": 1.0
                    },  # Simplified, weather service lookup is complex here
                )

                if pred and "tahmini_tuketim" in pred:
                    t.tahmini_tuketim = pred["tahmini_tuketim"]
                    print(f"  Updated: {t.tahmini_tuketim} L/100km")

            except Exception as e:
                print(f"  Failed: {e}")

        await uow.commit()
    print("Backfill complete.")


if __name__ == "__main__":
    asyncio.run(fix_predictions())
