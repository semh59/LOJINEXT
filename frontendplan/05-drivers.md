# 05 - Sürücüler

> Şoför kadrosunun listelenmesi ve yönetimi
> **Backend Senkronizasyonu:** ✅ Güncel (2026-01-30)

---

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│                              Sürücüler                               │
├──────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ 🔍 Ara...       │ ☑ Sadece Aktif │ [📤 Excel] [+ Yeni Şoför] │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ AD SOYAD   │ TELEFON     │ EHLİYET │ PUAN │ DURUM │ İŞLEM     │  │
│  ├────────────┼─────────────┼─────────┼──────┼───────┼───────────┤  │
│  │ Ahmet Yılmaz│ 532 *** 45 │ E       │ ★★★★☆│  ✅   │ ⋮         │  │
│  │ Mehmet Kaya │ 545 *** 12 │ E       │ ★★★☆☆│  ✅   │ ⋮         │  │
│  │ Ali Demir   │ 554 *** 78 │ C       │ ★★★★★│  ❌   │ ⋮         │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ← Önceki   Sayfa 1 / 3   Sonraki →                                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Tablo Kolonları

| Kolon | Width | Açıklama |
|-------|-------|----------|
| Ad Soyad | 150px | Tam isim |
| Telefon | 120px | Maskelenmiş: 532 *** 45 |
| İşe Başlama | 100px | Tarih formatı |
| Ehliyet | 60px | B, C, D, E, G |
| Puan | 100px | Yıldız gösterimi (1-5) |
| Durum | 80px | Aktif/Pasif badge |
| İşlemler | 80px | Dropdown menu |

---

## Puan Gösterimi (Backend Hibrit Skor Sistemi)

### Yıldız Display

```
★★★★☆  4.0
```

> **ÖNEMLİ:** Backend'de `score` alanı hibrit hesaplanır:
> - %60 Performans (sefer verilerinden)
> - %40 Manuel değerlendirme

| API Score | Yıldız | Görünüm | Renk |
|-----------|--------|---------|------|
| 1.8-2.0 | ★★★★★ | 5 yıldız | `#10B981` |
| 1.5-1.79 | ★★★★☆ | 4 yıldız | `#3B82F6` |
| 1.2-1.49 | ★★★☆☆ | 3 yıldız | `#F59E0B` |
| 0.8-1.19 | ★★☆☆☆ | 2 yıldız | `#EF4444` |
| 0.1-0.79 | ★☆☆☆☆ | 1 yıldız | `#EF4444` |

### Score to Star Mapping Formula
```javascript
const stars = Math.round((score - 0.1) / 0.38); // 0.1-2.0 → 1-5 stars
```

---

## Modal: Yeni/Düzenle Şoför

### Form Fields

| Alan | Tip | API Field | Kural |
|------|-----|-----------|-------|
| Ad Soyad* | Input | `ad_soyad` | Min 3, max 100 |
| Telefon | Input | `telefon` | Format: 0XXX XXX XX XX |
| İşe Başlama | Date Picker | `ise_baslama` | YYYY-MM-DD |
| Ehliyet Sınıfı | Select | `ehliyet_sinifi` | B, C, D, E, G (default: E) |
| Manuel Puan | Slider | `manual_score` | 0.1-2.0 (default: 1.0) |
| Notlar | Textarea | `notlar` | Max 500 |

### Telefon Mask

```
Input:  05321234567
Display: 0532 123 45 67
API:     Maskelenmiş döner
```

---

## Modal: Puan Güncelleme

```
┌──────────────────────────────────────┐
│  Şoför Puanı Güncelle               │
│                                      │
│  Ahmet Yılmaz                        │
│                                      │
│  Manuel Puan: [──────●────] 1.5     │
│                                      │
│  0.1                            2.0  │
│  (Riskli)                (Mükemmel)  │
│                                      │
│  Tahmini Hibrit Puan: 1.42          │
│  (Mevcut: 1.38)                      │
│                                      │
│  [İptal]              [Güncelle]     │
└──────────────────────────────────────┘
```

