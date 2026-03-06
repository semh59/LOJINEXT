from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:!23efe25ali!@localhost:5432/tir_yakit")
with engine.connect() as conn:
    print("--- 1. Unique constraints on seferler ---")
    res = conn.execute(
        text(
            "SELECT conname FROM pg_constraint WHERE conrelid = 'seferler'::regclass AND contype IN ('u', 'p');"
        )
    )
    print(res.fetchall())

    print("--- 2. Check constraints on seferler ---")
    res = conn.execute(
        text(
            "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'seferler'::regclass AND contype = 'c';"
        )
    )
    print(res.fetchall())

    print(
        "--- 3. Column definitions (ascent, descent, tahmini, is_real, rota_detay, etc) ---"
    )
    res = conn.execute(
        text(
            "SELECT column_name, data_type, column_default, is_nullable FROM information_schema.columns WHERE table_name = 'seferler';"
        )
    )
    for row in res.fetchall():
        print(f"{row[0]}: {row[1]}, default={row[2]}, nullable={row[3]}")

    print("--- 4. Triggers on seferler ---")
    res = conn.execute(
        text(
            "SELECT trigger_name, event_manipulation, action_timing FROM information_schema.triggers WHERE event_object_table = 'seferler';"
        )
    )
    print(res.fetchall())

    print("--- 5. MV Check (sefer_istatistik_mv) ---")
    try:
        res = conn.execute(
            text(
                "SELECT matviewname FROM pg_matviews WHERE matviewname = 'sefer_istatistik_mv';"
            )
        )
        print(res.fetchall())
    except Exception as e:
        print("MV Error:", e)

    print("--- 6. MV Index Check ---")
    try:
        res = conn.execute(
            text(
                "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'sefer_istatistik_mv';"
            )
        )
        print(res.fetchall())
    except Exception as e:
        print("MV Index Error:", e)

    print("--- 7. seferler_log Check ---")
    res = conn.execute(
        text(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'seferler_log';"
        )
    )
    print(res.fetchall())
