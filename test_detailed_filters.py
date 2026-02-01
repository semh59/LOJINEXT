import asyncio
import os
import sys
import json

sys.path.append(os.getcwd())

from app.core.services.sofor_service import get_sofor_service
from app.core.services.arac_service import get_arac_service

async def test_filters():
    sofor_service = get_sofor_service()
    arac_service = get_arac_service()
    
    print("=== Testing DRIVER Filters ===")
    
    # 1. Test Score Range (High score)
    high_score = await sofor_service.get_all_paged(min_score=1.5)
    print(f"Drivers with score >= 1.5: {len(high_score)}")
    for d in high_score:
        print(f"  - {d['ad_soyad']}: {d['score']}")

    # 2. Test License Class
    e_class = await sofor_service.get_all_paged(ehliyet_sinifi="E")
    print(f"\nDrivers with License E: {len(e_class)}")
    
    # 3. Combined Filter
    combined_drivers = await sofor_service.get_all_paged(ehliyet_sinifi="E", max_score=1.2)
    print(f"\nDrivers with License E AND Score <= 1.2: {len(combined_drivers)}")

    print("\n=== Testing VEHICLE Filters ===")
    
    # 4. Test Year Range
    modern_arac = await arac_service.get_all_paged(min_yil=2022)
    print(f"Vehicles built >= 2022: {len(modern_arac)}")
    for a in modern_arac:
        # Pydantic model to dict
        a_dict = a.model_dump() if hasattr(a, 'model_dump') else a
        print(f"  - {a_dict['plaka']}: {a_dict['yil']}")

    # 5. Test Brand Filter
    scania = await arac_service.get_all_paged(marka="SCANIA")
    print(f"\nScania Vehicles: {len(scania)}")

    # 6. Combined Search + Filter
    combined_arac = await arac_service.get_all_paged(search="34", min_yil=2015)
    print(f"\nVehicles with '34' in plaque AND Year >= 2015: {len(combined_arac)}")

if __name__ == "__main__":
    asyncio.run(test_filters())
