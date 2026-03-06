import asyncio
from app.database.connection import AsyncSessionLocal
from sqlalchemy import text


async def debug_fuel():
    async with AsyncSessionLocal() as session:
        # Check counts
        fuel_count = (
            await session.execute(text("SELECT COUNT(*) FROM yakit_alimlari"))
        ).scalar()
        arac_count = (
            await session.execute(text("SELECT COUNT(*) FROM araclar"))
        ).scalar()
        print(f"Total Fuel Records: {fuel_count}")
        print(f"Total Vehicles: {arac_count}")

        # Check active status breakdown
        active_res = await session.execute(
            text("SELECT aktif, COUNT(*) FROM yakit_alimlari GROUP BY aktif")
        )
        for active, count in active_res:
            print(f"Status Active={active}: {count}")

        # Check date range
        date_res = await session.execute(
            text("SELECT MIN(tarih), MAX(tarih) FROM yakit_alimlari")
        )
        min_date, max_date = date_res.fetchone()
        print(f"Date Range: {min_date} to {max_date}")

        # Check orphan records (arac_id not in araclar)
        orphan_res = await session.execute(
            text(
                "SELECT COUNT(*) FROM yakit_alimlari ya LEFT JOIN araclar a ON ya.arac_id = a.id WHERE a.id IS NULL"
            )
        )
        print(f"Orphan Fuel Records (No matching vehicle): {orphan_res.scalar()}")

        # Check sample records
        sample_res = await session.execute(
            text(
                "SELECT ya.*, a.plaka FROM yakit_alimlari ya JOIN araclar a ON ya.arac_id = a.id LIMIT 3"
            )
        )
        print("\nSample Records (Joined):")
        for row in sample_res.mappings():
            print(dict(row))


if __name__ == "__main__":
    asyncio.run(debug_fuel())
