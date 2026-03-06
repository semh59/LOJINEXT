import sys
import os
import asyncio

sys.path.append(os.getcwd())

from app.database.unit_of_work import UnitOfWork
from app.database.models import Sefer
from sqlalchemy import select
from app.infrastructure.logging.logger import get_logger

logger = get_logger("RepairScript")


async def repair_anomalies():
    print("--- Elevation Repair Script Starting ---")

    async with UnitOfWork() as uow:
        # Find all trips (or those with suspicious elevation)
        # 1288m was the report, but let's be more sensitive.
        stmt = select(Sefer).where(Sefer.ascent_m > 100)
        result = await uow.session.execute(stmt)
        trips = result.scalars().all()

        repaired_count = 0

        for t in trips:
            dist = t.mesafe_km
            ascent = t.ascent_m or 0.0

            # Simple Grade Check: ascent_m / (km * 1000)
            if dist > 0:
                grade = ascent / (dist * 1000)

                # Highway Limit: Typically 1.2% - 1.5% max over long stretches
                # Let's use 1.5% as a guardrail.
                if grade > 0.015:
                    old_ascent = ascent
                    # Correct using RouteValidator logic or 1.2% hard cap
                    new_ascent = round(dist * 1000 * 0.012, 1)

                    print(
                        f"Repairing Trip {t.id} ({t.sefer_no}): {old_ascent}m -> {new_ascent}m (Dist: {dist}km)"
                    )

                    t.ascent_m = new_ascent
                    # Also fix descent if needed (assuming symmetry)
                    if t.descent_m and t.descent_m > old_ascent * 0.8:
                        t.descent_m = new_ascent

                    # Trigger re-prediction after fixing data
                    from app.services.prediction_service import get_prediction_service

                    pred_service = get_prediction_service()

                    try:
                        pred_res = await pred_service.predict_consumption(
                            arac_id=t.arac_id,
                            mesafe_km=dist,
                            ton=t.ton or 0.0,
                            ascent_m=t.ascent_m,
                            descent_m=t.descent_m or 0.0,
                            flat_distance_km=t.flat_distance_km or 0.0,
                            sofor_id=t.sofor_id,
                            target_date=t.tarih,
                            bos_sefer=t.bos_sefer,
                        )
                        if pred_res and "prediction_liters" in pred_res:
                            t.tahmini_tuketim = float(pred_res["prediction_liters"])
                            print(f"  New Prediction: {t.tahmini_tuketim} L")
                    except Exception as e:
                        print(f"  Prediction redo failed for {t.id}: {e}")

                    repaired_count += 1

        if repaired_count > 0:
            await uow.commit()
            print(f"Successfully repaired {repaired_count} records.")
        else:
            print("No anomalous records found above threshold.")


if __name__ == "__main__":
    asyncio.run(repair_anomalies())