| Element | Stil |
|---------|------|
| Slider | Range 0.1-2.0, step 0.1 |
| Track | `#E2E8F0`, 8px height |
| Active | `#3B82F6` |
| Thumb | 24px circle, white, shadow |

---

## Actions Dropdown

| Item | Icon | Açıklama |
|------|------|----------|
| Düzenle | Pencil | Modal aç |
| Puan Ver | Star | Puan modal |
| Performans | BarChart | Şoför değerlendirme sayfası |
| Sil | Trash2 | Soft delete (pasife çek) |

---

## 🧠 Smart Scoring & Ops Logic

### Scoring API Interaction (Backend Doğrulanmış)
- **Endpoint**: `POST /api/v1/drivers/{id}/score?score=1.5`
- **Validation**: 0.1 - 2.0 aralığı backend tarafından kontrol edilir
- **Feedback**: Başarılı güncellemede **Green Toast**, hatada **Red Toast** döner

### Hybrid Score Calculation (Backend Tarafında)
- **Logic**: `score = (perf_score * 0.6) + (manual_score * 0.4)`
- **Performance Score**: Son seferlerin ortalama tüketimine göre hesaplanır
- **UI Preview**: Kullanıcı slider ile Manuel puanı değiştirirken, frontend "Tahmini Yeni Puan" simülasyonu yapabilir

### Multiplier Matrix (Tahmin Sisteminde Kullanımı)
- **2.0 Skor (Mükemmel)**: `0.8x` yakıt çarpanı (Yakıt tüketiminde %20'ye varan azalma)
- **1.0 Skor (Nötr)**: `1.0x` çarpan (Standart fizik verisi)
- **0.1 Skor (Riskli)**: `1.2x` yakıt çarpanı (Yakıt tüketiminde %20'ye varan artış)
- **Formula**: `Multiplier = 1.0 + (1.0 - Score) * 0.2`

### Optimistic UI
- **Delete**: Şoför silindiği anda listeden kalkar. Hata durumunda rollback yapılır.
- **PII Protection**: Telefon numaraları listede her zaman maskelenmiş (`532 *** 45`) gösterilir.

---

## API (Backend Doğrulanmış ✅)

```
# Şoför Listesi
GET /api/v1/drivers?aktif_only=true&skip=0&limit=100&search=ahmet
# Ek Filtreler: ehliyet_sinifi, min_score, max_score
Response: [
    {
        id: 1,
        ad_soyad: "Ahmet Yılmaz",
        telefon: "5321234567",      // Ham değer (DB)
        telefon_masked: "532 *** 45",  // Computed field
        ise_baslama: "2023-01-15",
        ehliyet_sinifi: "E",
        manual_score: 1.5,
        score: 1.42,        // Hibrit puan
        aktif: true,
        notlar: "",
        created_at: "2026-01-15T10:30:00Z"
    },
    ...
]
# NOT: Backend düz array döner, items/total wrapper YOK

# Şoför Ekle
POST /api/v1/drivers
Body: {
    ad_soyad: "Yeni Şoför",
    telefon: "5321234567",
    ise_baslama: "2026-01-30",
    ehliyet_sinifi: "E",
    manual_score: 1.0,
    notlar: ""
}
Response: { id: 19, ad_soyad: "Yeni Şoför", ... }

# Şoför Güncelle
PUT /api/v1/drivers/{id}
Body: { ad_soyad: "Güncel İsim", ... }

# Puan Güncelle (Dedicated Endpoint)
POST /api/v1/drivers/{id}/score?score=1.5
Response: { ...SoforResponse }
# Backend SoforResponse döner, güncel tüm şoför bilgisi

# Şoför Sil (Soft Delete - Pasife Çeker)
DELETE /api/v1/drivers/{id}
Response: { status: "success", message: "Şoför pasife çekildi" }

# Excel Template İndir
GET /api/v1/drivers/excel/template

# Excel Upload
POST /api/v1/drivers/excel/upload
Content-Type: multipart/form-data
Response: { status: "success", message: "X şoför yüklendi.", errors: [...] }
```

---

## States

| Durum | Görünüm |
|-------|---------|
| Loading | Skeleton rows |
| Empty | "Henüz şoför eklenmedi" + CTA |
| Error | Error banner + Retry |
