# Skill: Frontend React (Elite)

## Ne Zaman Yükle
- React component, UI/UX tasarımı veya API entegrasyonu yaparken.

## Teknoloji Stack
- React 18, TypeScript, Vite, TanStack Query, Zustand, Tailwind CSS.

## Geliştirme Standartları
- **Server State**: 
  - Veri çekme ve mutasyon işlemleri `TanStack Query` ile yapılmalıdır.
  - Form mutasyonlarından sonra ilgili query'ler invalidate edilmelidir.
- **UI State**: 
  - Componentler arası paylaşılması gereken global UI durumları için `Zustand` kullanılmalıdır.
- **Form Validation**: 
  - `react-hook-form` ve `zod` ikilisi zorunludur.

## Görsel & UX Kuralları
- 100+ item içeren listelerde `virtualization` kullanılmalıdır.
- Yükleme durumlarında `loading skeletons` tercih edilmelidir.
- Responsive tasarım (Mobile-First) zorunludur.

## Yapma
- `any` tipi kullanma.
- Inline styling yapma (Tailwind kullan).
- Business logic'i component içine gömme (Hook kullan).
