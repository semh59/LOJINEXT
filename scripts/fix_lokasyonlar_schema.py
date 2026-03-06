import asyncio
import os
from sqlalchemy import text
from app.database.connection import engine


async def migrate_lokasyonlar():
    print("Migrating 'lokasyonlar' table to add missing columns...")

    queries = [
        "ALTER TABLE lokasyonlar ADD COLUMN IF NOT EXISTS otoban_mesafe_km DOUBLE PRECISION DEFAULT 0.0;",
        "ALTER TABLE lokasyonlar ADD COLUMN IF NOT EXISTS sehir_ici_mesafe_km DOUBLE PRECISION DEFAULT 0.0;",
        "ALTER TABLE lokasyonlar ADD COLUMN IF NOT EXISTS aktif BOOLEAN DEFAULT TRUE;",
    ]

    try:
        async with engine.begin() as conn:
            for query in queries:
                print(f"Executing: {query}")
                await conn.execute(text(query))
        print("Migration successful!")
    except Exception as e:
        print(f"Migration failed: {e}")


if __name__ == "__main__":
    asyncio.run(migrate_lokasyonlar())
