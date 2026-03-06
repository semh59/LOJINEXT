import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.core.services.weather_service import WeatherService
from app.core.services.sefer_service import SeferService
from app.database.repositories.sefer_repo import SeferRepository
from app.database.repositories.lokasyon_repo import LokasyonRepository
from app.database.models import Kullanici


async def verify_dashboard_logic():
    print("Starting Dashboard Weather Logic Verification...")

    async with AsyncSessionLocal() as db:
        try:
            # Manual Injection
            sefer_repo = SeferRepository(session=db)
            lokasyon_repo = LokasyonRepository(session=db)

            sefer_service = SeferService(repo=sefer_repo)
            weather_service = WeatherService()

            # Mock user (admin)
            admin_user = Kullanici(id=1, kullanici_adi="admin", rol="admin")

            print("Fetching active trips...")
            active_trips_yolda = await sefer_service.get_all_paged(
                current_user=admin_user, durum="Yolda", limit=10
            )
            active_trips_devam = await sefer_service.get_all_paged(
                current_user=admin_user, durum="Devam Ediyor", limit=10
            )
            all_active = active_trips_yolda + active_trips_devam

            print(f"Found {len(all_active)} active trips.")

            summary = {
                "total_active": len(all_active),
                "high_risk": 0,
                "medium_risk": 0,
                "normal": 0,
                "details": [],
            }

            if len(all_active) == 0:
                print("No active trips. Verification incomplete (but code runs).")

            # Collect Route IDs
            guzergah_ids = {t.guzergah_id for t in all_active if t.guzergah_id}
            print(f"Unique Route IDs: {guzergah_ids}")

            # Fetch Routes
            all_routes = await lokasyon_repo.get_all(limit=1000)
            routes_map = {r["id"]: r for r in all_routes if r["id"] in guzergah_ids}

            print(f"Resolved {len(routes_map)} routes.")

            for trip in all_active:
                if trip.guzergah_id and trip.guzergah_id in routes_map:
                    route = routes_map[trip.guzergah_id]
                    c_lat = route.get("cikis_lat")
                    v_lat = route.get("varis_lat")

                    print(
                        f"Trip {trip.id}: Route {trip.guzergah_id} -> {c_lat},{v_lat}"
                    )

                    if c_lat and v_lat:
                        w_res = await weather_service.get_trip_impact_analysis(
                            c_lat, route["cikis_lon"], v_lat, route["varis_lon"]
                        )
                        impact = w_res.get("fuel_impact_factor", 1.0)
                        print(f"  -> Impact: {impact}")

                        if impact > 1.10:
                            summary["high_risk"] += 1
                            summary["details"].append({"id": trip.id, "impact": impact})
                        elif impact > 1.02:
                            summary["medium_risk"] += 1
                        else:
                            summary["normal"] += 1

            print("Final Summary:", summary)

        except Exception as e:
            print(f"Verification Error: {e}")
            raise e


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_dashboard_logic())
