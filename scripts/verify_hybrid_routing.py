import sys
import os
import asyncio
import logging
from unittest.mock import patch

sys.path.append(os.getcwd())

# Ensure env is loaded
from dotenv import load_dotenv

load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

from app.infrastructure.routing.mapbox_client import MapboxClient
from app.services.route_service import RouteService
from app.core.services.route_validator import RouteValidator


async def verify_mapbox_direct():
    """Test direct connection to Mapbox API"""
    logger.info("--- Testing MapboxClient Direct Connection ---")
    client = MapboxClient()

    # Istanbul coordinates (cca. Eminonu -> Taksim)
    # Using short distance to save bandwidth/latency
    start = (28.9784, 41.0082)
    end = (28.9850, 41.0370)

    result = await client.get_route(start, end)

    if result:
        logger.info(f"SUCCESS: Mapbox returned route.")
        logger.info(f"Distance: {result['distance_km']} km")
        logger.info(f"Duration: {result['duration_min']} min")
        return True
    else:
        logger.error("FAIL: Mapbox return None.")
        return False


async def verify_hybrid_fallback():
    """Test RouteService logic switching to Mapbox on anomaly"""
    logger.info("\n--- Testing Hybrid Routing Fallback Logic ---")

    service = RouteService()

    # Dummy mock return for ORS that triggers anomaly
    # validator checks if ascent/distance > 2.5% or something similar?
    # Actually validator checks average grade.
    # RouteValidator.SUSPICIOUS_GRADE_THRESHOLD = 0.025 (2.5%)

    # We will patch RouteValidator.validate_and_correct to FORCE 'is_corrected=True'
    # behaving as if it found an anomaly.

    original_validate = RouteValidator.validate_and_correct

    def mocked_validate(data):
        # Let's say we detect anomaly
        # We assume the input data is from ORS
        data["is_corrected"] = True
        data["correction_reason"] = "Forced Mock Verification"
        return data

    with patch.object(
        RouteValidator, "validate_and_correct", side_effect=mocked_validate
    ):
        # We need coordinates that ORS would normally fetch.
        # But we want to simulate the fallback.
        # If we use real ORS, it might be slow or use quota.
        # But RouteService calls ORS first.
        # We can also patch the ORS call inside RouteService if we want strict unit testing.
        # But let's try integration: Call real ORS (lite), get result, Validaor flags it (mock), then calls Mapbox.

        start = (28.9784, 41.0082)
        end = (28.9850, 41.0370)

        # NOTE: We need use_cache=False to force API usage
        try:
            # We must ensure we don't accidentally write to DB or it's fine (dev env).
            # It writes to 'route_paths'.

            result = await service.get_route_details(start, end, use_cache=False)

            logger.info(f"Final Source: {result.get('source')}")

            if result.get("source") == "mapbox_hybrid":
                logger.info("SUCCESS: RouteService switched to Mapbox!")
            else:
                logger.error(
                    f"FAIL: Source is {result.get('source')}, expected 'mapbox_hybrid'"
                )

        except Exception as e:
            logger.error(f"Service Error: {e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run tests
    success_direct = loop.run_until_complete(verify_mapbox_direct())
    if success_direct:
        loop.run_until_complete(verify_hybrid_fallback())
    else:
        logger.error("Skipping Hybrid Logic test due to Mapbox connection failure.")
