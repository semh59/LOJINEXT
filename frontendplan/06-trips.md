# 06 - Seferler

> Sefer kayıtlarının listelenmesi ve yönetimi
> **Backend Senkronizasyonu:** ✅ Güncel (2026-01-30)

---

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│                               Seferler                               │
├──────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ 📅 Tarih: [01.01] - [31.01] │ [📤 Excel] [+ Yeni Sefer]       │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │TARİH│SAAT│ARAÇ    │ŞOFÖR    │ÇIKIŞ  │VARIŞ  │KM │TON│TÜKETİM│⋮│  │
│  ├─────┼────┼────────┼─────────┼───────┼───────┼───┼───┼───────┼─┤  │
│  │25.01│08:30│34ABC12│A.Yılmaz │Ankara │İstanbul│450│18 │32.5   │⋮│  │
│  │24.01│14:00│06DEF45│M.Kaya   │İzmir  │Ankara │580│22 │ -     │⋮│  │
│  │24.01│09:15│35GHI78│A.Demir  │Bursa  │Antalya│480│15 │34.1   │⋮│  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Toolbar

| Element | Açıklama |
|---------|----------|
| Date Range | Başlangıç - Bitiş tarih picker |
| Durum Filter | Tamam, Devam Ediyor, İptal, Tümü |
| Excel | Secondary button |
| Yeni Sefer | Primary button |

---

## Tablo Kolonları (API Field Mapping)

| Kolon | Width | API Field | Format |
|-------|-------|-----------|--------|
| Tarih | 80px | `tarih` | 25.01.2026 |
| Saat | 60px | `saat` | 08:30 |
| Araç | 90px | `plaka` (join) | Plaka |
| Şoför | 100px | `sofor_adi` (join) | Ad Soyad |
| Çıkış | 80px | `cikis_yeri` | Şehir |
| Varış | 80px | `varis_yeri` | Şehir |
| Mesafe | 60px | `mesafe_km` | X km |
| Yük | 50px | `net_kg` / 1000 | X ton |
| Tüketim | 70px | `tuketim` | X.X L/100km veya "-" |
| Durum | 80px | `durum` | Badge |
| ⋮ | 40px | - | Menu |

---

## Durum Badge (Backend ile Eşleştirilmiş)

| Durum | API Value | Icon | BG | Text |
|-------|-----------|------|-----|------|
| Tamam | `Tamam` | ✅ | `#D1FAE5` | `#059669` |
| Devam Ediyor | `Devam Ediyor` | ⏳ | `#FEF3C7` | `#D97706` |
| İptal | `İptal` | ❌ | `#FEE2E2` | `#DC2626` |

---

## Modal: Yeni Sefer

### Form - Sol Kolon

| Alan | Tip | API Field |
|------|-----|-----------|
| Tarih* | Date Picker | `tarih` |
| Saat | Time Picker | `saat` |
| Araç* | Select (aktif araçlar) | `arac_id` |
| Şoför* | Select (aktif şoförler) | `sofor_id` |

### Form - Sağ Kolon

| Alan | Tip | API Field |
|------|-----|-----------|
| Çıkış Yeri* | Input | `cikis_yeri` |
| Varış Yeri* | Input | `varis_yeri` |
| Mesafe (km)* | Number | `mesafe_km` |
| Net Yük (kg) | Number | `net_kg` |

### Form - Alt (Full Width)

| Alan | Tip | API Field |
|------|-----|-----------|
| Boş Sefer | Checkbox | `bos_sefer` (0 veya 1) |
| Tırmanış (m) | Number | `ascent_m` |
| İniş (m) | Number | `descent_m` |
| Durum | Select | `durum` |

---

## Select Dropdown (Araç/Şoför)

```
┌────────────────────────┐
│ 🔍 Ara...              │
├────────────────────────┤
│ 🚛 34ABC123 - Mercedes │
│ 🚛 06DEF456 - Volvo    │
│ 🚛 35GHI789 - Scania   │
└────────────────────────┘
```

