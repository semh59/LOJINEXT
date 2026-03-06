import asyncio
from app.core.services.verifier_service import VerifierService


async def smoke_test_verifier():
    print("--- Starting VerifierService Smoke Test ---")
    service = VerifierService()

    try:
        print("Running verify_trip_integrity...")
        result = await service.verify_trip_integrity()
        print(f"✅ Verification Result: {result}")

        if result["suspicious_count"] >= 0:
            print("✅ 'suspicious_count' field is present and valid.")
        else:
            print("❌ 'suspicious_count' is negative?")

    except Exception as e:
        print(f"❌ Verification failed: {e}")

    print("\n--- Smoke Test Complete ---")


if __name__ == "__main__":
    asyncio.run(smoke_test_verifier())
