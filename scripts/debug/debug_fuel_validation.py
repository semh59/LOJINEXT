import asyncio
from app.database.connection import AsyncSessionLocal
from sqlalchemy import text
from app.schemas.yakit import YakitResponse
from pydantic import ValidationError


async def debug_validation():
    async with AsyncSessionLocal() as session:
        # Check for 0 or negative values in strict fields
        low_val_res = await session.execute(
            text(
                "SELECT id, litre, fiyat_tl, toplam_tutar FROM yakit_alimlari WHERE litre <= 0 OR fiyat_tl <= 0 OR toplam_tutar <= 0"
            )
        )
        low_vals = list(low_val_res.mappings())
        print(f"Records with low/zero values: {len(low_vals)}")
        for v in low_vals[:5]:
            print(dict(v))

        # Test validation on all records
        query = """
            SELECT ya.*, a.plaka 
            FROM yakit_alimlari ya
            JOIN araclar a ON ya.arac_id = a.id
        """
        res = await session.execute(text(query))
        records = res.mappings().all()

        valid_count = 0
        invalid_count = 0
        errors = []

        for r in records:
            data = dict(r)
            try:
                YakitResponse.model_validate(data)
                valid_count += 1
            except ValidationError as e:
                invalid_count += 1
                if len(errors) < 5:
                    errors.append((data["id"], str(e)))

        print(f"\nValidation Summary:")
        print(f"Valid: {valid_count}")
        print(f"Invalid: {invalid_count}")

        if errors:
            print("\nSample Validation Errors:")
            for rid, err in errors:
                print(f"Record ID {rid}: {err}")


if __name__ == "__main__":
    asyncio.run(debug_validation())
