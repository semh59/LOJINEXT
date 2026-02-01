# 07 - Yakıt Kayıtları

> Yakıt alım/fiş kayıtlarının takibi ve yönetimi
> **Backend Senkronizasyonu:** ✅ Güncel (2026-01-30)

---

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│                           Yakıt Kayıtları                            │
├──────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │📅 [01.01] - [31.01]│ Durum: [Tümü ▾]│ [📤 Excel] [+ Yeni]    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │TARİH│ARAÇ   │İSTASYON│LİTRE│FİYAT│TOPLAM│KM   │DEPO │DURUM│⋮ │  │
│  ├─────┼───────┼────────┼─────┼─────┼──────┼─────┼─────┼─────┼──┤  │
│  │25.01│34ABC12│Shell   │450L │42.50│19,125│45000│Doldu│ ⏳  │⋮ │  │
│  │24.01│06DEF45│Opet    │380L │41.80│15,884│62000│Kısmi│ ✅  │⋮ │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Toolbar

| Element | Açıklama |
|---------|----------|
| Date Range | Tarih filtresi |
| Durum Filter | Bekliyor, Onaylandı, Reddedildi, Tümü |
| Excel | Secondary |
| Yeni Kayıt | Primary |

---

## Tablo Kolonları (API Field Mapping)

| Kolon | Width | API Field | Format |
|-------|-------|-----------|--------|
| Tarih | 80px | `tarih` | 25.01.2026 |
| Araç | 90px | `plaka` (join) | Plaka |
| İstasyon | 100px | `istasyon` | Text |
| Litre | 70px | `litre` | X L |
| Birim Fiyat | 70px | `fiyat_tl` | X.XX TL |
| Toplam | 90px | `toplam_tutar` | X,XXX TL |
| KM Sayaç | 70px | `km_sayac` | Number |
| Fiş No | 80px | `fis_no` | Text |
| Depo | 70px | `depo_durumu` | Badge |
| Durum | 80px | `durum` | Badge |
| ⋮ | 40px | - | Menu |

---

## Badges

### Depo Durumu (Backend ile Eşleştirilmiş)

| Durum | API Value | BG | Text |
|-------|-----------|-----|------|
| Doldu | `Doldu` | `#D1FAE5` | `#059669` |
| Kısmi | `Kısmi` | `#FEF3C7` | `#D97706` |
| Bilinmiyor | `Bilinmiyor` | `#F1F5F9` | `#64748B` |

### Onay Durumu (Backend ile Eşleştirilmiş)

| Durum | API Value | BG | Text |
|-------|-----------|-----|------|
| Onaylandı | `Onaylandı` | `#D1FAE5` | `#059669` |
| Bekliyor | `Bekliyor` | `#FEF3C7` | `#D97706` |
| Reddedildi | `Reddedildi` | `#FEE2E2` | `#DC2626` |

---

## Modal: Yeni Yakıt Kaydı

### Form Fields (Backend ile Eşleştirilmiş)

| Alan | Tip | API Field | Validation |
|------|-----|-----------|------------|
| Tarih* | Date | `tarih` | Required |
| Araç* | Select | `arac_id` | Required |
| İstasyon | Input | `istasyon` | Max 100 |
| Litre* | Number | `litre` | 0.01-10000 |
| Birim Fiyat* | Number | `fiyat` | 0.01-1000 TL |
| Toplam Tutar | Number | (auto-calc) | Display only |
| KM Sayaç* | Number | `km_sayac` | 1-9999999 |
| Fiş No | Input | `fis_no` | Max 50 |
| Depo Durumu | Select | `depo_durumu` | Bilinmiyor/Doldu/Kısmi |

### Smart Calculations & Guards

- **Efficiency Guard**: Girilen litre ve KM farkı, aracın hedef tüketiminden %20+ sapıyorsa "Yüksek Tüketim Olabilir" uyarısı verir.
- **Auto-Total**: Litre veya Birim Fiyat değiştiğinde Toplam Tutar, kuruşu kuruşuna anlık hesaplanır.
- **Z-Score Anomaly**: Backend anomali tespiti yapar, kritik durumlar için alert oluşturur.

