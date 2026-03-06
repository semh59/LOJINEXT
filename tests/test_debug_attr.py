import pytest
from sqlalchemy import select
from app.database.models import Arac

@pytest.mark.asyncio
async def test_debug_attr(db_session):
    stmt = select(Arac).limit(1)
    result = await db_session.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
        print('Found object:', type(obj))
        for c in obj.__class__.__table__.columns:
            try:
                print('Testing column:', c.name)
                val = getattr(obj, c.name)
                print(c.name, 'OK')
            except Exception as e:
                print(c.name, 'ERROR:', type(e), e)
    else:
        print('No object found')
