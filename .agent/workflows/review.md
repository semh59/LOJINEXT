---
description: Kod review — kalite, güvenlik, filo domenine özgü kontroller
---

# /review — Elite Kod İnceleme

## Adım 1 — Kapsam ve Bağımlılık Analizi (Reason)
- Değişiklik yapılan dosyaları ve PR amacını anla.
- Katman zinciri (`router -> service -> UoW -> repo -> model`) ihlalini kontrol et.

## Adım 2 — Kalite & Güvenlik Taraması (Act) // turbo
- N+1 query taraması (`joinedload` / `selectinload` kontrolü) yap.
- Sürücü PII verilerinin sızma riskini analiz et.
- Async I/O blocking call kontrolü yap.

## Adım 3 — Karar ve Raporlama (Verify)
- LOJINEXT standartlarına (UTC, Precision, EventBus) uyumu değerlendir.
- **Review Artifact** oluştur: APPROVE / REQUEST_CHANGES.
