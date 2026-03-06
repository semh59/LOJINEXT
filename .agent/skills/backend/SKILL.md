# Skill: Backend Python (Elite)

## Ne Zaman Yükle
- Business logic (service), database (repository) veya API değişikliği yaparken.

## Mimari Standartlar
- **Unit of Work (UOW)**: Transaction yönetimi `app/database/unit_of_work.py` üzerinden yapılır.
- **Event-Driven**: Kritik veri değişikliklerinde `EventBus.publish` kullanılır.
- **Audit Logging**: Kritik aksiyonlar `app/infrastructure/audit` altındaki `audit_log` ile kaydedilir.

## Kod Desenleri (Elite Pattern)
- Service'den Repository'e erişim:
  ```python
  async with get_uow() as uow:
      await uow.{repo}.add(...)
      await uow.commit() # UOW dışı commit yasak.
  ```
- Event fırlatma:
  ```python
  @publishes(EventType.{EVENT_TYPE})
  async def update_status(self, ...):
      await self.event_bus.publish(...)
  ```

## Yapma
- Manuel `session.commit()` yapma (UOW kullan).
- Raw SQL yazma (ORM/Repository katmanını baypas etme).
- Sürücü PII verilerini (TCKN, tel) loglara veya audit_log'a yazma.
