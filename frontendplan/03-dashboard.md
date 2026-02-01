# 03 - Dashboard

> Filo durumunun tek bakışta görülmesi - Ana kontrol merkezi
> **Backend Senkronizasyonu:** ✅ Güncel (2026-01-30)

---

## Layout

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    ← Stats Cards    │
│  │ 🗺️      │ │ 📍      │ │ ⛽      │ │ 📊      │      (4 kolon)      │
│  │ Sefer   │ │ KM      │ │ Yakıt   │ │ Ortalama│                      │
│  │ 1,234   │ │ 45,678  │ │ 12,345L │ │ 32.5    │                      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                      │
│                                                                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                                  │
│  │ 🚛      │ │ 👤      │ │ 📅      │  ← 3 kolon                       │
│  │ Araç    │ │ Şoför   │ │ Bugün   │                                  │
│  │ 25      │ │ 18      │ │ 5       │                                  │
│  └─────────┘ └─────────┘ └─────────┘                                  │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                 📈 Aylık Tüketim Trendi                        │   │
│  │                                                                │   │
│  │     ▓▓▓   ▓▓▓   ▓▓▓   ▓▓▓   ▓▓▓   ▓▓▓                        │   │
│  │     Oca   Şub   Mar   Nis   May   Haz                         │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐  ← Hızlı Erişim        │
│  │ + Sefer    │ │ + Yakıt    │ │ 📥 Rapor   │                         │
│  └────────────┘ └────────────┘ └────────────┘                         │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Stats Kartları (7 adet)

### Kart Yapısı

```
┌────────────────────────┐
│  ┌────┐                │
│  │ 🗺️ │  TOPLAM SEFER  │  ← 12px, uppercase, #64748B
│  └────┘                │
│         1,234          │  ← 28px, 700, `#0F172A`
│         ↑ 5.2%         │  ← 12px, trend badge (yeşil/kırmızı)
└────────────────────────┘
```

### Kart Stilleri (Premium & Glass)

| Özellik | Değer |
|---------|-------|
| Grid | 4 + 3 kolon konfigürasyonu |
| Appearance | **Glassmorphism**: `bg-white/70`, `backdrop-blur-md` |
| Border | `1px solid rgba(255, 255, 255, 0.4)` |
| Radius | 24px (Super-ellipse) |
| Shadow | `Shadow Premium` (bkz. Design System) |
| Hover | `Scale(1.02)`, `shadow-xl`, Glow Effect |

### Smart Logic: Trends
- **Calculation**: Trend verileri API'den gelen son iki dönem verisi ile frontend tarafında anlık hesaplanır.
- **Empty State**: Veri yetersizse "Yeni" veya "---" ibaresi gösterilir, hata verilmez.

### Kart İçerikleri (API Field Mapping)

| Kart | İkon | Label | API Field |
|------|------|-------|-----------|
| Toplam Sefer | Route | TOPLAM SEFER | `toplam_sefer` |
| Toplam KM | MapPin | TOPLAM KM | `toplam_km` |
| Toplam Yakıt | Fuel | TOPLAM YAKIT | `toplam_yakit` |
| Filo Ortalaması | Gauge | FİLO ORT. | `filo_ortalama` |
| Aktif Araç | Truck | AKTİF ARAÇ | `aktif_arac` |
| Aktif Şoför | Users | AKTİF ŞOFÖR | `aktif_sofor` |
| Bugünkü Sefer | Calendar | BUGÜN | `bugun_sefer` |

### Trend Badge

| Durum | Renk | Icon |
|-------|------|------|
| Artış | `#059669` bg `#D1FAE5` | ↑ |
| Düşüş | `#DC2626` bg `#FEE2E2` | ↓ |
| Sabit | `#64748B` bg `#F1F5F9` | → |

---

## Grafik Kartı

| Özellik | Değer |
|---------|-------|
| Height | 320px |
| Chart Type | Area Chart + Line |
| Line Color | `#3B82F6` |
| Area Fill | `rgba(59, 130, 246, 0.1)` gradient |
| Grid | Dashed, `#E2E8F0` |
| X Axis | Son 6 ay |
| Y Axis | Litre |
| Tooltip | "Ocak 2026: 2,345 L" |

---

## Hızlı Erişim Butonları

| Buton | İkon | Aksiyon |
|-------|------|---------|
| Yeni Sefer | Plus + Route | Sefer modal |
| Yakıt Ekle | Plus + Fuel | Yakıt modal |
| Rapor İndir | Download | PDF dropdown |

| Stil | Değer |
|------|-------|
| Height | 48px |
| Background | `#FFFFFF` |
| Border | 1px solid `#E2E8F0` |
| Hover | Border `#3B82F6` |
| Icon | 20px, sol |
| Text | 14px, 500 |

---

## API (Backend Doğrulanmış ✅)

```
# Dashboard İstatistikleri
GET /api/v1/reports/dashboard
Response: {
    toplam_sefer: 1234,
    toplam_km: 456789,
    toplam_yakit: 12345.5,
    filo_ortalama: 32.5,
    aktif_arac: 25,
    aktif_sofor: 18,
    bugun_sefer: 5,
    trends: {
        sefer: 5.2,        // Bu ay vs geçen ay % değişim
        km: -2.1,
        tuketim: 1.5
    }
}

# Aylık Tüketim Trendi
GET /api/v1/reports/consumption-trend
Response: [
    { month: "2026-01", consumption: 1234.5 },
    { month: "2025-12", consumption: 1189.2 },
    ...
]

# Anomali Özeti (Header Badge için)
GET /api/v1/anomalies/summary
Response: {
    tuketim: { count: 5, critical: 1 },
    maliyet: { count: 3, critical: 0 },
    total_count: 8,
    unread_count: 3
}
```

---

## States

| Durum | Görünüm |
|-------|---------|
| Loading | Skeleton kartlar (pulse) |
| Error | Error card + Retry butonu |
| Empty | "Henüz veri yok" mesajı |

---

## Animasyonlar

| Element | Animation |
|---------|-----------|
| Kartlar | Staggered fade-in (50ms delay) |
| Stats Value | Count-up 1s |
| Grafik | Draw animation 800ms |
| Hover | Transform 150ms |
