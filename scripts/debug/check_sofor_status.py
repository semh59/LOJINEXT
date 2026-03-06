import asyncio
from sqlalchemy import text
from app.database.connection import engine


async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, ad_soyad, aktif FROM soforler"))
        rows = result.fetchall()
        print(f"TOTAL SOFORLER found: {len(rows)}")
        for r in rows:
            print(f" - ID {r[0]}: {r[1]} (Active: {r[2]})")


if __name__ == "__main__":
    asyncio.run(check())
