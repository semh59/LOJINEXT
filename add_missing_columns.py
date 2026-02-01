
import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent))

from app.database.connection import AsyncSessionLocal

async def add_columns():
    print("Connecting to DB...")
    async with AsyncSessionLocal() as session:
        print("Checking/Adding missing columns to 'araclar'...")
        
        # We use raw SQL ALTER TABLE for simplicity in this hotfix.
        # Ideally use Alembic.
        
        commands = [
            "ALTER TABLE araclar ADD COLUMN IF NOT EXISTS on_kesit_alani_m2 FLOAT DEFAULT 8.5;",
            "ALTER TABLE araclar ADD COLUMN IF NOT EXISTS hava_direnc_katsayisi FLOAT DEFAULT 0.7;",
            "ALTER TABLE araclar ADD COLUMN IF NOT EXISTS bos_agirlik_kg FLOAT DEFAULT 8000.0;",
            "ALTER TABLE araclar ADD COLUMN IF NOT EXISTS motor_verimliligi FLOAT DEFAULT 0.38;",
            "ALTER TABLE araclar ADD COLUMN IF NOT EXISTS lastik_direnc_katsayisi FLOAT DEFAULT 0.007;",
            "ALTER TABLE araclar ADD COLUMN IF NOT EXISTS maks_yuk_kapasitesi_kg INTEGER DEFAULT 26000;"
        ]
        
        for cmd in commands:
            try:
                print(f"Executing: {cmd}")
                await session.execute(text(cmd))
            except Exception as e:
                print(f"Error executing {cmd}: {e}")
        
        await session.commit()
        print("Done. Columns ensured.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(add_columns())
