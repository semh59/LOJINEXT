
import asyncio
import os
from datetime import date
from decimal import Decimal
from sqlalchemy import insert, text
from sqlalchemy.ext.asyncio import create_async_engine

# Set env
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

async def debug():
    from app.database.models import Base, YakitAlimi
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    print("Schema created.")
    
    async with engine.connect() as conn:
        # Check columns
        res = await conn.execute(text("PRAGMA table_info(yakit_alimlari)"))
        cols = [r[1] for r in res.fetchall()]
        print(f"Columns in yakit_alimlari: {cols}")
        
        # Try insert
        try:
            data = {
                "tarih": date.today(),
                "arac_id": 1,
                "istasyon": "Test",
                "fiyat_tl": Decimal("40"),
                "litre": Decimal("500"),
                "km_sayac": 100000,
                "aktif": True
            }
            stmt = insert(YakitAlimi).values(**data)
            await conn.execute(stmt)
            print("Insert worked!")
        except Exception as e:
            print(f"Insert failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug())
