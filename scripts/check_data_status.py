import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database.models import Sefer


async def check_data_status():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Toplam sefer
        total_q = await session.execute(select(func.count(Sefer.id)))
        total = total_q.scalar()

        # tuketim (Gerçek) dolu olanlar
        real_q = await session.execute(
            select(func.count(Sefer.id)).where(Sefer.tuketim != None)
        )
        real = real_q.scalar()

        # tahmini_tuketim dolu olanlar
        pred_q = await session.execute(
            select(func.count(Sefer.id)).where(Sefer.tahmini_tuketim != None)
        )
        pred = pred_q.scalar()

        # İkisi de dolu olanlar
        both_q = await session.execute(
            select(func.count(Sefer.id)).where(
                Sefer.tuketim != None, Sefer.tahmini_tuketim != None
            )
        )
        both = both_q.scalar()

        print(f"TOTAL_TRIPS: {total}")
        print(f"REAL_TUKETIM_FILLED: {real}")
        print(f"PRED_TUKETIM_FILLED: {pred}")
        print(f"BOTH_FILLED: {both}")


if __name__ == "__main__":
    asyncio.run(check_data_status())
