# 02 - Login Sayfası

> Kullanıcının sisteme güvenli giriş yapması
> **Backend Senkronizasyonu:** ✅ Güncel (2026-01-30)

---

## Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                     Background: #F1F5F9                         │
│                                                                 │
│                    ┌─────────────────────┐                      │
│                    │     🚛 LOGO (64px)  │                      │
│                    │                     │                      │
│                    │  LojiNext AI        │  ← 24px, 700         │
│                    │  TIR Yakıt Takip    │  ← 14px, 400         │
│                    │                     │                      │
│                    │  ┌───────────────┐  │                      │
│                    │  │ Kullanıcı Adı │  │  ← 48px height       │
│                    │  └───────────────┘  │                      │
│                    │        gap: 20px    │                      │
│                    │  ┌───────────────┐  │                      │
│                    │  │ Şifre     👁  │  │  ← Eye toggle        │
│                    │  └───────────────┘  │                      │
│                    │        gap: 24px    │                      │
│                    │  ┌───────────────┐  │                      │
│                    │  │  Giriş Yap    │  │  ← Primary button    │
│                    │  └───────────────┘  │                      │
│                    └─────────────────────┘                      │
│                           ↑                                     │
│                    Card: 400px, radius 16px                     │
│                    shadow: 0 4px 20px rgba(0,0,0,0.08)          │
│                    padding: 48px 40px                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tasarım Detayları

### Premium Login Interface

| Özellik | Değer |
|---------|-------|
| Background | **Vibrant Mask**: `#F1F5F9` ile soyut geometrik premium pattern |
| Login Card | **Glassmorphism**: `rgba(255,255,255,0.75)`, `backdrop-blur-xl`, radius 32px |
| Border | `1px solid rgba(255,255,255,0.5)` |
| Shadow | `Shadow Premium` + subtle glow |
| Input Style | Borderless glass style, 14px radius |

### Smart Logic & Security

- **Smart Feedback**: Hata durumunda kartta "Shake" animasyonu ve 2 saniyelik kırmızı border-glow.
- **Rate Limit UI**: Arka arkaya hatalı girişlerde butona "30sn bekleyin" sayacı eklenir.
- **Timing Attack Prevention**: Backend dummy hash ile timing attack önler

### Logo Alanı

| Element | Stil |
|---------|------|
| Logo | 64x64px, center |
| Başlık | 24px, 700, `#0F172A`, mt: 16px |
| Alt başlık | 14px, 400, `#475569`, mt: 4px |
| Gap to form | 32px |

### Form

| Element | Stil |
|---------|------|
| Label | 14px, 500, `#374151`, mb: 6px |
| Input | 48px height, 8px radius |
| Gap | 20px |
| Şifre icon | 20px, sağ padding içinde |

### Giriş Butonu

| Özellik | Değer |
|---------|-------|
| Width | 100% |
| Height | 48px |
| Margin Top | 24px |
| Background | `#3B82F6` |
| Hover | `#1D4ED8` |
| Text | 16px, 600, white |
| Radius | 12px |

### Durumlar

| Durum | Görünüm |
|-------|---------|
| Loading | Spinner 20px + "Giriş yapılıyor..." |
| Error Input | Border `#EF4444` |
| Error Message | 12px, `#EF4444`, icon ⚠️, mt: 4px |
| Disabled | opacity 0.6 |

---

## API (Backend Doğrulanmış ✅)

```
# Login
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded
Body: username=xxx&password=xxx

# Success Response
{
    access_token: "eyJhbGciOiJIUzI1NiIs...",
    token_type: "bearer"
}

# Error Responses
401: { detail: "Incorrect username or password" }
422: { detail: [...validation errors...] }
429: { detail: "Çok fazla deneme. Lütfen bekleyin." }
```

### Token Storage & Usage

```javascript
// Token'ı localStorage'a kaydet
localStorage.setItem('access_token', response.access_token);

// Tüm API çağrılarında header'a ekle
headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
}
```

### JWT Token İçeriği (Decode)

```json
{
    "sub": "admin",
    "user_id": 1,
    "role": "admin",
    "exp": 1738281600
}
```

### Backend Security Features

| Feature | Açıklama |
|---------|----------|
| bcrypt rounds=12 | Güçlü şifre hash |
| Timing Attack Prevention | Dummy hash ile sabit süre |
| JWT Expiration | Configurable (default 24h) |
| Rate Limiting | 5 deneme / dakika |

---

## Animasyonlar

| Element | Animation |
|---------|-----------|
| Card yüklenme | Fade-in + slide-up 300ms |
| Input focus | Border transition 150ms |
| Button hover | Background transition 150ms |
| Error | Form shake 200ms |

---

## Error Handling

| Error Code | Frontend Action |
|------------|-----------------|
| 401 | Shake animation + error message |
| 422 | Field-level validation errors |
| 429 | Disable button + countdown timer |
| 500 | Generic error + retry option |
