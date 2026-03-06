import asyncio
import os
import sys
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal


async def check_schema():
    async with AsyncSessionLocal() as db:
        print("\n--- CHECKING SCHEMA (Postgres): seferler ---")
        try:
            query = """
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'seferler'
            """
            result = await db.execute(text(query))
            columns = result.fetchall()
            for col in columns:
                print(f"Column: {col[0]} | Type: {col[1]} | Length: {col[2]}")
        except Exception as e:
            print(f"Error checking schema: {e}")


if __name__ == "__main__":
    asyncio.run(check_schema())
