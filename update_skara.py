import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.database.unit_of_work import UnitOfWork
from app.database.models import Kullanici

async def update_skara_account():
    # Hash generated in previous step for 'lojinext123'
    new_hash = "$2b$12$pW1Thns34RuWlynQe6OANOB9f5CQObdbxJtgJKoRNLHPGG7I2kJ9y"
    
    async with UnitOfWork() as uow:
        # Update first account skara@lojinext.internal (id: 1)
        k1 = await uow.kullanici_repo.get_by_id(1)
        if k1:
            print(f"Updating account 1: {k1['email']}")
            await uow.kullanici_repo.update(1, sifre_hash=new_hash, rol_id=1, aktif=True)
            
        # Update second account skara (id: 3)
        k3 = await uow.kullanici_repo.get_by_id(3)
        if k3:
            print(f"Updating account 3: {k3['email']}")
            await uow.kullanici_repo.update(3, sifre_hash=new_hash, rol_id=1, aktif=True)
            
        await uow.commit()
        print("Success: Skara accounts updated with password 'lojinext123' and super_admin role.")

if __name__ == "__main__":
    asyncio.run(update_skara_account())
