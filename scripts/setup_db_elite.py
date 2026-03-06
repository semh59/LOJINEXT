import asyncio
import sys
import os

# Project Root
sys.path.append(os.getcwd())

from app.database.connection import engine
from app.database.models import Base
from app.infrastructure.logging.logger import setup_logging

logger = setup_logging("db_setup")


async def setup_db():
    logger.info("Starting Elite Database Schema Setup...")
    async with engine.begin() as conn:
        # This will create all tables defined in models.py that don't exist
        # It's safer than raw SQL as it uses the SQLAlchemy definitions
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema setup complete.")


if __name__ == "__main__":
    asyncio.run(setup_db())
