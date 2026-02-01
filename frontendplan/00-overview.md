# LojiNext AI - Web Arayüzü Tasarım Dökümanları

> **Amaç:** Tasarımcıya verilecek sayfa özellik dökümanları
> **Platform:** Desktop only (1280px - 1920px)
> **Kullanıcı:** Filo Yöneticisi (Admin)
> **Teknoloji:** React
> **Backend Senkronizasyonu:** ✅ Güncel (2026-01-30)

---

## 📁 Dosya Yapısı

```
pages/
├── 00-overview.md          ← Bu dosya (genel bakış)
├── 01-design-system.md     ← Renk, tipografi, spacing, komponentler
├── 02-login.md             ← Giriş sayfası
├── 03-dashboard.md         ← Ana sayfa
├── 04-vehicles.md          ← Araçlar
├── 05-drivers.md           ← Sürücüler
├── 06-trips.md             ← Seferler
├── 07-fuel.md              ← Yakıt kayıtları
├── 08-reports.md           ← Raporlar
├── 09-predictions.md       ← AI Tahminler
├── 10-alerts.md            ← Uyarılar
├── 11-locations.md         ← Güzergahlar
├── 12-settings.md          ← Ayarlar
└── 13-users.md             ← Kullanıcı yönetimi
```

---

## 🎨 Tasarım Prensipleri (Premium & Smart)

| Prensip | Açıklama |
|---------|----------|
| **Premium Aesthetics** | Canlı renkler, yumuşak gölgeler ve cam efekti (Glassmorphism) ile üst düzey görünüm |
| **Glassmorphism** | `backdrop-blur` ve yarı saydam katmanlar ile derinlik hissi |
| **Smart UI Logic** | Optimistic updates (anlık tepki), akıllı validasyonlar ve hata önleyici UX |
| **Data-First** | Kritik verilerin (tüketim, sefer) en az tıklama ile görünürlüğü |
| **Resilient UX** | Skeleton loading ve kararlı bildirim (Toast) sistemi ile kesintisiz deneyim |

---

## 🧭 Navigasyon Haritası

```
Login → Dashboard ─┬→ Araçlar
                   ├→ Sürücüler
                   ├→ Seferler
                   ├→ Yakıt
                   ├→ Güzergahlar
                   ├→ Raporlar
                   ├→ AI Tahminler
                   ├→ Uyarılar (Header Bell)
                   ├→ Ayarlar (Admin)
                   └→ Kullanıcılar (Admin)
```

---

## 📐 Sayfa Şablonu (Ortak Layout)

```
┌─────────┬────────────────────────────────────────────────────────┐
│         │                    HEADER (64px)                       │
│         │  [Sayfa Başlığı]              🔔(3)  👤 Admin ▾       │
│ SIDEBAR ├────────────────────────────────────────────────────────┤
│ (260px) │                                                        │
│         │                    CONTENT AREA                        │
│  Menu   │                    (padding: 32px)                     │
│  Items  │                                                        │
│         │                                                        │
└─────────┴────────────────────────────────────────────────────────┘
```

---

## 🔗 Backend API Gateway

| Base URL | `http://localhost:8000/api/v1` |
|----------|--------------------------------|
| Auth | Bearer Token (JWT) |
| Content-Type | `application/json` |
| Rate Limit | Endpoint dependent (bkz. sayfa dökümanları) |

---

## 🏗️ Backend Mimari Özeti

### ML/AI Katmanı (5-Model Ensemble)
- **Physics Model (40%)**: Aerodinamik, yuvarlanma direnci, tırmanış enerjisi
- **LightGBM (25%)**: Kategorik feature, hızlı trend analizi
- **XGBoost (20%)**: Gradient boosting hata düzeltme
- **LSTM (10%)**: Time-series forecast, Monte Carlo dropout
- **Random Forest (5%)**: Varyans azaltma

### Güvenlik Özellikleri
- ✅ JWT Authentication (bcrypt rounds=12)
- ✅ Rate Limiting (Token bucket)
- ✅ XSS Protection (16 pattern)
- ✅ SQL Injection Prevention (ORM)
- ✅ CORS Policy (Config-based)
- ✅ Timing Attack Prevention (Dummy hash)
- ✅ Audit Logging (Tüm CRUD)

### Event-Driven Architecture
- EventBus ile cache invalidation
- Correlation ID tracking (distributed tracing)
- Idempotent event handling
