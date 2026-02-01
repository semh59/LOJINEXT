---
description: Safe database migration workflow using Alembic.
---

# Step 8: DATABASE MIGRATION (Veritabanı Göçü)

Changing the schema without losing data.

## 1. Preparation
- [ ] Backup the current database! (`cp app.db app.db.bak`).
- [ ] Verify models in `app/models/`.

## 2. Generate Migration
```bash
# Otomatik algılama
alembic revision --autogenerate -m "added_driver_status"
```
**CRITICAL**: Inspect the generated file in `alembic/versions/`.
- Does it drop tables? (⚠️ DANGER)
- Does it alter columns correctly?

## 3. Manual Verification
If complex data migration is needed (e.g., splitting a column):
- Create a script in `scripts/migrate_manual_score.py` (like existing ones).
- Test it on a copy of the DB.

## 4. Apply
```bash
alembic upgrade head
```

## 5. Verification
- Run `python scripts/check_db_contents.py` to verify data integrity.
