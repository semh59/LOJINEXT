import asyncio
from sqlalchemy import text
from app.database.connection import engine


async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT * FROM soforler WHERE id = 64"))
        row = result.mappings().one_or_none()
        print(dict(row) if row else "Not found")


if __name__ == "__main__":
    asyncio.run(check())
