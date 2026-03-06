import asyncio
from datetime import date, timedelta
from app.database.connection import AsyncSessionLocal
from sqlalchemy import text
from app.schemas.yakit import YakitResponse
from pydantic import ValidationError


async def check_visibility():
    today = date(2026, 2, 13)  # Simulation today based on logs
    start_date = today - timedelta(days=30)

    async with AsyncSessionLocal() as session:
        query = """
            SELECT ya.*, a.plaka 
            FROM yakit_alimlari ya
            JOIN araclar a ON ya.arac_id = a.id
        """
        res = await session.execute(text(query))
        records = res.mappings().all()

        counts = {
            "total": 0,
            "within_date_range": 0,
            "valid_and_within_range": 0,
            "invalid_but_within_range": 0,
            "invalid_reason_counts": {},
        }

        for r in records:
            counts["total"] += 1
            rec_date = r["tarih"]

            in_range = rec_date >= start_date
            if in_range:
                counts["within_date_range"] += 1

            try:
                YakitResponse.model_validate(dict(r))
                if in_range:
                    counts["valid_and_within_range"] += 1
            except ValidationError as e:
                if in_range:
                    counts["invalid_but_within_range"] += 1
                    for error in e.errors():
                        loc = str(error["loc"][0])
                        msg = error["msg"]
                        key = f"{loc}: {msg}"
                        counts["invalid_reason_counts"][key] = (
                            counts["invalid_reason_counts"].get(key, 0) + 1
                        )

        print(f"Total Records: {counts['total']}")
        print(
            f"Records within date range (>={start_date}): {counts['within_date_range']}"
        )
        print(f"Valid and visible: {counts['valid_and_within_range']}")
        print(f"Invalid but in range: {counts['invalid_but_within_range']}")
        print("\nInvalid reasons for records in range:")
        for reason, count in counts["invalid_reason_counts"].items():
            print(f"- {reason}: {count}")


if __name__ == "__main__":
    asyncio.run(check_visibility())
