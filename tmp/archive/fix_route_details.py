import sys
import os
import asyncio

sys.path.append(os.getcwd())

from app.database.unit_of_work import UnitOfWork
from app.database.models import Sefer
from sqlalchemy import select


async def fix_route_details():
    print("Starting route details backfill...")

    async with UnitOfWork() as uow:
        # Find trips with valid route but missing route details
        stmt = select(Sefer).where(Sefer.guzergah_id != None)
        result = await uow.session.execute(stmt)
        trips = result.scalars().all()

        print(f"Found {len(trips)} trips to check.")

        updated_count = 0

        for t in trips:
            # Get route details
            route_dict = await uow.lokasyon_repo.get_by_id(t.guzergah_id)
            if not route_dict:
                print(f"Trip {t.id}: Route {t.guzergah_id} not found.")
                continue

            # Check if update needed
            needs_update = False

            # 1. Rota Detay (JSON)
            if not t.rota_detay and route_dict.get("route_analysis"):
                t.rota_detay = {"route_analysis": route_dict["route_analysis"]}
                needs_update = True

            # 2. Otoban / Sehir Ici (From Route Analysis or direct columns if they exist in Lokasyon)
            # models.py for Lokasyon has 'otoban_mesafe_km' etc.

            if route_dict.get("otoban_mesafe_km"):
                if not t.otoban_mesafe_km or t.otoban_mesafe_km == 0:
                    t.otoban_mesafe_km = route_dict.get("otoban_mesafe_km")
                    needs_update = True

            if route_dict.get("sehir_ici_mesafe_km"):
                if not t.sehir_ici_mesafe_km or t.sehir_ici_mesafe_km == 0:
                    t.sehir_ici_mesafe_km = route_dict.get("sehir_ici_mesafe_km")
                    needs_update = True

            # Also calculate from analysis if columns are empty
            if (
                not t.otoban_mesafe_km
                and t.rota_detay
                and "route_analysis" in t.rota_detay
            ):
                analysis = t.rota_detay["route_analysis"]
                if "highway" in analysis:
                    # Sum values in highway dict
                    hwy_vals = analysis["highway"]
                    total_hwy = sum(float(v) for v in hwy_vals.values())
                    t.otoban_mesafe_km = total_hwy
                    needs_update = True

            if needs_update:
                print(
                    f"Trip {t.id}: Updated route details (Highway: {t.otoban_mesafe_km} km)"
                )
                updated_count += 1

        if updated_count > 0:
            await uow.commit()
            print(f"Successfully updated {updated_count} trips.")
        else:
            print("No trips needed updates.")


if __name__ == "__main__":
    asyncio.run(fix_route_details())
