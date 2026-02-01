
import asyncio
import sys
from pathlib import Path
from sqlalchemy import text, delete
from app.database.connection import AsyncSessionLocal
from app.database.models import Arac

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent))

async def clean_data():
    print("Connecting to DB...")
    async with AsyncSessionLocal() as session:
        print("Cleaning invalid vehicles...")
        
        # Delete ID 1 and 2 (known invalid 'TEST' plates that violate regex)
        stmt = delete(Arac).where(Arac.plaka.like('%TEST%'))
        result = await session.execute(stmt)
        print(f"Deleted {result.rowcount} invalid vehicles.")
        
        await session.commit()
        print("Done.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(clean_data())
