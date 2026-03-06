import asyncio
import os
import sys
from sqlalchemy import update, select
from app.database.connection import AsyncSessionLocal
from app.database.models import Sefer


async def prepare_test_data():
    async with AsyncSessionLocal() as session:
        # Get 40 enriched trips
        stmt = select(Sefer.id).where(Sefer.rota_detay != None).limit(40)
        result = await session.execute(stmt)
        ids = result.scalars().all()

        if not ids:
            print("No enriched trips found!")
            return

        # Mark as real
        update_stmt = update(Sefer).where(Sefer.id.in_(ids)).values(is_real=True)
        await session.execute(update_stmt)
        await session.commit()
        print(f"Successfully marked {len(ids)} trips as is_real=True for testing.")


if __name__ == "__main__":
    asyncio.run(prepare_test_data())
