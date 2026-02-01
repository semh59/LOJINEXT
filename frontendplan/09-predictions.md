# 09 - AI Tahminler

> ML/AI modelleri ile yakıt tüketim tahmini ve trend analizi
> **Backend Senkronizasyonu:** ✅ Güncel (2026-01-30)

---

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│                            AI Tahminler                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    🎯 Yakıt Tahmini                             ││
│  │                                                                 ││
│  │  Araç: [34ABC123 ▾]    Şoför: [A.Yılmaz ▾]                     ││
│  │  Mesafe: [450] km      Yük: [18] ton                           ││
│  │  Tırmanış: [500] m     İniş: [300] m                           ││
│  │                                                                 ││
│  │  [Tahmin Et]                                                    ││
│  │                                                                 ││
│  │  ┌─────────────────────────────────────────────────────────┐   ││
│  │  │    Tahmini Tüketim: 34.2 L/100km                        │   ││
│  │  │    Güven Aralığı: 31.5 - 36.9 L/100km (95%)            │   ││
│  │  │    Model: 5-Model Ensemble                              │   ││
│  │  └─────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌────────────────────────────┐ ┌────────────────────────────────┐  │
│  │  📈 Haftalık Tahmin       │ │  📊 Trend Analizi              │  │
│  │                            │ │                                │  │
│  │  7 günlük tahmin grafiği   │ │  Trend: Artıyor ↑             │  │
│  │  + güven aralığı           │ │  Eğim: +0.5                   │  │
│  │                            │ │  Mevcut: 35.2 L/100km         │  │
│  │                            │ │  Önceki: 34.1 L/100km         │  │
│  └────────────────────────────┘ └────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Yakıt Tahmini Formu

### Form Fields

| Alan | Tip | Kural |
|------|-----|-------|
| Araç* | Select | Aktif araçlar |
| Şoför | Select | Aktif şoförler (skor için) |
| Mesafe* | Number | 1-10000 km |
| Yük | Number | 0-50 ton |
| Tırmanış | Number | 0-5000 m |
| İniş | Number | 0-5000 m |

### 💎 Hero Prediction Display
- **Visual**: Tahmin sonucu, kenarları hafif parlayan (Glow) geniş bir Glass Card içinde gösterilir.
- **Güven Aralığı**: `confidence_low` ve `confidence_high` değerleri 95% güven aralığı olarak gösterilir.
- **Animation**: Değer (L/100km) ekranda "Count-up" efektiyle belirir.
- **Smart Loading**: Hesaplama sırasında "AI İşleniyor..." metni ile birlikte beyin merkezli "Pulse" animasyonu gösterilir.

### 🧠 Smart Ensemble Engine (Backend Mimarisi)

> **ÖNEMLİ:** Backend 5-model ensemble sistemi kullanır. Frontend bu detayları API response'dan alır.

- **Hybrid Architecture (5 Model)**:
    - **Fizik Bazlı Model (40%)**: Hava direnci, yuvarlanma direnci ve tırmanış enerjisi hesaplaması.
    - **LightGBM (25%)**: Kategorik veriler ve hızlı trend analizi.
    - **XGBoost (20%)**: En güçlü hata düzeltme katmanı.
    - **LSTM (10%)**: Time-series forecasting, Monte Carlo dropout.
    - **Random Forest (5%)**: Varyans azaltma.
- **Core Factors**:
    - **Vehicle Specs**: Drag (Cd), boş ağırlık, lastik direnci ve Euro sınıfı.
    - **Environmental**: Mevsimsel faktör, yol kalitesi, yükseklik profili.
    - **Driver Score**: Şoför skoru (0.1-2.0) yakıt çarpanı olarak kullanılır.
- **Model Checksum**: Backend SHA256 ile model bütünlüğünü doğrular.

---

## Haftalık Tahmin Grafiği (LSTM Time-Series)

| Özellik | Değer |
|---------|-------|
| Chart Type | Line + Confidence Band |
| Line | `#3B82F6` |
| Confidence | `rgba(59,130,246,0.1)` |
| X Axis | 7 gün (tarihler) |
| Y Axis | L/100km |
| Tooltip | Tarih + Tahmin + Aralık |

---

## Trend Analizi Kartı

### Trend Badge

