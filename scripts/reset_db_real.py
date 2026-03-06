import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.database.connection import engine
from app.database.models import Base


async def reset_db():
    print("WARNING: This will DROP ALL TABLES in the database.")
    print("Database URL:", engine.url)

    # Safety check
    if os.getenv("ENVIRONMENT") == "prod":
        print("❌ Cannot run reset in PRODUCTION!")
        sys.exit(1)

    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    print("Recreating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database reset complete.")


if __name__ == "__main__":
    asyncio.run(reset_db())
