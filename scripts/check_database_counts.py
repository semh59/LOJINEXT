import asyncio
from sqlalchemy import text
from app.database.connection import engine


async def check_counts():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT COUNT(*) FROM seferler"))
        total = res.scalar()
        print(f"REAL TOTAL TRIPS: {total}")

        res = await conn.execute(
            text("SELECT COUNT(*) FROM seferler WHERE (tuketim IS NULL OR tuketim > 0)")
        )
        filtered = res.scalar()
        print(f"FILTERED TRIPS (tuketim IS NULL OR > 0): {filtered}")

        res = await conn.execute(
            text("SELECT COUNT(*) FROM seferler WHERE tuketim = 0")
        )
        zero_fuel = res.scalar()
        print(f"TRIPS WITH 0 FUEL: {zero_fuel}")


if __name__ == "__main__":
    asyncio.run(check_counts())
