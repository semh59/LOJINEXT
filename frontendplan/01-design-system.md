# Design System

> Tüm sayfalarda kullanılacak ortak tasarım değerleri

---

## 🎨 Renk Paleti (Vibrant & Premium)

### Ana Renkler

| Renk | Hex | Kullanım |
|------|-----|----------|
| Primary | `#3B82F6` | Butonlar, linkler, aktif durumlar (Brilliant Blue) |
| Primary Dark | `#1D4ED8` | Hover durumları |
| Primary Light | `#EFF6FF` | Subtle backgrounds |
| Surface (Glass) | `rgba(255, 255, 255, 0.7)` | Glassmorphism katmanları |
| Accent | `#10B981` | Başarı, pozitif trendler |

### Durum Renkleri

| Durum | Background | Text | Border |
|-------|-------------|------|--------|
| Success | `#D1FAE5` | `#059669` | `#10B981` |
| Warning | `#FEF3C7` | `#D97706` | `#F59E0B` |
| Error | `#FEE2E2` | `#DC2626` | `#EF4444` |
| Info | `#DBEAFE` | `#3B82F6` | `#3B82F6` |

### Severity (Alerts)

| Level | Background | Text | Line (Side) |
|-------|------------|------|-------------|
| Critical | `#FEE2E2` | `#DC2626` | `#DC2626` |
| High | `#FFEDD5` | `#EA580C` | `#EA580C` |
| Medium | `#FEF3C7` | `#D97706` | `#D97706` |
| Low | `#F3F4F6` | `#6B7280` | `#6B7280` |

### Nötr Tonlar & Glassmorphism

| Ton | Hex / Value | Kullanım |
|-----|-------------|----------|
| Background | `#F1F5F9` | Yumuşak gri sayfa arka plan |
| Glass Border | `rgba(255, 255, 255, 0.4)` | Saydam çerçeveler |
| Backdrop Blur | `12px` | Glassmorphism bulanıklık seviyesi |
| Text | `#0F172A` | Derin lacivert ana metin |
| Text Secondary| `#475569` | İkincil açıklama metinleri |
| Divider | `#E2E8F0` | Ayraçlar ve ince çerçeveler |
| Shadow Premium| `0 10px 25px -5px rgba(0,0,0,0.05)` | Yumuşak derinlik gölgesi |

---

## 📝 Typography

### Font Family

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

### Scale

| Token | Size | Weight | Line Height | Kullanım |
|-------|------|--------|-------------|----------|
| h1 | 28px | 700 | 1.2 | Sayfa başlık |
| h2 | 22px | 600 | 1.3 | Bölüm başlık |
| h3 | 18px | 600 | 1.4 | Kart başlık |
| body | 14px | 400 | 1.5 | Normal metin |
| small | 12px | 400 | 1.4 | Alt bilgi |
| caption | 11px | 500 | 1.3 | Badge, label |

| Özel | Size | Weight | Kullanım |
|------|------|--------|----------|
| stat-value | 32px | 700 | Dashboard kartları |
| table-header | 12px | 600 | Tablo başlık (uppercase) |
| button | 14px | 500 | Buton metni |

---

## 📐 Spacing

### Base: 8px

| Token | Value | Kullanım |
|-------|-------|----------|
| xs | 4px | İkon padding |
| sm | 8px | Input iç boşluk |
| md | 16px | Kart padding |
| lg | 24px | Bölüm arası |
| xl | 32px | Sayfa padding |
| 2xl | 48px | Büyük boşluklar |

### Grid

| Özellik | Değer |
|---------|-------|
| Container | max 1400px, center |
| Sidebar | 260px fixed |
| Header | 64px fixed |
| Content Padding | 32px |
| Gutter | 24px |
| Columns | 12 |

---

## 🧩 Komponentler

### Button

