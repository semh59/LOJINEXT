
import asyncio
import sys
from pathlib import Path
from sqlalchemy import select

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent))

from app.database.connection import AsyncSessionLocal
from app.database.models import Arac

async def fetch_vehicles():
    print("Connecting to DB...")
    async with AsyncSessionLocal() as session:
        print("Executing SELECT * FROM araclar...")
        try:
            stmt = select(Arac)
            result = await session.execute(stmt)
            vehicles = result.scalars().all()
            print(f"Found {len(vehicles)} vehicles.")
            
            print("Accessing fields to trigger deferred loading/errors...")
            from app.schemas.arac import AracResponse
            
            for v in vehicles:
                print(f"ID: {v.id}, Plaka: {v.plaka}")
                try:
                    # Simulate Pydantic serialization
                    pydantic_obj = AracResponse.model_validate(v)
                    print(f"   [OK] Validated: {pydantic_obj.plaka}")
                except Exception as ve:
                    print(f"   [FAIL] Validation Error for ID {v.id}: {ve}")
                    raise ve
                
        except Exception as e:
            print("\nCRITICAL FAILURE!")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(fetch_vehicles())
