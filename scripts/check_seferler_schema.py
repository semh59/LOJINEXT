import asyncio
import os
import sys
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal


async def check_schema():
    async with AsyncSessionLocal() as db:
        print("\n--- CHECKING SCHEMA: seferler ---")
        try:
            # PRAGMA is SQLite specific
            result = await db.execute(text("PRAGMA table_info(seferler)"))
            columns = result.fetchall()
            for col in columns:
                print(f"Column: {col[1]} | Type: {col[2]}")
        except Exception as e:
            print(f"Error checking schema: {e}")


if __name__ == "__main__":
    asyncio.run(check_schema())
