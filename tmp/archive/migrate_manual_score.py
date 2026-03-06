import asyncio
import os
import sys
from sqlalchemy import text

sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal

async def migrate():
    print("Starting database migration: Adding manual_score to soforler")
    async with AsyncSessionLocal() as session:
        try:
            # Check if column exists first
            check_query = text("SELECT column_name FROM information_schema.columns WHERE table_name='soforler' AND column_name='manual_score'")
            result = await session.execute(check_query)
            if result.scalar():
                print("Column 'manual_score' already exists.")
            else:
                print("Adding column 'manual_score'...")
                await session.execute(text("ALTER TABLE soforler ADD COLUMN manual_score FLOAT DEFAULT 1.0"))
                await session.commit()
                print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(migrate())
