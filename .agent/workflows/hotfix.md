---
description: Production bug düzelt — planlama atla, hızlı fix, regression test
---

# /hotfix — Acil Hata Düzeltme

## Adım 1 — Sorun Teşhisi (Reason)
- Hata loglarını ve context'i analiz et.
- Hatayı reproduse etmek için hızlı bir test senaryosu oluştur.

## Adım 2 — Uygula (Act) // turbo
- Sorunu çözen en minimal ve güvenli kodu (UoW patternini bozmadan) uygula.
- PII ve güvenlik açıklarını kontrol et.

## Adım 3 — Doğrulama & Temizlik (Verify)
- Regression testlerini çalıştır.
- Yapılan değişikliği `AuditLog` üzerinden gözlemle.
- **Hotfix Report Artifact** ile kullanıcıyı bilgilendir.
