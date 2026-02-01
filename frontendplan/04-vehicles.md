# 04 - Araçlar

> Filo araçlarının listelenmesi ve yönetimi (CRUD + Excel Import)
> **Backend Senkronizasyonu:** ✅ Güncel (2026-01-30)

---

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│                               Araçlar                                │
├──────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ 🔍 Ara...       │ ☑ Sadece Aktif │ [📤 Excel] [+ Yeni Araç]  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ PLAKA    │ MARKA    │ MODEL  │ YIL │ TANK │ HEDEF │ DURUM │⋮  │  │
│  ├──────────┼──────────┼────────┼─────┼──────┼───────┼───────┼───┤  │
│  │ 34ABC123 │ Mercedes │ Actros │2022 │ 600L │ 32.0  │  ✅   │ ⋮ │  │
│  │ 06DEF456 │ Volvo    │ FH16   │2021 │ 700L │ 30.0  │  ✅   │ ⋮ │  │
│  │ 35GHI789 │ Scania   │ R500   │2023 │ 650L │ 31.5  │  ❌   │ ⋮ │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ← Önceki   Sayfa 1 / 5   Sonraki →                                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Toolbar

| Element | Stil |
|---------|------|
| Container | bg white, padding 16px, radius 8px, shadow |
| Search | 280px width, icon sol |
| Toggle | "Sadece Aktif", default ON |
| Excel Button | Secondary, icon Upload |
| Add Button | Primary, icon Plus |

---

## Tablo

### Header

| Özellik | Değer |
|---------|-------|
| Background | `#F1F5F9` (subtle contrast) |
| Text | 12px, 600, uppercase, `#475569` |
| Padding | 16px |

### Kolonlar (API Field Mapping)

| Kolon | Width | API Field | Align |
|-------|-------|-----------|-------|
| Plaka | 120px | `plaka` | left |
| Marka | 100px | `marka` | left |
| Model | 100px | `model` | left |
| Yıl | 60px | `yil` | center |
| Tank | 80px | `tank_kapasitesi` | right |
| Hedef | 80px | `hedef_tuketim` | right |
| Durum | 80px | `aktif` | center |
| İşlemler | 60px | - | center |

### Row

| Özellik | Değer |
|---------|-------|
| Padding | 16px |
| Border | 1px solid `#F1F5F9` |
| Hover | `#F1F5F9` |

### Durum Badge

| Durum | BG | Text |
|-------|-----|------|
| Aktif | `#D1FAE5` | `#059669` |
| Pasif | `#FEE2E2` | `#DC2626` |

### Actions Dropdown

| Item | Icon | Color |
|------|------|-------|
| Düzenle | Pencil | default |
| Detay | Eye | default |
| Sil | Trash2 | `#EF4444` |

---

## Modal: Yeni/Düzenle Araç

### Container

| Özellik | Değer |
|---------|-------|
| Width | 640px |
| Radius | 16px |
| Padding | 32px |

### Form Fields (Backend ile Eşleştirilmiş)

| Alan | Tip | API Field | Validation |
|------|-----|-----------|------------|
| Plaka* | Input | `plaka` | `^[0-9]{2}[A-Z]{1,3}[0-9]{2,4}$` |
| Marka* | Input | `marka` | min 2, max 50 |
| Model | Input | `model` | max 50 |
| Yıl | Number | `yil` | 1990 - now+1 |
| Tank | Number + "L" | `tank_kapasitesi` | 1-5000, default 600 |
| Hedef | Number + "L/100km" | `hedef_tuketim` | 1-100, default 32 |
| Notlar | Textarea | `notlar` | max 500 |

### Fizik Parametreleri (Collapsible - Advanced)

| Alan | API Field | Default | Açıklama |
|------|-----------|---------|----------|
| Boş Ağırlık (kg) | `bos_agirlik_kg` | 8000 | Aracın boş ağırlığı |
| Hava Direnci (Cd) | `hava_direnc_katsayisi` | 0.7 | Aerodinamik katsayı |
| Ön Kesit Alanı (m²) | `on_kesit_alani_m2` | 8.5 | Ön cephe alanı |
| Motor Verimi | `motor_verimliligi` | 0.38 | 0-1 arası |
| Lastik Direnci | `lastik_direnc_katsayisi` | 0.007 | Yuvarlanma katsayısı |
| Max Yük (kg) | `maks_yuk_kapasitesi_kg` | 26000 | Maksimum taşıma |

