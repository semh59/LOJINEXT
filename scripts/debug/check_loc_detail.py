import asyncio
from sqlalchemy import text
from app.database.connection import engine


async def check():
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id, cikis_yeri, varis_yeri, aktif FROM lokasyonlar")
        )
        rows = result.fetchall()
        print(f"TOTAL LOKASYONLAR found: {len(rows)}")
        for r in rows:
            print(f" - {r[0]}: {r[1]} -> {r[2]} (Active: {r[3]})")


if __name__ == "__main__":
    asyncio.run(check())