| Variant | Background | Text | Border |
|---------|------------|------|--------|
| Primary | `#3B82F6` | `#FFFFFF` | none |
| Secondary | `#FFFFFF` | `#0F172A` | `#E2E8F0` |
| Danger | `#EF4444` | `#FFFFFF` | none |
| Ghost | transparent | `#475569` | none |

| Size | Height | Padding | Font |
|------|--------|---------|------|
| sm | 32px | 8px 12px | 13px |
| md | 40px | 10px 16px | 14px |
| lg | 48px | 12px 24px | 15px |

| State | Style |
|-------|-------|
| Hover | Darken 10% |
| Disabled | opacity 0.5, cursor not-allowed |
| Loading | Spinner 16px + text |

### Input

| Property | Value |
|----------|-------|
| Height | 40px (44px for forms) |
| Border | 1px solid `#E2E8F0` |
| Border Radius | 12px |
| Padding | 14px 18px |
| Focus | Border `#3B82F6`, shadow `0 0 0 4px rgba(59,130,246,0.15)` |
| Error | Border `#EF4444` |

### Card

| Property | Value |
|----------|-------|
| Background | `Surface (Glass)` |
| Border Radius | 24px |
| Shadow | `Shadow Premium` |
| Padding | 24px |
| Hover (clickable) | Shadow `0 20px 25px -5px rgba(0,0,0,0.1)` |

### Table

| Property | Value |
|----------|-------|
| Header BG | `#F8FAFC` (subtle contrast) |
| Header Text | 12px, 600, uppercase, `#475569` |
| Cell Padding | 18px 24px |
| Row Hover | `#F1F5F9` |
| Border | 1px solid `#F1F5F9` |

### Modal

| Property | Value |
|----------|-------|
| Overlay | `rgba(15, 23, 42, 0.4)` (deep frosted) |
| Size SM | 440px |
| Size MD | 560px |
| Size LG | 800px |
| Border Radius | 24px |
| Padding | 32px |
| Shadow | `0 25px 50px -12px rgba(0,0,0,0.25)` |

### Badge

| Variant | Background | Text |
|---------|------------|------|
| Default | `#F1F5F9` | `#475569` |
| Success | `#D1FAE5` | `#059669` |
| Warning | `#FEF3C7` | `#D97706` |
| Error | `#FEE2E2` | `#DC2626` |

Padding: 4px 10px, Border Radius: 4px, Font: 11px 500

### Toast

| Type | Left Border | Icon |
|------|-------------|------|
| Success | `#10B981` | ✓ |
| Error | `#EF4444` | ✕ |
| Warning | `#F59E0B` | ⚠ |
| Info | `#3B82F6` | ℹ |

Position: Top-right, Duration: 3s, Animation: Slide-in from right

---

## 🎬 Animasyonlar

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Hover | Color/shadow | 150ms | ease-out |
| Modal | Fade + scale 0.95→1 | 200ms | ease-out |
| Dropdown | Fade + slideY | 150ms | ease-out |
| Toast | Slide from right | 300ms | ease-out |
| Page | Fade | 200ms | ease-in-out |
| Skeleton | Pulse | 1.5s | linear loop |

---

## 🔤 İkonlar

**Önerilen:** [Lucide Icons](https://lucide.dev/)

| Icon | Kullanım |
|------|----------|
| LayoutDashboard | Dashboard |
| Truck | Araçlar |
| Users | Sürücüler |
| Route | Seferler |
| Fuel | Yakıt |
| MapPin | Güzergahlar |
| BarChart3 | Raporlar |
| Brain | AI Tahmin |
| Bell | Bildirimler |
| Settings | Ayarlar |
| Plus | Ekle |
| Pencil | Düzenle |
| Trash2 | Sil |
| Search | Ara |
| Filter | Filtrele |
| Download | İndir |
| Upload | Yükle |
| Eye / EyeOff | Göster/Gizle |
| ChevronDown | Dropdown |
| X | Kapat |
| Check | Onay |
| AlertTriangle | Uyarı |
