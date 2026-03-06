import sys
import os
import asyncio
from datetime import datetime

sys.path.append(os.getcwd())

# Ensure env is loaded
from dotenv import load_dotenv

load_dotenv()

from app.core.services.sefer_service import SeferService
from app.schemas.sefer import SeferCreate
from app.database.connection import get_sync_session


async def verify_add_trip():
    print("Testing Add Trip Integration (with RouteValidator)...")

    # Instantiate service (it handles its own repo/uow usually, or uses global)
    # But SeferService.add_sefer is async.
    service = SeferService()

    # Create input data
    # Using a known valid route: Gebze (40.80, 29.43) -> Dilovasi (40.78, 29.53) ~10-15km
    sefer_in = SeferCreate(
        arac_id=1,
        sofor_id=1,
        cikis_yeri="Gebze Integration Test",
        varis_yeri="Dilovasi Integration Test",
        cikis_lat=40.80277,
        cikis_lon=29.43056,
        varis_lat=40.78583,
        varis_lon=29.53722,
        yuk_miktari=10,
        yuk_birimi="ton",
        sefer_tarihi=datetime.now(),
        notlar="Integration Test Run",
    )

    try:
        print("Calling add_sefer...")
        # Note: add_sefer returns 'id' (int) or raises exception
        sefer_id = await service.add_sefer(sefer_in)
        print(f"Sefer Created Successfully! ID: {sefer_id}")

        # Verify saved data
        from app.database.models import Sefer, Lokasyon
        from sqlalchemy import text

        with get_sync_session() as session:
            sefer = session.execute(
                text("SELECT * FROM seferler WHERE id = :id"), {"id": sefer_id}
            ).fetchone()

            if sefer:
                lokasyon_id = sefer.guzergah_id
                print(f"Associated Route ID: {lokasyon_id}")

                lokasyon = session.execute(
                    text("SELECT * FROM lokasyonlar WHERE id = :id"),
                    {"id": lokasyon_id},
                ).fetchone()

                if lokasyon:
                    print(f"Route Data: {lokasyon.cikis_yeri} -> {lokasyon.varis_yeri}")
                    print(f"Distance: {lokasyon.api_mesafe_km} km")
                    print(f"Ascent: {lokasyon.ascent_m} m")
                    # Check if ascent is sane (Gebze-Dilovası is hilly but short)
                    # 15km, maybe 100-200m ascent?
                    # If RouteValidator kicked in (unlikely here), it would be < 1.5% grade.
                    pass
                else:
                    print("Error: Route not found!")
            else:
                print("Error: Trip not found!")

    except Exception as e:
        print(f"Sefer Creation Failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_add_trip())