### Layout

- 1 column: Plaka, Marka, Model, Notlar
- 2 column: Yıl + Tank, Hedef + (empty)
- Collapsible: Fizik Parametreleri

### Footer

| Button | Position |
|--------|----------|
| İptal | Left, secondary |
| Kaydet | Right, primary |

---

## 🧠 Smart UI & Ops Logic

### Optimistic UI (Fast Response)
- **Delete**: Kullanıcı "Sil"e bastığı anda, API yanıtı beklenmeden satır DOM'dan kaldırılır. Hata durumunda ("Rollback") satır geri getirilir ve kullanıcı Toast ile uyarılır.
- **Update**: Düzenleme sonrası modal kapandığı anda listedeki veri güncellenir.

### Smart Validation: Plaka
- **Regex**: `^(0[1-9]|[1-7][0-9]|8[0-1])\s?[A-Z]{1,3}\s?(0[1-9]|[1-9][0-9]{1,3})$`
- **Format**: `34 ABC 123` (Boşluklu veya bitişik kabul edilir, backend'e normalize edilip gönderilir).
- **Duplicate Check**: Backend TOCTOU korumalı plaka benzersizlik kontrolü yapar

### Euro Sınıfı (Otomatik Hesaplama)
- Backend araç yılından Euro sınıfını otomatik hesaplar
- UI'da read-only olarak gösterilebilir

### Skeleton Loading
- **Structure**: Tablo yüklenirken kolon genişliklerine sadık kalan, "Shimmer" efektli skeleton satırları gösterilir.
- **Duration**: Minimum 300ms (UX için sıçramayı önler).

---

## Excel Upload Modal

| Element | Stil |
|---------|------|
| Dropzone | Dashed border, 200px height |
| Icon | Cloud Upload, 48px |
| Text | "Dosyayı sürükleyin veya seçin" |
| Subtext | "Max 10MB, .xlsx/.xls" |
| Progress | Linear bar, `#3B82F6` |
| Success | ✅ X kayıt eklendi |
| Errors | ⚠️ Y hata (list) |

---

## API (Backend Doğrulanmış ✅)

```
# Araç Listesi
GET /api/v1/vehicles?aktif_only=true&skip=0&limit=100&search=mercedes
# Ek Filtreler: marka, model, min_yil, max_yil
Response: [
    {
        id: 1,
        plaka: "34ABC123",
        marka: "Mercedes",
        model: "Actros",
        yil: 2022,
        tank_kapasitesi: 600,
        hedef_tuketim: 32.0,
        bos_agirlik_kg: 8000,
        hava_direnc_katsayisi: 0.7,
        on_kesit_alani_m2: 8.5,
        motor_verimliligi: 0.38,
        lastik_direnc_katsayisi: 0.007,
        maks_yuk_kapasitesi_kg: 26000,
        aktif: true,
        notlar: "",
        created_at: "2026-01-15T10:30:00Z"
    },
    ...
]
# NOT: Backend düz array döner, items/total wrapper YOK

# Araç Ekle
POST /api/v1/vehicles
Body: {
    plaka: "34XYZ789",
    marka: "Volvo",
    model: "FH16",
    yil: 2023,
    tank_kapasitesi: 700,
    hedef_tuketim: 30.0,
    ...
}
Response: { id: 26, ... }

# Araç Güncelle
PUT /api/v1/vehicles/{id}
Body: { marka: "Mercedes-Benz", ... }

# Araç Sil (Soft Delete)
DELETE /api/v1/vehicles/{id}

# Excel Upload (Chunked - Max 10MB)
POST /api/v1/vehicles/upload
Content-Type: multipart/form-data
Response: {
    success: true,
    inserted: 15,
    updated: 3,
    errors: [
        { row: 5, field: "plaka", message: "Geçersiz plaka formatı" }
    ]
}

# Araç Detay (İstatistiklerle)
GET /api/v1/vehicles/{id}/stats
Response: {
    ...vehicle_data,
    toplam_sefer: 145,
    toplam_km: 45678,
    ort_tuketim: 33.2
}
```

---

## Animasyonlar

| Element | Animation |
|---------|-----------|
| Table rows | Staggered fade (30ms) |
| Modal | Scale 0.95→1, 200ms |
| Dropdown | Slide down, 150ms |
| Delete | Slide left out, 200ms |
