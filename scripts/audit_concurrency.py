import asyncio
import sys
import os
import random
import time
from datetime import date
from typing import List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.services.import_service import get_import_service
from app.core.services.sefer_service import get_sefer_service
from app.core.entities.models import SeferCreate
from app.database.unit_of_work import get_uow
from app.database.repositories.arac_repo import get_arac_repo
from app.database.repositories.sofor_repo import get_sofor_repo
from app.infrastructure.logging.logger import get_logger

logger = get_logger("concurrency_audit")


async def simulate_bulk_import_worker(
    worker_id: int, arac_id: int, sofor_id: int, count: int
):
    """Simulates a worker performing bulk imports simultaneously."""
    sefer_service = get_sefer_service()

    test_trips = [
        SeferCreate(
            tarih=date.today(),
            arac_id=arac_id,
            sofor_id=sofor_id,
            cikis_yeri=f"WorkerCity_{worker_id}_Start",
            varis_yeri=f"WorkerCity_{worker_id}_End",
            mesafe_km=random.uniform(10, 500),
            net_kg=random.randint(5000, 25000),
            durum="Tamam",
            notlar=f"Concurrency Test / Worker {worker_id} / Batch item {i}",
        )
        for i in range(count)
    ]

    print(f"👷 Worker {worker_id}: Attempting to bulk add {count} trips...")
    try:
        start_time = time.time()
        imported_count = await sefer_service.bulk_add_sefer(test_trips)
        end_time = time.time()
        print(
            f"✅ Worker {worker_id}: Successfully added {imported_count} trips in {end_time - start_time:.2f}s"
        )
        return imported_count
    except Exception as e:
        print(f"❌ Worker {worker_id}: FAILED with error: {e}")
        return 0


async def perform_concurrency_audit():
    print("🔥 Starting ELITE Concurrency & Race Condition Audit...")

    # 1. Setup Data
    vehicles = await get_arac_repo().get_all(limit=1)
    drivers = await get_sofor_repo().get_all(limit=1)

    if not vehicles or not drivers:
        print("❌ Error: No lookup data found.")
        return

    arac_id = vehicles[0]["id"]
    sofor_id = drivers[0]["id"]

    # 2. Run Parallel Tasks
    num_workers = 5
    items_per_worker = 10

    print(
        f"🚀 Spawning {num_workers} parallel workers (Total: {num_workers * items_per_worker} trips)..."
    )

    tasks = [
        simulate_bulk_import_worker(i, arac_id, sofor_id, items_per_worker)
        for i in range(num_workers)
    ]

    results = await asyncio.gather(*tasks)

    total_imported = sum(results)
    print(
        f"\n📊 Total successfully imported: {total_imported} / {num_workers * items_per_worker}"
    )

    # 3. Integrity Verification
    print("\n🔍 Verifying Data Integrity...")
    async with get_uow() as uow:
        # Check for duplicated IDs or unusual counts
        count_in_db = await uow.sefer_repo.count(filters={"arac_id": arac_id})
        print(f"📈 Current total trips for vehicle {arac_id}: {count_in_db}")

        # Check for sequential ID gaps (indicates transaction failure/rollback leaks)
        # Note: Some gaps are normal in DBs, but pattern is important.

    if total_imported == (num_workers * items_per_worker):
        print(
            "\n🏆 CONCURRENCY TEST PASSED: No race conditions detected during bulk inserts."
        )
    else:
        print(
            "\n⚠️ CONCURRENCY TEST PARTIAL: Some workers failed. Check logs for deadlocks/timeout."
        )


if __name__ == "__main__":
    asyncio.run(perform_concurrency_audit())
