import asyncio
from sqlalchemy import update
from app.database.connection import AsyncSessionLocal
from app.database.models import Sefer


async def prepare_test_data_full():
    async with AsyncSessionLocal() as session:
        # Mark all trips as real
        update_stmt = update(Sefer).values(is_real=True)
        await session.execute(update_stmt)
        await session.commit()
        print("Successfully marked all trips as is_real=True for testing.")


if __name__ == "__main__":
    asyncio.run(prepare_test_data_full())
