import asyncio
import os
import sys
import json
from pydantic import ValidationError

sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.schemas.sofor import SoforCreate
from app.core.services.sofor_service import get_sofor_service

async def diagnose():
    service = get_sofor_service()
    
    # Test Data from Frontend (simulated)
    payload = {
        "ad_soyad": "Gerçek Test Sürücüsü",
        "telefon": "0555 111 22 33",
        "ise_baslama": "2024-01-28",
        "ehliyet_sinifi": "E",
        "manual_score": 1.5,
        "notlar": "Test için oluşturuldu"
        # Note: 'score' is missing here, should get default 1.0 from schema
    }
    
    print("--- Testing Pydantic Validation ---")
    try:
        sofor_in = SoforCreate(**payload)
        print("Pydantic Validation: SUCCESS")
        print(f"Validated Data: {sofor_in.model_dump()}")
    except ValidationError as e:
        print(f"Pydantic Validation: FAIL")
        print(e.json())
        return

    print("\n--- Testing Service.add_sofor ---")
    try:
        sofor_id = await service.add_sofor(
            ad_soyad=sofor_in.ad_soyad,
            telefon=sofor_in.telefon,
            ehliyet_sinifi=sofor_in.ehliyet_sinifi,
            ise_baslama=str(sofor_in.ise_baslama) if sofor_in.ise_baslama else None,
            manual_score=sofor_in.manual_score,
            notlar=sofor_in.notlar
        )
        print(f"Service.add_sofor: SUCCESS (ID: {sofor_id})")
    except Exception as e:
        print(f"Service.add_sofor: FAIL")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diagnose())
