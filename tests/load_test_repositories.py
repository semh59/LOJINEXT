
"""
Repository Layer Load Test
Verifies thread-safety of singletons and LoginAttemptTracker under high concurrency.
"""
import asyncio
import threading
import time
import pytest
from app.database.repositories.arac_repo import get_arac_repo
from app.database.repositories.kullanici_repo import get_login_tracker, get_kullanici_repo
from app.database.repositories.sefer_repo import get_sefer_repo

async def test_singleton_concurrency_load():
    """Simulate 1000 concurrent requests to repository singletons."""
    print("\n[LOAD TEST] Starting Singleton Concurrency Load Test (1000 requests)")
    
    repo_getters = [get_arac_repo, get_kullanici_repo, get_sefer_repo]
    all_instances = {getter: [] for getter in repo_getters}
    
    def worker(getter, list_to_append):
        # Heavy hitting the singleton getter
        for _ in range(100):
            list_to_append.append(getter())

    threads = []
    for getter in repo_getters:
        for _ in range(10): # 10 threads per repo
            t = threading.Thread(target=worker, args=(getter, all_instances[getter]))
            threads.append(t)
            t.start()

    for t in threads:
        t.join()

    print("[LOAD TEST] Verifying singleton integrity...")
    for getter, instances in all_instances.items():
        # Check if all instances are the same object
        first_instance = instances[0]
        assert all(inst is first_instance for inst in instances), f"Thread-safety failure in {getter.__name__}: Multiple instances created"
        print(f"  ✅ {getter.__name__}: Thread-safe (1000/1000 matched)")

async def test_login_tracker_load():
    """Simulate heavy load on LoginAttemptTracker."""
    print("\n[LOAD TEST] Starting LoginAttemptTracker Load Test (5000 records)")
    tracker = get_login_tracker()
    
    def worker():
        for i in range(500):
            tracker.record_attempt(f"user_{i % 10}", False)

    start_time = time.time()
    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    duration = time.time() - start_time
    print(f"  ✅ LoginAttemptTracker: 5000 records in {duration:.4f}s")
    for i in range(10):
        assert tracker.is_locked(f"user_{i}"), f"user_{i} should be locked"

if __name__ == "__main__":
    asyncio.run(test_singleton_concurrency_load())
    asyncio.run(test_login_tracker_load())