### KM Monotonicity Check (Backend)
- Backend her yakıt kaydında KM sayacının önceki değerden büyük olduğunu kontrol eder
- Hatalı KM girişleri uyarı üretir

### Periyot Hesaplaması (Backend)
- Yakıt alımları arasındaki periyotlar otomatik hesaplanır
- Tüketim değerleri seferlere dağıtılır

### Onay Mekanizması (Admin Smart Action)
- **Quick Approve**: Bekleyen kayıtlarda sağ tık veya hızlı işlem butonu ile Optimistic onay verilebilir.
- **Duplicate Check**: Aynı gün, aynı araç için mükerrer olabilecek benzer litre kayıtları sistem tarafından kırmızı ile vurgulanır.

---

## Actions Dropdown

| Item | Icon | API Endpoint | Açıklama |
|------|------|--------------|----------|
| Onayla | Check | `PUT /{id}` durum=Onaylandı | Durum = Onaylandı |
| Düzenle | Pencil | - | Modal |
| Reddet | X | `PUT /{id}` durum=Reddedildi | Durum = Reddedildi |
| Sil | Trash2 | `DELETE /{id}` | Soft delete |

---

## API (Backend Doğrulanmış ✅)

```
# Yakıt Listesi
GET /api/v1/fuel?skip=0&limit=100
# NOT: arac_id filtresi şu anda backend'de yok, sadece skip/limit
Response: [
    {
        id: 1,
        tarih: "2026-01-25",
        arac_id: 5,
        istasyon: "Shell",
        fiyat_tl: 42.50,
        litre: 450.00,
        toplam_tutar: 19125.00,
        km_sayac: 45000,
        fis_no: "SH-123456",
        depo_durumu: "Doldu",        // "Bilinmiyor" | "Doldu" | "Kısmi"
        durum: "Bekliyor",           // "Bekliyor" | "Onaylandı" | "Reddedildi"
        created_at: "2026-01-25T10:00:00Z"
    },
    ...
]
# NOT: Backend düz array döner, items/total wrapper YOK
# NOT: plaka bilgisi için ayrıca /vehicles/{arac_id} çağrılmalı

# Yakıt Ekle
POST /api/v1/fuel
Body: {
    tarih: "2026-01-30",
    arac_id: 5,
    istasyon: "Opet",
    fiyat_tl: 41.80,          // NOT: fiyat değil fiyat_tl
    litre: 380.00,
    toplam_tutar: 15884.00,   // ZORUNLU (backend şemasında required)
    km_sayac: 46200,
    fis_no: "OP-789012",
    depo_durumu: "Kısmi"
}
Response: { id: 157, ... }

# Yakıt Güncelle
PUT /api/v1/fuel/{id}
Body: { durum: "Tamam", ... }

# Yakıt Sil (Soft Delete)
DELETE /api/v1/fuel/{id}

# Excel Upload (Rate Limited, Chunked)
POST /api/v1/fuel/upload
Content-Type: multipart/form-data
Header: (Rate limit: see trips)
Response: {
    success: true,
    inserted: 23,
    errors: [...]
}

# Araç Son KM (Validation için)
GET /api/v1/vehicles/{id}/last-km
Response: { last_km: 45000 }

# Yakıt Periyotları
GET /api/v1/fuel/periods?arac_id=5&limit=20
Response: {
    items: [
        {
            id: 1,
            alim1_tarih: "2026-01-20",
            alim2_tarih: "2026-01-25",
            ara_mesafe: 1200,
            toplam_yakit: 450,
            ort_tuketim: 37.5
        },
        ...
    ]
}
```

---

## States

| Durum | Görünüm |
|-------|---------|
| Loading | Skeleton rows |
| Empty | "Henüz yakıt kaydı yok" + CTA |
| Error | Error banner + Retry |
