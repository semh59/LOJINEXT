---
description: AI tahmin performansını iyileştir veya yeni model eğit (Elite)
---

# /ai-pipeline — AI Tahmin Sistemi Geliştirme

## Adım 1 — Mevcut Durumu Anla (Reason)
- `app/core/ml/` altındaki ensemble ağırlıklarını ve fizik motoru parametrelerini oku.
- Mevcut r2_score ve MAE metriklerini `benchmark.py` ile al.

## Adım 2 — Veri Kalitesi & Analiz // turbo
- Null oranlarını ve outlierları (IQR) kontrol et.
- Training ve Real-time veri tutarlılığını doğrula.

## Adım 3 — Model / Feature Geliştirme (Act)
- `feature_engineering.py` veya `physics_engine.py` (Cd, Area kalibrasyonu) güncellemesi yap.
- Ensemble tuning ile ağırlıkları optimize et.

## Adım 4 — Robustness & Failback (Reflect)
- Kirli veri senaryolarında fallback (rule-based) mekanizmasını stress testine tabi tut.
- Physics override flag'lerinin doğruluğunu kontrol et.

## Adım 5 — Metrik Doğrulama & Versiyonlama (Verify)
- `benchmark.py` ile iyileşmeyi kanıtla.
- Yeni modeli versiyonlayarak kaydet ve `ai_service.py` entegrasyonunu tamamla.
