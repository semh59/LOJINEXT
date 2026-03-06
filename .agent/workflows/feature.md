---
description: Yeni bir filo özelliği için Uçtan Uca Geliştirme (Elite) — Reason-Act-Reflect-Verify döngüsüyle 8 Adım.
---

# /feature — Yeni Filo Özelliği Geliştirme

Bu workflow, LOJINEXT projesinde yeni bir özellik eklerken takip edilmesi gereken elite standarttır.

---

## Adım 1 — Kapsam ve Gereksinim Analizi (Reason)
- Kullanıcının talebini anla, belirsizlikleri netleştir.
- Mevcut sistemdeki etkilenen modülleri (`models`, `services`, `UI`) belirle.

## Adım 2 — Teknik Tasarım & Planlama
- **Unit of Work (UoW)** ve **EventBus** etkileşimlerini planla.
- PII (Kişisel veri) ve GDPR risklerini değerlendir.
- **Plan Artifact** oluştur ve kullanıcı onayı al.

## Adım 3 — Veritabanı ve Domain Geliştirme (Act) // turbo
- `models.py` güncellemesi -> Alembic migration.
- `repositories` ve `schemas` (Pydantic) katmanlarını oluştur.

## Adım 4 — Business Logic & Servis Katmanı
- Servis metodlarını `async` ve UoW uyumlu kodla.
- Kritik state değişikliklerinde `EventBus.publish` tetikle.
- `AuditLog` entegrasyonunu doğrula.

## Adım 5 — API & Frontend Geliştirme
- FastAPI router/endpointlerini tanımlat (Rate limiting & Pagination dahil).
- Frontend'de TanStack Query mutasyonlarını ve UI bileşenlerini (virtualization ile) kodla.

## Adım 6 — Doğrulama & Test (Verify)
- `pytest` ile backend (unit/integration) testlerini çalıştır.
- React Testing Library ile kritik UI flowları test et.
- Hata alınırsa Adım 7'ye (Reflect) geç.

## Adım 7 — İyileştirme & Öz-Eleştiri (Reflect)
- N+1 query taraması yap (`joinedload` kontrolü).
- UTC timezone ve PII sızıntısı kontrolü yap.
- Kod kalitesini `filo-kurallar.md` ile kıyasla.

## Adım 8 — Kayıt & Kapanış
- Commit mesajını projenin standardına göre at.
- **Walkthrough Artifact** ile yapılan her şeyi özetle.
