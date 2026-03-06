import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from datetime import date
from app.core.services.sefer_service import get_sefer_service
from app.schemas.sefer import SeferCreate
from app.database.unit_of_work import get_uow


async def verify():
    print("Testing Fuel Prediction Saving...")
    service = get_sefer_service()

    # Create a test Sefer
    test_data = SeferCreate(
        tarih=date.today(),
        saat="10:00",
        arac_id=857,  # Valid Arac ID
        sofor_id=93,  # Valid Sofor ID
        cikis_yeri="İstanbul",
        varis_yeri="Ankara",
        mesafe_km=450.0,
        net_kg=20000,
        ton=20.0,
        ascent_m=500.0,
        descent_m=300.0,
        flat_distance_km=400.0,
    )

    try:
        sefer_id = await service.add_sefer(test_data)
        print(f"Created Sefer ID: {sefer_id}")

        # Now read it back
        sefer = await service.get_by_id(sefer_id)
        if sefer:
            print(f"Retrieved Sefer ID: {sefer.id}")
            print(f"Tahmini Tüketim: {sefer.tahmini_tuketim}")

            if sefer.tahmini_tuketim is not None:
                print("SUCCESS: Fuel prediction was calculated and saved!")
            else:
                print(
                    "FAILURE: Fuel prediction is None. Check if model is trained for vehicle 1."
                )
        else:
            print("FAILURE: Could not retrieve sefer.")

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(verify())
