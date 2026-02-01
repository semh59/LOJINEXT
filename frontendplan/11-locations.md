# 11 - Güzergahlar (Locations)

> Sık kullanılan güzergahların yönetimi ve analizi
> **Backend Senkronizasyonu:** ✅ Güncel (2026-01-30)

---

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│                             Güzergahlar                              │
├──────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 🔍 Ara...              │ Zorluk: [Tümü ▾] │ [+ Yeni Güzergah] │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ ÇIKIŞ    │ VARIŞ    │ MESAFE │ SÜRE  │ ZORLUK   │ TIRM.│ İNİŞ │⋮││
│  ├──────────┼──────────┼────────┼───────┼──────────┼──────┼──────┼─┤│
│  │ Ankara   │ İstanbul │ 450 km │ 5.5 s │ 🟢 Düz   │ 200m │ 180m │⋮││
│  │ İzmir    │ Antalya  │ 480 km │ 6.0 s │ 🟡 Eğimli│ 950m │ 800m │⋮││
│  │ Trabzon  │ Erzurum  │ 320 km │ 5.0 s │ 🔴 Dağlık│1500m │ 400m │⋮││
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Tablo Kolonları (API Field Mapping)

| Kolon | Width | API Field | Format |
|-------|-------|-----------|--------|
| Çıkış | 100px | `cikis_yeri` | Şehir |
| Varış | 100px | `varis_yeri` | Şehir |
| Mesafe | 80px | `mesafe_km` | X km |
| Süre | 70px | `tahmini_sure_saat` | X.X s |
| Zorluk | 100px | `zorluk` | Badge |
| Tırmanış | 70px | `ascent_m` | Xm |
| İniş | 70px | `descent_m` | Xm |
| ⋮ | 40px | - | Menu |

---

## Zorluk Badge (Backend ile Eşleştirilmiş)

| Zorluk | API Value | Icon | BG | Text |
|--------|-----------|------|-----|------|
| Düz | `Normal` | 🟢 | `#D1FAE5` | `#059669` |
| Hafif Eğimli | `Orta` | 🟡 | `#FEF3C7` | `#D97706` |
| Dik/Dağlık | `Zor` | 🔴 | `#FEE2E2` | `#DC2626` |

---

## Modal: Yeni Güzergah

### Form Fields (Backend ile Eşleştirilmiş)

| Alan | Tip | API Field | Kural |
|------|-----|-----------|-------|
| Çıkış Yeri* | Input | `cikis_yeri` | Max 100 |
| Varış Yeri* | Input | `varis_yeri` | Max 100 |
| Mesafe (km)* | Number | `mesafe_km` | > 0 |
| Tahmini Süre | Number | `tahmini_sure_saat` | 0-48 saat |
| Zorluk | Select | `zorluk` | Normal, Orta, Zor |
| Tırmanış (m) | Number | `ascent_m` | 0-10000 |
| İniş (m) | Number | `descent_m` | 0-10000 |
| Notlar | Textarea | `notlar` | Max 500 |

### Koordinatlar (Opsiyonel - Collapsible)

| Alan | API Field | Açıklama |
|------|-----------|----------|
| Çıkış Lat | `cikis_lat` | -90 to 90 |
| Çıkış Lon | `cikis_lon` | -180 to 180 |
| Varış Lat | `varis_lat` | -90 to 90 |
| Varış Lon | `varis_lon` | -180 to 180 |

---

## Actions

| Item | Icon | Açıklama |
|------|------|----------|
| Analiz Et | BarChart | OpenRouteService ile analiz |
| Düzenle | Pencil | Modal |
| Sil | Trash2 | Soft delete |

---

## 🏔️ Smart Route Analysis

### Elevation Profile Visualization
- **Graph**: Analiz modali içinde, güzergahın "Yükseklik Profili" (Elevation Chart) premium bir line chart olarak gösterilir.
- **Smart Difficulty**: Zorluk derecesi sadece statik veriye göre değil, toplam tırmanış/iniş oranına göre sistem tarafından akıllı hesaplanır (Auto-Difficulty).

### Auto-Difficulty Calculation (Backend)
```
if ascent_m < 300: zorluk = "Normal"
elif ascent_m < 800: zorluk = "Orta"  
else: zorluk = "Zor"
```

### Integrated Ops
- **Fetch & Fill**: "Analiz Et" tıklandığında OpenRouteService'den gelen Mesafe, Süre ve Tırmanış verileri forma otomatik "Smart Fill" (akıllı doldurma) ile yansıtılır.
- **API Mesafe**: ORS'den gelen mesafe `api_mesafe_km` alanına kaydedilir
- **Custom Icons**: Zorluk badge'lerinde düz yol için `Wind`, engebeli için `TrendingUp`, dağlık için `Mountain` ikonları kullanılır.

### Fuzzy Location Matching (Backend)
- Backend `difflib` ile benzer lokasyon isimlerini eşleştirir
- Typo toleransı: %60 benzerlik yeterli
- Bulk import sırasında N+1 query önleme için pre-fetch yapılır

---

## API (Backend Doğrulanmış ✅)

```
# Güzergah Listesi (LokasyonResponse array)
GET /api/v1/locations?zorluk=Zor&skip=0&limit=100
# NOT: search parametresi yok
Response: [
    {
        id: 1,
        cikis_yeri: "Ankara",
        varis_yeri: "İstanbul",
        mesafe_km: 450,
        tahmini_sure_saat: 5.5,
        zorluk: "Normal",
        ascent_m: 200,
        descent_m: 180,
        cikis_lat: 39.9334,
        cikis_lon: 32.8597,
        varis_lat: 41.0082,
        varis_lon: 28.9784,
        api_mesafe_km: 452,
        api_sure_saat: 5.3,
        tahmini_yakit_lt: 144.0,
        last_api_call: "2026-01-28T10:00:00Z",
        notlar: ""
    },
    ...
]
# NOT: Backend düz array döner, items/total wrapper YOK

# Güzergah Ekle
POST /api/v1/locations
Body: {
    cikis_yeri: "Bursa",
    varis_yeri: "Antalya",
    mesafe_km: 480,
    tahmini_sure_saat: 6.0,
    zorluk: "Orta",
    ascent_m: 950,
    descent_m: 800
}
Response: { id: 46, ... }

# Güzergah Güncelle
PUT /api/v1/locations/{id}
Body: { mesafe_km: 485, ... }

# Güzergah Sil
DELETE /api/v1/locations/{id}

# OpenRouteService Analizi
POST /api/v1/locations/{id}/analyze
Response: {
    success: true,
    api_mesafe_km: 452,
    api_sure_saat: 5.3,
    ascent_m: 215,
    descent_m: 190,
    elevation_profile: [
        { distance_km: 0, elevation_m: 850 },
        { distance_km: 50, elevation_m: 920 },
        ...
    ]
}

# Rota ile Arama (Sefer formu için)
GET /api/v1/locations/search/by-route?cikis=Ankara&varis=Istanbul
Response: {
    found: true,
    location: { ... }
}

# Benzersiz Lokasyonlar (Autocomplete için)
GET /api/v1/locations/unique-names
Response: ["Ankara", "İstanbul", "İzmir", ...]
```

---

## States

| Durum | Görünüm |
|-------|---------|
| Loading | Skeleton rows |
| Empty | "Henüz güzergah eklenmedi" + CTA |
| Error | Error banner + Retry |
| Analyzing | Spinner + "Analiz ediliyor..." |
