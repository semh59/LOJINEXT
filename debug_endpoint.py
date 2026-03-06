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


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


async def run_diagnostic():
    print("--- Starting Endpoint Diagnostic ---")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        uow = UnitOfWork(session)
        service = await get_dorse_service(uow)

        print("1. Fetching data via service...")
        data = await service.get_all_paged()
        print(f"Service returned {len(data)} items")

        print("2. Attempting Pydantic validation (List[DorseResponse])...")
        try:
            validated_list = [DorseResponse.model_validate(item) for item in data]
            print(f"Validation successful for {len(validated_list)} items")
        except Exception as e:
            print(f"FAILURE in Pydantic validation: {e}")
            import traceback

            traceback.print_exc()
            return

        print("3. Attempting StandardResponse wrapping...")
        try:
            # Replicating endpoint logic
            response_obj = StandardResponse(data=validated_list)
            print("StandardResponse wrapping successful")

            print("4. Attempting JSON serialization simulation...")
            json_str = response_obj.model_dump_json()
            print(f"JSON dump successful, length: {len(json_str)}")
        except Exception as e:
            print(f"FAILURE in response wrapping/dump: {e}")
            import traceback

            traceback.print_exc()

    print("--- Diagnostic Complete ---")


if __name__ == "__main__":
    asyncio.run(run_diagnostic())
