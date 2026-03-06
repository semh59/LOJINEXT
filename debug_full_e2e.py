import asyncio
import sys
import os
import json
from datetime import date, datetime

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.api.deps import get_dorse_service
from app.database.unit_of_work import UnitOfWork
from app.schemas.dorse import DorseResponse
from app.schemas.base import StandardResponse


async def run_diagnostic():
    print("--- Starting Full E2E Serialization Diagnostic ---")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        uow = UnitOfWork(session)
        service = await get_dorse_service(uow)

        print("1. Creating a diagnostic trailer...")
        test_data = {
            "plaka": "34 E2E 001",
            "marka": "E2E Brand",
            "tipi": "Standart",
            "yil": 2024,
            "bos_agirlik_kg": 6000.0,
            "maks_yuk_kapasitesi_kg": 24000,
            "lastik_sayisi": 6,
        }

        async with uow:
            dorse_id = await service.create(**test_data)
            await uow.commit()  # Commit this time!
            print(f"Created and committed trailer ID {dorse_id}")

        uow_read = UnitOfWork(session)  # New UoW instance for reading
        service_read = await get_dorse_service(uow_read)

        print("2. Fetching paged data...")
        data = await service_read.get_all_paged()
        print(f"Service returned {len(data)} items")
        for item in data:
            print(f"  - Item: {item['plaka']} (ID: {item['id']})")

        print("3. Validating through DorseResponse...")
        try:
            validated = [DorseResponse.model_validate(item) for item in data]
            print(f"Successfully validated {len(validated)} response objects")
        except Exception as e:
            print(f"VALIDATION FAILURE: {e}")
            import traceback

            traceback.print_exc()
            return

        print("4. Final StandardResponse dump check...")
        try:
            resp = StandardResponse(data=validated)
            json_out = resp.model_dump_json()
            print(
                f"SUCCESS: Endpoint response is serializable. Length: {len(json_out)}"
            )
        except Exception as e:
            print(f"SERIALIZATION FAILURE: {e}")
            import traceback

            traceback.print_exc()

    print("--- Diagnostic Complete ---")


if __name__ == "__main__":
    asyncio.run(run_diagnostic())
