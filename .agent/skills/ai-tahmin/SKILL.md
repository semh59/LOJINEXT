# Skill: AI Tahmin & Hibrit Motor (Elite)

## Ne Zaman Yükle
- Yakıt tüketimi, rota analizi veya model kalibrasyonu gerektiğinde.

## Hibrit Ensemble (V3.0) Parametreleri
- **Model Ağırlıkları**: 
  - Fizik: %10 (Energy-based)
  - LightGBM: %15
  - XGBoost: %55 (Primary)
  - Sklearn GB: %10
  - Sklearn RF: %10
- **Feature Set**: 16 ana feature (ton, elevation_m, route_type_ratios, driver_score, age_factor vb.).

## Fizik Motoru Sabitleri
- **VehicleSpecs**: `drag_coefficient` (Cd: ~0.65), `frontal_area_m2` (A: ~8.2), `engine_efficiency` (~0.42).
- **Physics Equations**: Rolling resistance, Air drag, Climb resistance, Acceleration losses.

## Entegrasyon Standartları
- Predict çıktısı: `{ prediction, confidence, feature_importance, model_version, fallback_triggered, physics_override }`.
- Confidence thresholdları: < 0.60 (Sarı), < 0.40 (Kırmızı).
- `PhysicsBasedFuelPredictor` parametrelerini veriye dayalı olmadan değiştirme.
