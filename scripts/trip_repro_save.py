import asyncio
import os
import sys
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.repositories.sefer_repo import SeferRepository
from app.core.services.sefer_service import SeferService
from app.schemas.sefer import SeferCreate
from app.database.repositories.arac_repo import AracRepository
from app.database.repositories.sofor_repo import SoforRepository
from app.database.repositories.lokasyon_repo import LokasyonRepository


async def test_save():
    print("Testing Sefer save via Service...")
    async with AsyncSessionLocal() as session:
        # We need real IDs
        arac_repo = AracRepository(session=session)
        sofor_repo = SoforRepository(session=session)
        lokasyon_repo = LokasyonRepository(session=session)

        arac = (await arac_repo.get_all(limit=1))[0]
        sofor = (await sofor_repo.get_all(limit=1))[0]
        lokasyon = (await lokasyon_repo.get_all(limit=1))[0]

        print(
            f"Using Arac ID: {arac.get('id')}, Sofor ID: {sofor.get('id')}, Lokasyon ID: {lokasyon.get('id')}"
        )

        data = SeferCreate(
            tarih=date.today(),
            saat="14:30",
            arac_id=arac.get("id"),
            sofor_id=sofor.get("id"),
            guzergah_id=lokasyon.get("id"),
            cikis_yeri=lokasyon.get("cikis_yeri"),
            varis_yeri=lokasyon.get("varis_yeri"),
            mesafe_km=145.5,  # Float distance
            bos_agirlik_kg=8000,
            dolu_agirlik_kg=24000,
            net_kg=16000,
            durum="Tamam",
        )

        repo = SeferRepository(session=session)
        service = SeferService(repo=repo)

        try:
            sefer_id = await service.add_sefer(data)
            print(f"Success! Created Sefer ID: {sefer_id}")
        except Exception as e:
            print(f"Failed to save Sefer: {e}")


if __name__ == "__main__":
    asyncio.run(test_save())
