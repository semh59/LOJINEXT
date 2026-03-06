import sys
import os
import asyncio
import json

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.database.unit_of_work import UnitOfWork
from app.database.models import Sefer
from app.schemas.sefer import SeferResponse


async def check_api():
    print("--- CHECKING API RESPONSE SERIALIZATION ---")

    async with UnitOfWork() as uow:
        # Manual Service Call Simulation
        print("Querying Repo...")
        records = await uow.sefer_repo.get_all(limit=1)

        if not records:
            print("No records found in DB.")
            return

        raw_record = records[0]
        # Convert Row to dict if needed (get_all returns dicts usually but let's see)
        if not isinstance(raw_record, dict):
            raw_record = dict(raw_record)

        print(f"1. Raw Repo Record Keys: {list(raw_record.keys())}")

        if "otoban_mesafe_km" in raw_record:
            print(f"   -> otoban_mesafe_km VALUE: {raw_record['otoban_mesafe_km']}")
        else:
            print("   -> CRITICAL: otoban_mesafe_km MISSING in Repo Result!")

        # Validate with Schema (mimic Service Logic + API Response)
        try:
            # Service Logic: Sefer.model_validate(dict(r))
            sefer_obj = Sefer.model_validate(raw_record)
            print(
                f"2. Sefer Model Object otoban_mesafe_km: {sefer_obj.otoban_mesafe_km}"
            )

            # API Response Logic: SeferResponse.model_validate(sefer_obj)
            # NOTE: FastAPI uses this implicitly
            pydantic_out = SeferResponse.model_validate(sefer_obj)
            print(
                f"3. API Schema Output otoban_mesafe_km: {pydantic_out.otoban_mesafe_km}"
            )

            if pydantic_out.otoban_mesafe_km is None and raw_record.get(
                "otoban_mesafe_km"
            ):
                print("   -> FAILURE: Schema stripped the value!")
            elif pydantic_out.otoban_mesafe_km == raw_record.get("otoban_mesafe_km"):
                print("   -> SUCCESS: Value survived serialization.")

        except Exception as e:
            print(f"Validation Error: {e}")


if __name__ == "__main__":
    asyncio.run(check_api())
