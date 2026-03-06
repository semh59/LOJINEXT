import asyncio
from sqlalchemy import text
from app.database.connection import AsyncSessionLocal


async def sync_distances():
    async with AsyncSessionLocal() as session:
        print("🔄 Syncing seferler.mesafe_km from lokasyonlar...")
        # Get counts for verification
        res = await session.execute(
            text("SELECT count(*) FROM seferler WHERE mesafe_km = 0")
        )
        zero_count = res.scalar()
        print(f"DEBUG: Found {zero_count} trips with 0 distance.")

        await session.execute(
            text("""
            UPDATE seferler s 
            SET mesafe_km = l.mesafe_km 
            FROM lokasyonlar l 
            WHERE s.guzergah_id = l.id
        """)
        )

        res = await session.execute(
            text("SELECT count(*) FROM seferler WHERE mesafe_km > 0")
        )
        populated_count = res.scalar()
        print(f"DEBUG: Now {populated_count} trips have valid distance.")

        await session.commit()
    print("✅ Sync complete.")


if __name__ == "__main__":
    asyncio.run(sync_distances())
