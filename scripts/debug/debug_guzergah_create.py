import asyncio
import os
import sys

# Add root to python path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.repositories.guzergah_repo import GuzergahRepository
from app.core.services.guzergah_service import GuzergahService
from app.schemas.guzergah import GuzergahCreate

async def main():
    print("Testing Guzergah Creation with Coords...")
    
    async with AsyncSessionLocal() as db:
        repo = GuzergahRepository(session=db)
        service = GuzergahService(repo=repo)
        
        # Data with coordinates (Gebze -> Ankara)
        # 0 km initially. Should be updated by RouteService.
        dto = GuzergahCreate(
            ad="Test Rota Auto",
            cikis_yeri="Gebze",
            varis_yeri="Ankara",
            mesafe_km=0, 
            cikis_lat=40.80277,
            cikis_lon=29.43068,
            varis_lat=39.92078,
            varis_lon=32.85405
        )
        
        try:
            print("Creating route...")
            result = await service.create_guzergah(dto)
            
            print("--- RESULT ---")
            print(f"ID: {result.id}")
            print(f"Name: {result.ad}")
            print(f"Mesafe: {result.mesafe_km} km") # Should be ~380-450 km
            print(f"Ascent: {result.ascent_m}")
            print(f"Geometry present: {bool(result.geometry)}")
            
            if result.mesafe_km > 10:
                print("SUCCESS: Distance updated from API!")
            else:
                print("FAILURE: Distance not updated.")
                
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
