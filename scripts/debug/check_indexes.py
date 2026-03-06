import asyncio
from sqlalchemy import text
from app.database.connection import AsyncSessionLocal

async def check_indexes():
    async with AsyncSessionLocal() as session:
        query = text("SELECT indexname FROM pg_indexes WHERE tablename IN ('seferler', 'araclar', 'soforler')")
        res = await session.execute(query)
        print([r[0] for r in res])

if __name__ == "__main__":
    asyncio.run(check_indexes())
