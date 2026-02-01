# 10 - Uyarılar (Alerts)

> Sistem bildirimleri ve anomali uyarılarının yönetimi
> **Backend Senkronizasyonu:** ✅ Güncel (2026-01-30)

---

## Header Zil Simgesi

```
┌──────────────────────────────────────────┐
│                            🔔(3) 👤 Admin │
│                             ↓             │
│  ┌─────────────────────────────────────┐ │
│  │ Bildirimler     [Tümünü Okundu Yap] │ │
│  ├─────────────────────────────────────┤ │
│  │ 🔴 Yakıt Anomalisi                  │ │
│  │    34ABC123 aracında yüksek tük...  │ │
│  │    2 saat önce                      │ │
│  ├─────────────────────────────────────┤ │
│  │ 🟡 Maliyet Uyarısı                  │ │
│  │    Haftalık yakıt maliyeti %15...   │ │
│  │    5 saat önce                      │ │
│  ├─────────────────────────────────────┤ │
│  │ 🟢 Sistem Bildirimi                 │ │
│  │    Yedekleme tamamlandı             │ │
│  │    1 gün önce        ✓ Okundu       │ │
│  ├─────────────────────────────────────┤ │
│  │         [Tümünü Gör →]              │ │
│  └─────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

---

## Zil Simgesi

| Özellik | Değer |
|---------|-------|
| Icon | Bell, 24px |
| Badge | 16px circle, `#EF4444`, white text |
| Badge Position | Top-right, -4px offset |
| Hover | Background `#F1F5F9` |

---

## Dropdown Panel

| Özellik | Değer |
|---------|-------|
| Width | 380px |
| Max Height | 400px |
| Background | `#FFFFFF` |
| Shadow | `0 10px 40px rgba(0,0,0,0.15)` |
| Border Radius | 12px |
| Position | Right-aligned, below header |

---

## Uyarı Kartı (Dropdown İçi)

| Element | Stil |
|---------|------|
| Container | Padding 16px, border-bottom |
| Severity Dot | 8px circle, sol üst |
| Title | 14px, 600, `#0F172A` |
| Message | 13px, `#475569`, truncate 2 line |
| Time | 12px, `#94A3B8` |
| Unread BG | `#F1F5F9` |
| Read | Normal white bg |

---

## Severity Colors (Backend ile Eşleştirilmiş)

| Level | API Value | Dot | Left Border |
|-------|-----------|-----|-------------|
| Critical | `critical` | `#DC2626` | 3px `#DC2626` |
| High | `high` | `#EA580C` | 3px `#EA580C` |
| Medium | `medium` | `#D97706` | 3px `#D97706` |
| Low | `low` | `#6B7280` | 3px `#6B7280` |

---

## Alert Types (Backend ile Eşleştirilmiş)

| API Type | Türkçe | Icon |
|----------|--------|------|
| `fuel_anomaly` | Yakıt Anomalisi | ⛽ |
| `cost_anomaly` | Maliyet Uyarısı | 💰 |
| `consumption_spike` | Tüketim Artışı | 📈 |
| `km_mismatch` | KM Uyumsuzluğu | 🛣️ |
| `driver_performance` | Şoför Performansı | 👤 |
| `system` | Sistem Bildirimi | ⚙️ |

---

## 🔔 Smart Notification System

### Pulsing Alert Bell
- **Interaction**: Kritik (Critical) veya Yüksek (High) seviyeli okunmamış uyarı varsa, zil simgesi hafif bir "Pulse" (nabız) animasyonu yapar.
- **Frosted Dropdown**: Panel, `backdrop-blur-2xl` ve `bg-white/80` (Frosty) etkisiyle premium bir derinlik kazanır.

### Smart Interaction
- **Optimistic Mark-All-Read**: "Tümünü Okundu Yap" tıklandığında, API yanıtından önce UI anlık olarak temizlenir.
- **Direct Action**: Uyarı kartı içindeki "Detaya Git" butonu, akıllı yönlendirme ile ilgili aracın veya seferin sayfasına focus atar.

### Automatic Alert Generation
- Backend anomaly detection sonuçlarını otomatik olarak alert'e çevirir
- Z-Score tabanlı anomaly detection ile kritik uyarılar oluşturulur

---

## Uyarılar Sayfası (Tam Liste)

```
┌──────────────────────────────────────────────────────────────────────┐
│                              Uyarılar                                │
├──────────────────────────────────────────────────────────────────────┤
│  [Tümünü Okundu Yap]              Filtre: [Severity ▾] [Tip ▾]      │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ SEVERİTY │ TİP          │ BAŞLIK           │ TARİH   │ DURUM │⋮││
│  ├──────────┼──────────────┼──────────────────┼─────────┼───────┼─┤│
│  │ 🔴 CRİT  │ fuel_anomaly │ Yüksek tüketim   │ 2s önce │ Yeni  │⋮││
│  │ 🟡 MED   │ cost_anomaly │ Maliyet artışı   │ 5s önce │ Yeni  │⋮││
│  │ 🟢 LOW   │ system       │ Backup tamamlandı│ 1g önce │ ✓     │⋮││
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## API (Backend Doğrulanmış ✅)

```
# Alert Listesi (AlertResponse array)
GET /api/v1/alerts?status=unread&limit=10&severity=critical
Response: [
    {
        id: 1,
        title: "Yüksek Tüketim Tespit Edildi",
        message: "34ABC123 aracında ortalama tüketim %25 arttı",
        severity: "critical",           // critical | high | medium | low
        alert_type: "fuel_anomaly",     // fuel_anomaly | cost_anomaly | driver_alert | vehicle_alert | system
        source_type: "vehicle",         // NOT: entity_type değil
        source_id: 5,                   // NOT: entity_id değil
        status: "unread",               // unread | read | dismissed
        created_at: "2026-01-30T10:15:00Z",
        read_at: null
    },
    ...
]
# NOT: Backend düz array döner, items/total/unread wrapper YOK

# Okunmamış Alertler (Hızlı erişim)
GET /api/v1/alerts/unread?limit=10
Response: [ ...AlertResponse array ]

# Alert Sayıları (AlertCountResponse - Header Badge için)
GET /api/v1/alerts/count
Response: {
    total: 25,
    unread: 8,
    critical: 2,
    high: 5,
    medium: 10,
    low: 8
}

# Çoklu Alert Okundu İşaretle
POST /api/v1/alerts/mark-read
Body: { alert_ids: [1, 2, 3] }
Response: { success: true, marked_count: 3 }

# Tümünü Okundu İşaretle
POST /api/v1/alerts/mark-all-read
Response: { success: true, marked_count: 8 }

# Alert Dismiss (Soft Delete)
DELETE /api/v1/alerts/{id}
Response: { success: true, dismissed_id: 1 }

# Alert Oluştur
POST /api/v1/alerts/create
Body: {
    alert_type: "fuel_anomaly",
    severity: "medium",
    title: "Test Alert",
    message: "Test message",
    source_id: 5,
    source_type: "vehicle"
}

# Anomalilerden Otomatik Alert Üret
POST /api/v1/alerts/generate-from-anomalies
Response: { success: true, created_count: 3 }
```

---

## Response Field Mapping

| API Field | UI Element |
|-----------|------------|
| `severity` | Severity dot & border color |
| `alert_type` | Type badge & icon |
| `title` | Card title |
| `message` | Card description (truncated) |
| `read` | Background color (unread = gray) |
| `created_at` | Relative time ("2 saat önce") |
| `entity_type` + `entity_id` | Detay navigasyonu için |
