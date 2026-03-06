import asyncio
from app.database.models import Lokasyon
from sqlalchemy import inspect


def check_model():
    mapper = inspect(Lokasyon)
    print("--- Lokasyon Columns ---")
    for column in mapper.attrs:
        print(f"Attr: {column.key}")

    print("\n--- Physical Columns ---")
    for column in Lokasyon.__table__.columns:
        print(f"Table Column: {column.name}")


if __name__ == "__main__":
    check_model()
