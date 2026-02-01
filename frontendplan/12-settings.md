# 12 - Ayarlar (Settings)

> Sistem konfigürasyonu (Sadece Admin)
> **Backend Senkronizasyonu:** ✅ Güncel (2026-01-30)

---

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│                               Ayarlar                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ ⛽ Filo Ayarları                                                ││
│  │                                                                 ││
│  │  Hedef Tüketim (L/100km)    [32.0    ]                         ││
│  │  Anormal Üst Sınır (%)      [20      ]                         ││
│  │  Anormal Alt Sınır (%)      [20      ]                         ││
│  │                                                                 ││
│  │                                        [Kaydet]                 ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ ⚙️ Sistem                                                       ││
│  │                                                                 ││
│  │  Otomatik Yedekleme         [● Açık]                           ││
│  │  Yedekleme Günü             [Pazar ▾]                          ││
│  │  Zaman Dilimi               [Europe/Istanbul ▾]                ││
│  │                                                                 ││
│  │                                        [Kaydet]                 ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 🎨 Görünüm                                                      ││
│  │                                                                 ││
│  │  Tema                       [● Açık] [○ Koyu]                  ││
│  │                                                                 ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Ayar Grupları (Backend ile Eşleştirilmiş)

### Filo Ayarları

| Ayar | Key | Tip | Default | Validation |
|------|-----|-----|---------|------------|
| Hedef Tüketim | `filo_hedef_tuketim` | Number | 32.0 | 1-100 |
| Anormal Üst Sınır | `anormal_ust_sinir` | Number | 20 | 1-100 |
| Anormal Alt Sınır | `anormal_alt_sinir` | Number | 20 | 1-100 |
| Uzun Periyot Eşiği | `uzun_periyot_esigi` | Number | 14 | 1-365 gün |

### Sistem

| Ayar | Key | Tip | Default |
|------|-----|-----|---------|
| Otomatik Yedekleme | `otomatik_yedekleme` | Toggle | true |
| Yedekleme Günü | `yedek_gunu` | Select | Pazar |
| Zaman Dilimi | `timezone` | Select | Europe/Istanbul |

### Raporlar

| Ayar | Key | Tip | Default |
|------|-----|-----|---------|
| Maks Rapor Günü | `max_report_days` | Number | 365 |
| Varsayılan Fiyat | `default_fuel_price` | Number | 40.0 |

### Bildirimler

| Ayar | Key | Tip | Default |
|------|-----|-----|---------|
| Bildirimler | `notification_enabled` | Toggle | true |

### Görünüm

| Ayar | Key | Tip | Default |
|------|-----|-----|---------|
| Tema | `theme` | Radio | light |
| Dil | `language` | Select | tr |

---

### Premium Settings UI
- **Glass Groups**: Her ayar grubu (Filo, Sistem, Görünüm) `backdrop-blur-lg` efektli birer Glass Card içinde toplanır.
- **Floating Save Bar**: Sayfada herhangi bir değişiklik yapıldığında en altta premium bir "Değişiklikleri Kaydet" yüzer çubuğu (Floating Bar) belirir.
- **Draft Mode**: Kaydedilmemiş değişiklik içeren inputların kenarları hafif sarı bir "Glow" efekti ile vurgulanır.

### Smart Logic: Configuration
- **Value Safeguard**: Hedef tüketim veya limit değerleri mantıksal sınırların dışına çıktığında (`300 L/100km` gibi) sistem anında uyarı verir ve kaydı engeller.
- **Timezone Sync**: Sistem, tarayıcı üzerinden kullanıcı zaman dilimini otomatik algılar ve ayarı "Smart Suggestion" olarak sunar.
- **Key Whitelist**: Backend sadece izin verilen key'leri kabul eder, bilinmeyen key'ler reddedilir.

---

## Kart Stilleri

| Özellik | Değer |
|---------|-------|
| Background | `Surface (Glass)` |
| Border Radius | 24px |
| Padding | 32px |
| Shadow | `Shadow Premium` |
| Gap | 24px |
| Title | 16px, 600, icon sol |

---

## Form Elements

| Element | Stil |
|---------|------|
| Label | 14px, 500, 200px width |
| Input | 300px width, right aligned |
| Toggle | 44px, `#3B82F6` when on |
| Select | 300px width |
| Kaydet | Primary, card footer sağ |

---

## API (Backend Doğrulanmış ✅)

```
# Tüm Ayarları Getir
GET /api/v1/settings
Response: {
    filo_hedef_tuketim: 32.0,
    anormal_ust_sinir: 20,
    anormal_alt_sinir: 20,
    uzun_periyot_esigi: 14,
    otomatik_yedekleme: true,
    yedek_gunu: "Pazar",
    default_fuel_price: 40.0,
    notification_enabled: true,
    theme: "light",
    language: "tr",
    timezone: "Europe/Istanbul",
    max_report_days: 365
}

# Tekil Ayar Getir
GET /api/v1/settings/{key}
Example: GET /api/v1/settings/filo_hedef_tuketim
Response: { filo_hedef_tuketim: "32.0" }  // Key dinamik, value string

# Ayar Güncelle
POST /api/v1/settings?key=filo_hedef_tuketim&value=30.0&description=...
Response: { 
    status: "success",
    message: "Ayar 'filo_hedef_tuketim' başarıyla güncellendi."
}

# Error Response (Invalid Key)
400: { detail: "Geçersiz ayar anahtarı: xyz" }

# Error Response (Invalid Value)
422: { detail: "Değer geçerli aralıkta değil" }
```

---

## Allowed Keys (Backend Whitelist)

```javascript
const ALLOWED_KEYS = [
    'filo_hedef_tuketim',
    'anormal_ust_sinir', 
    'anormal_alt_sinir',
    'uzun_periyot_esigi',
    'otomatik_yedekleme',
    'yedek_gunu',
    'default_fuel_price',
    'notification_enabled',
    'theme',
    'language',
    'timezone',
    'max_report_days'
];
```

---

## Frontend Storage (Theme/Language)

```javascript
// Theme ve language localStorage'da da tutulabilir (offline access)
localStorage.setItem('theme', 'dark');
document.documentElement.setAttribute('data-theme', theme);
```

---

## States

| Durum | Görünüm |
|-------|---------|
| Loading | Skeleton inputs |
| Saving | Button spinner + disabled |
| Success | Green toast "Ayarlar kaydedildi" |
| Error | Red toast + validation message |
| Dirty | Yellow glow on changed fields |
