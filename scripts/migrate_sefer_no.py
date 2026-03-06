import asyncio
import os
import sys
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal


async def migrate_sefer_no():
    async with AsyncSessionLocal() as db:
        print("\n--- DATABASE MIGRATION: Adding sefer_no to seferler ---")
        try:
            # Check if column exists (SQLite specific check or generic catch)
            # We'll just try to add it and catch error if it exists
            await db.execute(
                text("ALTER TABLE seferler ADD COLUMN sefer_no VARCHAR(50)")
            )
            await db.execute(
                text(
                    "CREATE UNIQUE INDEX idx_sefer_no ON seferler(sefer_no) WHERE sefer_no IS NOT NULL"
                )
            )
            await db.commit()
            print("Successfully added sefer_no column and index.")
        except Exception as e:
            if (
                "duplicate column name" in str(e).lower()
                or "already exists" in str(e).lower()
            ):
                print("Column already exists, skipping.")
            else:
                print(f"Error during migration: {e}")
                await db.rollback()


if __name__ == "__main__":
    asyncio.run(migrate_sefer_no())
