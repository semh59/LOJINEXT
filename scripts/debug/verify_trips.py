import asyncio
from datetime import date
from app.database.connection import AsyncSessionLocal
from app.database.repositories.sefer_repo import get_sefer_repo

async def verify_filters():
    async with AsyncSessionLocal() as session:
        repo = get_sefer_repo(session)
        
        # 1. Test Default Order (DESC)
        print("Testing Default Order...")
        trips = await repo.get_all(limit=5)
        for i in range(len(trips) - 1):
            t1 = trips[i]['tarih']
            t2 = trips[i+1]['tarih']
            if t1 < t2:
                print(f"FAIL: Order is not DESC! {t1} < {t2}")
            else:
                print(f"OK: {t1} >= {t2}")

        # 2. Test Filter by Driver (Pick first driver found)
        if trips:
            driver_id = trips[0]['sofor_id']
            print(f"Testing Filter by Driver ID {driver_id}...")
            filtered = await repo.get_all(sofor_id=driver_id, limit=5)
            for t in filtered:
                if t['sofor_id'] != driver_id:
                    print(f"FAIL: Driver ID mismatch! Expect {driver_id}, got {t['sofor_id']}")
                else:
                    print("OK: Driver match")
        
        # 3. Test Filter by Date Range (Today)
        today = date.today().isoformat()
        print(f"Testing Filter by Date {today}...")
        todays = await repo.get_all(tarih=today, limit=5)
        print(f"Found {len(todays)} trips for today.")

if __name__ == "__main__":
    asyncio.run(verify_filters())
