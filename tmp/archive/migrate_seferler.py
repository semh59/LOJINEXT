import asyncio
from sqlalchemy import text
from app.database.connection import AsyncSessionLocal

async def migrate():
    async with AsyncSessionLocal() as session:
        # Check if columns exist
        res = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'seferler'"))
        columns = [r[0] for r in res]
        print(f"Current columns in seferler: {columns}")
        
        if 'ascent_m' not in columns:
            print("Adding ascent_m column...")
            await session.execute(text("ALTER TABLE seferler ADD COLUMN ascent_m FLOAT DEFAULT 0.0"))
            
        if 'descent_m' not in columns:
            print("Adding descent_m column...")
            await session.execute(text("ALTER TABLE seferler ADD COLUMN descent_m FLOAT DEFAULT 0.0"))
            
        await session.commit()
        print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
