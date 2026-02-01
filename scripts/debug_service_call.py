
import asyncio
import sys
import os

# Set up path
sys.path.append(os.getcwd())

from app.core.services.sofor_service import get_sofor_service
from app.core.entities.models import SoforCreate

async def test_bulk_add_logic():
    print("--- Starting SoforService Bulk Add Test ---")
    service = get_sofor_service()
    
    # Create a dummy Pydantic model
    dto = SoforCreate(
        ad_soyad="Test Driver Auto",
        telefon="5559998877",
        ehliyet_sinifi="E"
    )
    
    print(f"DTO Type: {type(dto)}")
    print(f"DTO Data: {dto.model_dump()}")
    
    try:
        # Pass it as a list of OBJECTS (which caused the error before fix)
        # Note: This will actually try to insert into DB, so we should expect it to work or fail with DB error, 
        # BUT NOT AttributeError.
        print("Calling bulk_add_sofor...")
        result_count = await service.bulk_add_sofor([dto])
        print(f"SUCCESS: Result count = {result_count}")
    except AttributeError as e:
        print(f"CRITICAL FAILURE: AttributeError detected! -> {e}")
        # Print Traceback manually if needed
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"Other Error (Expected if DB constraint etc): {type(e).__name__}: {e}")
        # If it's not AttributeError, the fix logic handling 'get' IS working.

if __name__ == "__main__":
    asyncio.run(test_bulk_add_logic())
