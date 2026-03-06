import asyncio
import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.unit_of_work import get_uow


async def perform_performance_audit():
    print("📊 Starting ELITE Database & Query Performance Audit...")

    queries_to_test = [
        ("Dashboard Stats", "SELECT count(*) FROM seferler WHERE durum = 'Tamam'"),
        (
            "Recent Trips with Joins",
            """
            SELECT s.*, a.plaka, sf.ad_soyad 
            FROM seferler s 
            JOIN araclar a ON s.arac_id = a.id 
            JOIN soforler sf ON s.sofor_id = sf.id 
            ORDER BY s.tarih DESC LIMIT 100
        """,
        ),
        (
            "Fuel Consumption Aggregation",
            """
            SELECT arac_id, SUM(miktar) as toplam_yakit 
            FROM yakit_alimlari 
            GROUP BY arac_id
        """,
        ),
        (
            "Anomaly History",
            "SELECT * FROM anomaliler ORDER BY tarih_saat DESC LIMIT 50",
        ),
    ]

    async with get_uow() as uow:
        from sqlalchemy import text

        for name, query in queries_to_test:
            print(f"\n🔍 Testing: {name}")

            # 1. Measurement
            start_time = time.time()
            res = await uow.session.execute(text(query))
            res.all()
            end_time = time.time()
            duration = (end_time - start_time) * 1000

            # 2. Explain
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            explain_res = await uow.session.execute(text(explain_query))
            explain_results = explain_res.mappings().all()

            print(f"⏱️ Execution Time: {duration:.2f}ms")
            print("🗺️ Execution Plan:")
            for row in explain_results:
                print(f"   - {row.get('detail', row)}")

            if duration > 100:
                print("⚠️ WARNING: Query is slow (> 100ms). Consider indexing.")
            else:
                print("✅ Performance: Excellent.")

        await uow.commit()  # Avoid Ghost Transaction

    # 3. Check Index Coverage
    print("\n📦 Checking Index Coverage (SQLite Master)...")
    index_check_query = "SELECT name, tbl_name FROM sqlite_master WHERE type = 'index'"
    async with get_uow() as uow:
        res = await uow.session.execute(text(index_check_query))
        indices = res.mappings().all()
        for idx in indices:
            print(f"   🔹 Index: {idx['name']} on Table: {idx['tbl_name']}")
        await uow.commit()


if __name__ == "__main__":
    asyncio.run(perform_performance_audit())
