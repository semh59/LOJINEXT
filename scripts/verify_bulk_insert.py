"""
Bulk Insert Verification Script.

Repository bulk insert işlemlerini doğrular.
"""

import asyncio
import sys
from datetime import date
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.infrastructure.verification.verify_utils import VerificationRunner
from app.database.connection import AsyncSessionLocal
from app.database.repositories.yakit_repo import get_yakit_repo
from app.database.models import YakitPeriyodu


async def verify_bulk_insert(runner: VerificationRunner):
    """Bulk insert işlemini test eder."""
    import time
    
    if not runner.should_run_check("bulk"):
        runner.add_skipped("Bulk Insert", "Not selected")
        return
    
    # Dry-run modunda gerçek DB işlemi yapma
    if runner.is_dry_run:
        runner.add_result(
            "Bulk Insert",
            True,
            "DRY-RUN: Bulk insert operation simulated (no DB changes)",
            {"dry_run": True, "simulated_count": 10}
        )
        return
    
    start = time.time()
    
    try:
        async with AsyncSessionLocal() as session:
            repo = get_yakit_repo(session=session)
            
            # Mevcut bir arac_id bul - FK constraint için gerekli
            from sqlalchemy import text
            result = await session.execute(text("SELECT id FROM araclar LIMIT 1"))
            row = result.scalar_one_or_none()
            if not row:
                runner.add_result(
                    "Bulk Insert",
                    False,
                    "No vehicles in database for testing. Insert a vehicle first.",
                    {"error": "no_test_data"}
                )
                return
            arac_id = row
            
            # Fake data generator - 10 kayıt
            periods = []
            for i in range(10): 
                p = YakitPeriyodu(
                    arac_id=arac_id,
                    alim1_id=None, 
                    alim2_id=None,
                    alim1_tarih=date.today(), 
                    alim2_tarih=date.today(),
                    alim1_km=1000 + i * 100, 
                    alim2_km=1200 + i * 100,
                    alim1_litre=50.0, 
                    ara_mesafe=200, 
                    toplam_yakit=50.0,
                    ort_tuketim=25.0, 
                    durum='Tamam'
                )
                periods.append(p)
            
            if runner.args.verbose and not runner.args.json:
                print(f"   📊 Prepared {len(periods)} periods for bulk insert...")
            
            # Execute save
            count = await repo.save_fuel_periods(periods, clear_existing=False)
            
            if count != 10:
                runner.add_result(
                    "Bulk Insert",
                    False,
                    f"Count mismatch: expected 10, got {count}",
                    duration=time.time() - start
                )
                await session.rollback()
                return
            
            # Rollback to clean up - TEST ENVIRONMENT
            await session.rollback()
            
            runner.add_result(
                "Bulk Insert",
                True,
                f"Successfully saved {count} periods (rolled back)",
                {"count": count, "rolled_back": True},
                duration=time.time() - start
            )
            
    except Exception as e:
        runner.add_result(
            "Bulk Insert",
            False,
            f"Failed: {str(e)}",
            duration=time.time() - start
        )


async def main():
    runner = VerificationRunner(
        "Bulk Insert Verification",
        "Validates repository bulk insert operations"
    )
    
    runner.register_check("bulk")
    
    await verify_bulk_insert(runner)
    
    runner.finalize()


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
