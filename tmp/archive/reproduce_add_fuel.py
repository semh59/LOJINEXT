import asyncio
import os
import sys
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())

from app.core.services.yakit_service import get_yakit_service
from app.core.entities.models import YakitAlimiCreate
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


async def reproduce_add():
    service = get_yakit_service()

    # Needs a valid arac_id. repro_output said 851 is active.
    # If 851 doesn't exist in my local DB, I might need to find one.
    # I'll rely on the fact that I'm in the same environment or I'll query for one.
    from app.database.unit_of_work import get_uow

    arac_id = 1

    async with get_uow() as uow:
        # Get first active vehicle
        araclar = await uow.arac_repo.get_all(sadece_aktif=True)
        if araclar:
            arac_id = araclar[0]["id"]
            print(f"Using vehicle ID: {arac_id}")
        else:
            print("No active vehicle found. Cannot reproduce.")
            return

    try:
        print(f"Attempting to add fuel for vehicle {arac_id}...")

        # Valid data
        data = YakitAlimiCreate(
            tarih=date.today(),
            arac_id=arac_id,
            istasyon="Test Station",
            fiyat_tl=40.0,
            litre=10.0,
            km_sayac=500000,  # Assuming this is > last_km
            fis_no="TEST-001",
            depo_durumu="Full",
        )

        # This triggers _check_outlier -> get_bulk_driver_metrics
        result = await service.add_yakit(data)
        print(f"Success! Fuel ID: {result}")

    except Exception as e:
        print(f"FAILED with error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(reproduce_add())
