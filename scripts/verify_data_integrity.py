import asyncio
import sys
import os
from sqlalchemy import text

sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal


async def verify_integrity():
    print("🛡️ Starting Data Integrity Audit...")

    async with AsyncSessionLocal() as session:
        # 1. Check for Duplicate Sefer (Same Vehicle, Same Time)
        print("\n🔍 Checking for Duplicate Trips...")
        query_dupe_trips = """
        SELECT arac_id, tarih, saat, COUNT(*) 
        FROM seferler 
        GROUP BY arac_id, tarih, saat 
        HAVING COUNT(*) > 1
        """
        result = await session.execute(text(query_dupe_trips))
        dupes = result.fetchall()
        if dupes:
            print(f"❌ Found {len(dupes)} duplicate trip groups!")
            for d in dupes[:5]:
                print(f"   - Vehicle {d[0]} at {d[1]} {d[2]}: {d[3]} records")
        else:
            print("✅ No duplicate trips found.")

        # 2. Check for Orphaned Trips (Invalid Vehicle ID)
        print("\n🔍 Checking for Orphaned Trips (Invalid Vehicle)...")
        query_orphans = """
        SELECT count(*) FROM seferler s 
        LEFT JOIN araclar a ON s.arac_id = a.id 
        WHERE a.id IS NULL
        """
        result = await session.execute(text(query_orphans))
        orphans = result.scalar()
        if orphans > 0:
            print(f"❌ Found {orphans} orphaned trips!")
        else:
            print("✅ No orphaned trips found.")

        # 3. Check for NULL Critical Fields
        print("\n🔍 Checking for Data completeness...")
        query_nulls = """
        SELECT count(*) FROM seferler 
        WHERE tuketim IS NULL OR mesafe_km IS NULL OR ton IS NULL
        """
        result = await session.execute(text(query_nulls))
        nulls = result.scalar()
        if nulls > 0:
            print(f"⚠️ Found {nulls} trips with NULL critical data.")
        else:
            print("✅ All trips have critical data.")

        # 4. Check Ascent/Descent Coverage
        print("\n🔍 Checking Elevation Data Coverage...")
        query_elevation = """
        SELECT 
            count(*) as total,
            sum(case when s.ascent_m IS NULL AND l.ascent_m IS NULL then 1 else 0 end) as missing
        FROM seferler s
        LEFT JOIN lokasyonlar l ON (s.cikis_yeri = l.cikis_yeri AND s.varis_yeri = l.varis_yeri)
        """
        result = await session.execute(text(query_elevation))
        row = result.fetchone()
        if row:
            total, missing = row
            print(
                f"📊 Elevation Coverage: {total - missing}/{total} ({(total - missing) / total * 100:.1f}%)"
            )
            if missing > 0:
                print(f"⚠️ {missing} trips still missing elevation data.")

        # 5. Check Sequence Gaps (Vehicle KM Counter)
        # TODO: This requires ordering by date and checking km_sayac continuity.

    print("\n🏁 Audit Complete.")


if __name__ == "__main__":
    asyncio.run(verify_integrity())
