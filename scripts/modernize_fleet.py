import asyncio
from app.database.unit_of_work import get_uow
from app.database.models import Arac
from sqlalchemy import select, update


async def modernize_fleet():
    print("Modernizing fleet parameters to Euro 6 standards...")
    async with get_uow() as uow:
        # Update all vehicles using legacy defaults (0.38 efficiency)
        stmt = (
            update(Arac)
            .where(Arac.motor_verimliligi == 0.38)
            .values(
                motor_verimliligi=0.44,
                hava_direnc_katsayisi=0.52,
                lastik_direnc_katsayisi=0.006,
            )
        )
        result = await uow.session.execute(stmt)
        await uow.commit()
        print(f"Modernized vehicles.")


if __name__ == "__main__":
    asyncio.run(modernize_fleet())
