# 13 - Kullanıcı Yönetimi (Users)

> Sistem kullanıcılarının yönetimi (Sadece Admin)
> **Backend Senkronizasyonu:** ✅ Güncel (2026-01-30)

---

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│                           Kullanıcılar                               │
├──────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 🔍 Ara...                               [+ Yeni Kullanıcı]     │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ KULLANICI ADI │ AD SOYAD       │ ROL    │ DURUM  │ İŞLEM      │ │
│  ├───────────────┼────────────────┼────────┼────────┼────────────┤ │
│  │ admin         │ Sistem Admin   │ 👑 Admin│  ✅    │ -          │ │
│  │ operator1     │ Ali Veli       │ 👤 User │  ✅    │ ⋮          │ │
│  │ operator2     │ Ahmet Yılmaz   │ 👤 User │  ❌    │ ⋮          │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Tablo Kolonları (API Field Mapping)

| Kolon | Width | API Field | Format |
|-------|-------|-----------|--------|
| Kullanıcı Adı | 150px | `kullanici_adi` | Text |
| Ad Soyad | 180px | `ad_soyad` | Text |
| Rol | 100px | `rol` | Badge |
| Durum | 80px | `aktif` | Badge |
| İşlemler | 80px | - | Menu |

---

## Rol Badge (Backend ile Eşleştirilmiş)

| Rol | API Value | Icon | BG | Text |
|-----|-----------|------|-----|------|
| Admin | `admin` | 👑 | `#DBEAFE` | `#3B82F6` |
| User | `user` | 👤 | `#F1F5F9` | `#475569` |

---

## Durum Badge

| Durum | API Value | BG | Text |
|-------|-----------|-----|------|
| Aktif | `true` | `#D1FAE5` | `#059669` |
| Pasif | `false` | `#FEE2E2` | `#DC2626` |

---

## Modal: Yeni Kullanıcı

```
┌────────────────────────────────────────┐
│  👤 Yeni Kullanıcı                     │
│                                        │
│  Kullanıcı Adı*  [                  ]  │
│  Şifre*          [                  ]  │
│  Ad Soyad        [                  ]  │
│  Rol             [User ▾            ]  │
│  Aktif           [● Açık]              │
│                                        │
│  [İptal]              [Kaydet]         │
└────────────────────────────────────────┘
```

### Form Fields (Backend ile Eşleştirilmiş)

| Alan | Tip | API Field | Kural |
|------|-----|-----------|-------|
| Kullanıcı Adı* | Input | `kullanici_adi` | Unique, 3-50 char |
| Şifre* | Password | `sifre` | Min 8, bcrypt hashed |
| Ad Soyad | Input | `ad_soyad` | Max 100 |
| Rol | Select | `rol` | admin, user |
| Aktif | Toggle | `aktif` | Default: true |

### Password Requirements

```
- Minimum 8 karakter
- En az 1 büyük harf
- En az 1 küçük harf
- En az 1 rakam
```

---

## Actions

| Item | Icon | Açıklama | Color |
|------|------|----------|-------|
| Sil | Trash2 | Soft delete (pasife çek) | `#EF4444` |

> **Not:** Admin kendini silemez (Backend 400 error döner)

---

## Delete Confirmation

```
┌────────────────────────────────────┐
│  ⚠️ Kullanıcı Silinecek           │
│                                    │
│  "operator1" kullanıcısı           │
│  pasif yapılacaktır.               │
│                                    │
│  [İptal]             [Sil]         │
└────────────────────────────────────┘
```

---

## 🧠 Smart User Management

### User Integrity & Security

- **Real-time Availability**: Kullanıcı adı girilirken sistem arka planda (debounced) benzersizlik kontrolü yapar ve anında görsel onay (Check icon) verir.
- **Strength Visualizer**: Şifre her karakterde premium bir animasyonlu bar ile "Düşük/Orta/Güçlü" seviyesini gösterir.
- **Optimistic Toggle**: Kullanıcının "Aktif" durumu değiştirildiğinde, API yanıtı beklenmeden badge rengi ve ikon anlık olarak güncellenir.

### Self-Delete Prevention (Backend)
- Backend mevcut kullanıcının kendini silmesini engeller
- 400 Bad Request: "Kendinizi silemezsiniz"

### Premium Visuals
- **Avatar Support**: Kullanıcının Ad/Soyad baş harfleri ile şık bir `Vibrant Gradient Avatar` otomatik oluşturulur.
- **Interactive Badges**: Roller (Admin/User) üzerine gelindiğinde parlayan (Glow) ve açıklama içeren premium badgelar kullanılır.

---

## API (Backend Doğrulanmış ✅)

```
# Kullanıcı Listesi (KullaniciRead array)
GET /api/v1/users?skip=0&limit=100
Response: [
    {
        id: 1,
        kullanici_adi: "admin",
        ad_soyad: "Sistem Admin",
        rol: "admin",
        aktif: true
    },
    {
        id: 2,
        kullanici_adi: "operator1",
        ad_soyad: "Ali Veli",
        rol: "user",
        aktif: true
    },
    ...
]
# NOT: Backend düz array döner, items/total wrapper YOK

# Kullanıcı Ekle (201 Created)
POST /api/v1/users
Body: {
    kullanici_adi: "newuser",
    sifre: "SecurePass123",
    ad_soyad: "Yeni Kullanıcı",
    rol: "user",
    aktif: true
}
Response: { id: 6, kullanici_adi: "newuser", ad_soyad: "Yeni Kullanıcı", ... }

# Kullanıcı Sil (Soft Delete - 204 No Content)
DELETE /api/v1/users/{id}
Response: No Content (204)
# NOT: Self-delete 400 error: "Kendi hesabınızı silemezsiniz."

# Error: Self Delete
DELETE /api/v1/users/{current_user_id}
Response: 400 { detail: "Kendinizi silemezsiniz" }

# Error: Duplicate Username
POST /api/v1/users
Response: 400 { detail: "Bu kullanıcı adı zaten kullanılıyor" }

# Username Availability Check (Frontend Debounced)
GET /api/v1/users/check-username?username=newuser
Response: { available: true }
```

---

## Validations

| Alan | Kural |
|------|-------|
| Kullanıcı Adı | Unique check on blur |
| Şifre | Strong password regex |
| Self Delete | Blocked (400 error) |

---

## States

| Durum | Görünüm |
|-------|---------|
| Loading | Skeleton rows |
| Empty | "Henüz kullanıcı eklenmedi" + CTA |
| Error | Error toast + message |
| Deleting | Row fade out animation |
