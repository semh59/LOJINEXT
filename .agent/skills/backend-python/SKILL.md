# Skill: Backend Python (Elite Factory Standard)

## Ne Zaman Yükle
- Business logic (service), database (repository) veya API değişikliği yaparken.

## Bu Skill Ne Bilir

### Elite Foundations
- **Unit of Work (UOW)**: Transaction'lar `app/database/unit_of_work.py` üzerinden yönetilir. 
  ```python
  async with get_uow() as uow:
      await uow.sefer_repo.add(...)
      await uow.commit()
  ```
- **Repository Pattern**: `app/database/repositories/` altındaki repository'ler `BaseRepository`'den türer ve `all()`, `get_by_id()`, `add()` gibi standart metodlara sahiptir.
- **Event-Driven**: Durum değişiklikleri için `app/infrastructure/events/event_bus.py` kullanılır. `@publishes` dekoratörü ve `EventBus.publish` metodlarını takip et.
- **Audit Logging**: Kritik aksiyonları `app/infrastructure/audit` altındaki `audit_log` ile kaydet.

### Kod Standartları
- Tüm servis metodları `async` olmalı.
- Pydantic şemaları `app/schemas/` altında (SeferCreate, SoforUpdate vb.) tanımlanmalıdır.
- Type hint (Mapped/mapped_column) zorunludur.

## Yapma
- Manuel `session.commit()` yapma (UOW kullan).
- Repository katmanını baypas edip direkt SQL yazma.
