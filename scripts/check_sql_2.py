from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:!23efe25ali!@localhost:5432/tir_yakit")
with engine.connect() as conn:
    print("--- 1. Unique Index on sefer_no ---")
    res = conn.execute(
        text(
            "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'seferler' AND indexname LIKE '%sefer_no%';"
        )
    )
    print(res.fetchall())

    print("--- 2. net_kg duplicates or inconsistencies ---")
    res = conn.execute(
        text(
            "SELECT id, sefer_no, bos_agirlik_kg, dolu_agirlik_kg, net_kg FROM seferler WHERE net_kg != (dolu_agirlik_kg - bos_agirlik_kg) AND bos_agirlik_kg IS NOT NULL AND dolu_agirlik_kg IS NOT NULL;"
        )
    )
    print(res.fetchall())

    print("--- 3. Foreign Keys for created_by_id, updated_by_id ---")
    res = conn.execute(
        text(
            "SELECT conname FROM pg_constraint WHERE conrelid = 'seferler'::regclass AND contype = 'f';"
        )
    )
    print(res.fetchall())

    print("--- 4. Checking mat view shape ---")
    res = conn.execute(text("SELECT * FROM sefer_istatistik_mv LIMIT 1;"))
    print(res.fetchall())