| Stil | Değer |
|------|-------|
| Search | Üstte, sticky |
| Item Height | 40px |
| Icon | Truck/User, 16px |
| Hover | `#F1F5F9` |

---

## 🧠 Smart UI & Ops Logic

### Smart KM Validation
- **Sequence Check**: Seferin "Başlangıç KM"si, aracın sistemdeki "Son KM"si ile uyumlu değilse uyarı verir.
- **Bitiş KM**: Bitiş KM < Başlangıç KM girişi anında engellenir.
- **Efficiency Warning**: Gelen KM ve yük verisine göre "Anormal Tüketim" ihtimali varsa modalda uyarı çıkarır.

### Passive Safety Rules (Backend Tarafında)
- Backend sefer kaydederken pasif güvenlik kontrolleri yapar
- Anormal değerler loglanır ve alert oluşturulabilir

### Optimistic UI
- **Add Trip**: Kaydet butonuna basıldığı an sefer listeye en üste eklenir. API hatasında rollback yapılır.
- **Status Change**: Durum değişikliği (Tamam/İptal) anında badge üzerinde yansıtılır.

### Tüketim Hesaplaması
- **Backend**: Yakıt periyodu kapandığında tüketim otomatik hesaplanır
- **Display**: Henüz hesaplanmamış seferler için "-" gösterilir

### Resilient Loading
- **Skeleton**: Tablo yüklenirken araç plakası ve güzergah bölgeleri için özel tasarlanmış skeletonlar kullanılır.

---

## API (Backend Doğrulanmış ✅)

```
# Sefer Listesi
GET /api/v1/trips?skip=0&limit=100&baslangic_tarih=2026-01-01&bitis_tarih=2026-01-31&durum=Tamam
# Ek Filtreler: arac_id, sofor_id
Response: [
    {
        id: 1,
        tarih: "2026-01-25",
        saat: "08:30",
        arac_id: 5,
        plaka: "34ABC123",      // joined/computed
        sofor_id: 3,
        sofor_adi: "Ahmet Yılmaz",  // joined/computed
        cikis_yeri: "Ankara",
        varis_yeri: "İstanbul",
        mesafe_km: 450,
        net_kg: 18000,
        ton: 18.0,
        bos_sefer: false,
        ascent_m: 500,
        descent_m: 300,
        baslangic_km: 100000,
        bitis_km: 100450,
        tuketim: 32.5,          // null if not calculated yet
        dagitilan_yakit: 146.25,
        durum: "Tamam",         // "Tamam" | "Devam Ediyor" | "İptal"
        created_at: "2026-01-25T08:30:00Z"
    },
    ...
]
# NOT: Backend düz array döner, items/total wrapper YOK

# Sefer Ekle
POST /api/v1/trips
Body: {
    tarih: "2026-01-30",
    saat: "14:00",
    arac_id: 5,
    sofor_id: 3,
    cikis_yeri: "İzmir",
    varis_yeri: "Ankara",
    mesafe_km: 580,
    net_kg: 22000,
    bos_sefer: 0,
    ascent_m: 800,
    descent_m: 600
}
Response: { id: 1235, ... }

# Sefer Güncelle
PUT /api/v1/trips/{id}
Body: { durum: "Tamam", ... }

# Sefer Sil (Soft Delete)
DELETE /api/v1/trips/{id}

# Excel Upload (Chunked - Max 10MB, Rate Limited)
POST /api/v1/trips/upload
Content-Type: multipart/form-data
Response: {
    success: true,
    inserted: 45,
    errors: [...]
}

# Bugünün Seferleri (Dashboard için)
GET /api/v1/trips/today
Response: { items: [...], total: 5 }
```

---

## Validations

| Alan | Kural |
|------|-------|
| Mesafe | 1-10000 |
| Net Yük | 0-50000 kg |
| Tarih | Required, ISO format |
| Araç/Şoför | Required, must exist |

---

## Animasyonlar

| Element | Animation |
|---------|-----------|
| Table rows | Staggered fade (30ms) |
| Modal | Scale 0.95→1, 200ms |
| Status change | Color transition 200ms |
