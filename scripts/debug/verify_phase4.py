import asyncio
import sys
import os
from datetime import date

# Proje kök dizinini ekle
sys.path.append(os.getcwd())

from app.services.smart_ai_service import get_smart_ai
from app.core.services.analiz_service import get_analiz_service
from app.infrastructure.cache.cache_manager import get_cache_manager
from app.core.errors import create_error_response
from app.core.entities.models import VehicleStats


async def test_ai_context():
    print("\n--- Testing AI Context ---")
    ai = get_smart_ai()
    log_entry = {
        "timestamp": "2026-02-11T00:40:00",
        "level": "ERROR",
        "message": "Critical fuel sensor failure detected on Vehicle #5",
        "module": "sensor_monitor",
    }
    success = await ai.learn_from_log(log_entry)
    print(f"Index log success: {success}")

    stats = ai.get_stats()
    print(f"AI KB Stats: {stats['knowledge_base']['total_documents']} docs indexed.")


async def test_structured_caching():
    print("\n--- Testing Structured Caching ---")
    cache = get_cache_manager()
    analiz = get_analiz_service()

    # Pre-set some cache
    cache.set("arac:5:stats", "dummy_stats")
    print(f"Cached arac:5:stats: {cache.get('arac:5:stats')}")

    # Invalidate pattern
    cache.delete_pattern("arac:5:*")
    print(f"After invalidation, arac:5:stats: {cache.get('arac:5:stats')}")


async def test_self_healing():
    print("\n--- Testing Self-Healing Diagnostics ---")
    # Test specific pattern match
    response = create_error_response(
        400, "bos_sefer should not have ton > 0", "VALIDATION_ERROR", "req_123"
    )
    data = response.body.decode()
    print(f"Error Response Body: {data}")
    if "suggestion" in data and "bos_sefer" in data:
        print("Suggestion FOUND for bos_sefer error.")
    else:
        print("Suggestion MISSING or incorrect.")


async def test_eei_calculation():
    print("\n--- Testing EEI Calculation ---")
    analiz = get_analiz_service()
    eei = analiz.calculate_eei(40.0, 30.0)  # actual > predicted (verimsiz)
    print(f"EEI (Actual: 40, Predicted: 30): {eei} (Expected < 100)")

    eei_good = analiz.calculate_eei(25.0, 30.0)  # actual < predicted (verimli)
    print(f"EEI (Actual: 25, Predicted: 30): {eei_good} (Expected > 100)")


async def main():
    try:
        await test_ai_context()
        await test_structured_caching()
        await test_self_healing()
        await test_eei_calculation()
        print("\n✅ Phase 4 Verification Completed.")
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
