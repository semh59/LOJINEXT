# 08 - Raporlar

> PDF raporlar, maliyet analizi ve tasarruf hesaplamaları
> **Backend Senkronizasyonu:** ✅ Güncel (2026-01-30)

---

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│                               Raporlar                               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                    │
│  │ 📄 PDF      │ │ 💰 Maliyet  │ │ 📊 Tasarruf │  ← Tab/Segment    │
│  │  Raporlar   │ │  Analizi    │ │  & ROI      │                    │
│  └─────────────┘ └─────────────┘ └─────────────┘                    │
│                                                                      │
│  ╔══════════════════════════════════════════════════════════════╗   │
│  ║                     TAB CONTENT                              ║   │
│  ╚══════════════════════════════════════════════════════════════╝   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Tab 1: PDF Raporlar

### Rapor Kartları

```
┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
│  📊 Filo Özeti     │ │  🚛 Araç Detay     │ │  👤 Şoför Karşı.  │
│                    │ │                    │ │                    │
│  Genel filo        │ │  Tek araç          │ │  Performans        │
│  raporu            │ │  raporu            │ │  karşılaştırması   │
│                    │ │                    │ │                    │
│  📅 [Tarih Aralığı]│ │  🚛 [Araç Seç]     │ │                    │
│                    │ │  📅 [Ay/Yıl]       │ │                    │
│                    │ │                    │ │                    │
│  [📥 PDF İndir]    │ │  [📥 PDF İndir]    │ │  [📥 PDF İndir]    │
└────────────────────┘ └────────────────────┘ └────────────────────┘
```

| Kart | Form | Description |
|------|------|-------------|
| Filo Özeti | Date Range Picker | Tüm filo istatistikleri |
| Araç Detay | Vehicle Select + Month/Year | Tek araç raporu |
| Şoför Karşılaştırma | - (direkt indir) | Performans sıralaması |

---

## Tab 2: Maliyet Analizi

### Dönemsel Analiz

```
┌─────────────────────────────────────────────────────────────────┐
│  📅 Dönem: [01.01.2026] - [31.01.2026]   🚛 Araç: [Tümü ▾]    │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ Yakıt       │ │ Toplam      │ │ Ort. Fiyat  │ │ KM Başı   │ │
│  │ Maliyeti    │ │ Litre       │ │             │ │ Maliyet   │ │
│  │ 125,430 TL  │ │ 3,245 L     │ │ 38.65 TL/L  │ │ 2.78 TL   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │           📈 Aylık Maliyet Trendi (12 Ay)                 ││
│  │   ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓     ││
│  └────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### API Response Mapping (Maliyet)

| UI Element | API Field |
|------------|-----------|
| Yakıt Maliyeti | `toplam_maliyet` |
| Toplam Litre | `toplam_litre` |
| Ort. Fiyat | `ortalama_fiyat` |
| KM Başı Maliyet | `km_basi_maliyet` |

---

## Tab 3: Tasarruf & ROI

### Tasarruf Potansiyeli

```
┌─────────────────────────────────────────────────────────────────┐
│  Hedef Tüketim: [────────●──────] 30.0 L/100km                 │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Mevcut     │ Hedef      │ Tasarruf    │ Yıllık            │ │
│  │ 35.2 L/100 │ 30.0 L/100 │ 12,500 TL   │ 150,000 TL        │ │
│  │            │            │ (%14.8)     │                    │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Tab 3: Tasarruf & ROI (Smart Simulator)

- **Interactive ROI**: Kullanıcı "Yatırım Tutarı" sliderını hareket ettirdikçe, sistem anlık olarak "Geri Ödeme Süresi" ve "ROI Yüzdesi"ni (AI bazlı tasarruf verisiyle) yeniden hesaplar.
- **Visual Feedback**: ROI %100'ü geçtiğinde kartta premium bir "Zirve" efekti oluşur.

### Premium Report Previews
- **PDF Cards**: Her rapor kartında, raporun içeriğini temsil eden mini bir "Glassmorphism Thumbnail" (önizleme) gösterilir.
- **Export Progress**: PDF oluşturulurken lineer premium progress bar ve "Hazırlanıyor..." micro-interaction gösterilir.

---

## API (Backend Doğrulanmış ✅)

```
# PDF Raporlar
GET /api/v1/advanced-reports/pdf/fleet-summary?start_date=2026-01-01&end_date=2026-01-31
Response: PDF binary (Content-Type: application/pdf)
Headers: {
    Content-Disposition: attachment; filename="filo_ozet_2026-01-01_2026-01-31.pdf"
}

GET /api/v1/advanced-reports/pdf/vehicle/{id}?month=1&year=2026
Response: PDF binary

GET /api/v1/advanced-reports/pdf/driver-comparison
Response: PDF binary

# Maliyet Analizi (CostBreakdownResponse)
GET /api/v1/advanced-reports/cost/period?start_date=2026-01-01&end_date=2026-01-31&arac_id=5
Response: {
    fuel_cost: 125430.50,
    fuel_liters: 3245.5,
    avg_price_per_liter: 38.65,
    trip_count: 45,
    total_distance: 45123.0,
    cost_per_km: 2.78,
    period_start: "2026-01-01",
    period_end: "2026-01-31"
}

# Maliyet Trend (12 Ay)
GET /api/v1/advanced-reports/cost/trend?months=12
Response: [
    { month: "2026-01", cost: 125430.50, liters: 3245.5 },
    { month: "2025-12", cost: 118920.00, liters: 3120.0 },
    ...
]

# Tasarruf Potansiyeli (SavingsPotentialResponse)
GET /api/v1/advanced-reports/cost/savings-potential?target_consumption=30
Response: {
    current_consumption: 35.2,
    target_consumption: 30.0,
    current_cost: 125430.50,
    target_cost: 106890.00,
    potential_savings: 18540.50,
    savings_percentage: 14.8,
    annual_projection: 222486.00
}

# ROI Hesaplama (ROIResponse)
GET /api/v1/advanced-reports/cost/roi?investment=50000&months=12
Response: {
    investment: 50000,
    monthly_savings: 18540.50,
    annual_savings: 222486.00,
    payback_months: 2.7,
    annual_roi_percentage: 344.97,
    cost_improvement_pct: 14.8
}

# Araç Maliyet Karşılaştırması
GET /api/v1/advanced-reports/cost/vehicle-comparison?months=3
Response: [
    { arac_id: 1, plaka: "34ABC123", total_cost: 45000.50, cost_per_km: 2.65 },
    ...
]

# Excel Template
GET /api/v1/advanced-reports/excel/template/{entity_type}
# entity_type: yakit, sefer, arac, sofor
Response: Excel binary
```

---

## Response Field Mapping (Tasarruf - SavingsPotentialResponse)

| API Field | UI Element |
|-----------|------------|
| `current_consumption` | Mevcut değer |
| `target_consumption` | Hedef değer (slider ile set) |
| `potential_savings` | Aylık tasarruf kartı |
| `annual_projection` | Yıllık tasarruf kartı |
| `savings_percentage` | Yüzde badge |

---

## PDF Download Handling

```javascript
// PDF indirme
const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` }
});

const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = response.headers.get('Content-Disposition')
    ?.split('filename=')[1] || 'rapor.pdf';
a.click();
```

---

## States

| Durum | Görünüm |
|-------|---------|
| Loading | Skeleton kartlar |
| Generating | Progress bar + "Rapor hazırlanıyor..." |
| Error | Error toast + Retry |
| Empty | "Bu dönem için veri bulunamadı" |