| Trend | Icon | Color |
|-------|------|-------|
| Artıyor | ↑ | `#EF4444` (kötü) |
| Azalıyor | ↓ | `#10B981` (iyi) |
| Sabit | → | `#475569` |

### Metrics

| Metric | Format |
|--------|--------|
| Eğim | +0.5 veya -0.3 |
| Mevcut | X.X L/100km |
| Önceki | X.X L/100km |

---

## Model Durumu (Admin Panel)

```
┌────────────────────────────────────────────────────────────────┐
│  🤖 Model Durumu                                               │
│                                                                │
│  ✅ Physics Model      (Ağırlık: 40%)   Checksum: ✓           │
│  ✅ LightGBM           (Ağırlık: 25%)   Trained: 1,234 samples│
│  ✅ XGBoost            (Ağırlık: 20%)   R²: 0.87              │
│  ✅ LSTM               (Ağırlık: 10%)   Last Train: 2 gün önce│
│  ✅ Random Forest      (Ağırlık: 5%)    Features: 12          │
│                                                                │
│  [Modeli Eğit]                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## API (Backend Doğrulanmış ✅)

```
# Tek Tahmin (PredictionResponse)
POST /api/v1/predictions/predict
Body: { 
    arac_id: 5, 
    mesafe_km: 450.0, 
    ton: 18.0, 
    ascent_m: 500.0, 
    descent_m: 300.0,
    sofor_id: 3,           // opsiyonel
    sofor_score: 1.2,      // opsiyonel (0.1-2.0)
    model_type: "linear"   // "linear" | "xgboost"
}
Response: {
    tahmini_tuketim: 34.2,
    model_used: "linear",           // "linear" | "xgboost"
    status: "success",
    confidence_low: 30.78,          // ±10% 
    confidence_high: 37.62,
    faktorler: null                 // opsiyonel
}

# Zaman Serisi Tahmini (LSTM)
GET /api/v1/predictions/time-series/forecast?arac_id=5
Response: { 
    success: true,
    forecast: [32.1, 32.5, 33.0, ...],
    forecast_dates: ["2026-01-31", ...],
    confidence_low: [30.1, ...],
    confidence_high: [34.1, ...],
    trend: "stable",
    vehicle_id: 5
}

# Trend Analizi
GET /api/v1/predictions/time-series/trend?arac_id=5&days=30
Response: { 
    success: true,
    trend: "increasing",              // "increasing" | "stable" | "decreasing"
    trend_tr: "Artıyor",              // "Artıyor" | "Sabit" | "Azalıyor"
    slope: 0.5,
    current_avg: 35.2,
    previous_avg: 34.1,
    moving_average_7: [34.5, 34.8, ...]
}

# Ensemble Durumu (Backend Formatı!)
GET /api/v1/predictions/ensemble/status
Response: { 
    models: {
        physics: true,
        lightgbm: true,       // kütüphane varsa
        xgboost: true,        // kütüphane varsa  
        gradient_boosting: true,
        random_forest: true
    },
    weights: { physics: 0.4, lightgbm: 0.25, ... },
    sklearn_available: true,
    lightgbm_available: true,
    xgboost_available: true,
    total_models: 5
}

# Time-Series Model Durumu
GET /api/v1/predictions/time-series/status
Response: { trained: true, last_train: "2026-01-28", epochs: 100, ... }

# Model Eğitimi (TrainingResponse)
POST /api/v1/predictions/train/{arac_id}?model_type=xgboost
Response: {
    status: "success",
    model_type: "xgboost",
    r2_score: 0.87,
    sample_count: 234,
    metrics: { ... }
}

POST /api/v1/predictions/time-series/train?arac_id=5&days=180&epochs=100
Response: { success: true, ... }
```

---

## Response Mapping (Frontend)

| API Field | UI Element |
|-----------|------------|
| `tahmini_tuketim` | Hero Card - Ana değer |
| `confidence_low` / `confidence_high` | Hero Card - Güven aralığı |
| `model_used` | Hero Card - Model etiketi |
| `faktorler` | Detay Tab - Faktör breakdown |
| `forecast[]` | Haftalık Grafik - Line data |
| `trend_tr` | Trend Kartı - Badge |
| `slope` | Trend Kartı - Eğim değeri |
