# LOJINEXT — Elite Global Agent Kuralları

## 🏗️ Mimari Standartlar

**Katman Zinciri (UoW Zorunluluğu):**
`router → service → unit_of_work → repository → model`
- Servis katmanı repository'e doğrudan erişmez, her zaman UnitOfWork (UoW) üzerinden geçer.
- UoW dışında manuel `session.commit()` veya transaction açılmaz.

**Event-Driven Mimari:**
- Kritik domain olayları (durum değişiklikleri, önemli atamalar) `EventBus` üzerinden publish edilmelidir.
- Servisler arası sıkı bağımlılıktan (direct calling) kaçınıp EventBus tercih edilmelidir.

## 🚛 Domain Kuralları

**Araç & Sürücü (Fleet):**
- Araç statüsü her değiştiğinde `vehicle_event_log` tablosuna kayıt atılır.
- Konum verileri Redis'te (TTL: 5 dk) ve PostgreSQL'de saklanır (GDPR: 90 gün limit).
- Sürücü PII verileri (TCKN, telefon, ad) asla `logger` veya `audit_log` içine yazılmaz.

**Sefer & Rota:**
- Tüm zaman hesaplamaları **UTC** olarak yapılır.
- Rota olayları (`route.started`, `route.completed`) EventBus'a bildirilmelidir.

**AI & Tahmin:**
- Model çıktısı sabit şemaya uymalıdır: `{ prediction, confidence, feature_importance, model_version, fallback_triggered, physics_override }`.
- Confidence thresholdları: < 0.60 (Sarı Uyarı), < 0.40 (Kırmızı/Manuel Giriş).
- Model hatasında rule-based fallback çalıştırılmalıdır.

## ⚙️ Teknik Standartlar
- Tüm public fonksiyonlar: type hint + docstring.
- Yeni endpointlerde rate limiting ve pagination (default limit: 50, max: 200) zorunludur.
- API Standart Formatı: `{ data, meta, errors }`.
- Frontend listeleri 100+ kayıt için `virtualization` kullanmalıdır.
