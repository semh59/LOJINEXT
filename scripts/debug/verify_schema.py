import asyncio
import sys
import os
from sqlalchemy import text

# Add root to python path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        try:
            # Check if cikis_lat column exists in guzergahlar table
            # Need to use 'guzergahlar' (table name is plural in models.py)
            result = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='guzergahlar' AND column_name='cikis_lat'"))
            row = result.fetchone()
            if row:
                print("SCHEMA_VERIFIED: cikis_lat exists")
            else:
                # Fallback check for case sensitivity
                print("Checking manually via SELECT...")
                try:
                    await session.execute(text("SELECT cikis_lat FROM guzergahlar LIMIT 1"))
                    print("SCHEMA_VERIFIED: SELECT succeeded")
                except Exception as e:
                     print(f"SCHEMA_MISSING: {e}")

        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        # Removed set_event_loop_policy as it might cause issues if not needed or platform specific handling is better
        # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        pass
    asyncio.run(main())
