import asyncio
from sqlalchemy import text
from app.database.connection import AsyncSessionLocal

async def migrate():
    async with AsyncSessionLocal() as session:
        # Check if column exists
        res = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'seferler'"))
        columns = [r[0] for r in res]
        print(f"Current columns: {columns}")
        
        if 'notlar' not in columns:
            print("Adding notlar column...")
            await session.execute(text("ALTER TABLE seferler ADD COLUMN notlar VARCHAR(255)"))
        else:
            print("notlar column already exists.")

        await session.commit()
        print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
