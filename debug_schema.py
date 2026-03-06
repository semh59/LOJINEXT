import asyncio
import sys
from unittest.mock import MagicMock
from sqlalchemy.types import UserDefinedType


# Mock Geometry
class MockGeometry(UserDefinedType):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def get_col_spec(self, **kw):
        return "TEXT"


sys.modules["geoalchemy2"] = MagicMock()
sys.modules["geoalchemy2"].Geometry = MockGeometry


async def check_ddl():
    from app.database.models import Lokasyon

    print("Columns in Lokasyon table object:")
    for col in Lokasyon.__table__.columns:
        print(f" - {col.name}: {col.type}")


if __name__ == "__main__":
    # Add project root to sys.path
    import os

    sys.path.append(os.getcwd())
    asyncio.run(check_ddl())
