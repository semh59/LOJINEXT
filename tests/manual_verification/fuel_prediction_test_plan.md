# Yakıt Tahmini Sistemi - Detaylı Test ve Eksiklik Analiz Planı

## 🎯 Amaç

Sistemin "Yakıt Tahmin Algoritmalarının" doğru çalışıp çalışmadığını ve uçtan uca (End-to-End) veri akışını doğrulamak.

---

## 1. Statik Kod Analizi (Yapıldı)

Kod tabanında yapılan ilk inceleme bulguları:

| Bileşen                 | Durum         | Bulgular                                                                                        |
| ----------------------- | ------------- | ----------------------------------------------------------------------------------------------- |
| **Prediction Engine**   | ✅ **MEVCUT** | `PredictionService` (`app/services/prediction_service.py`) fizik tabanlı hesaplamaları yapıyor. |
| **Service Integration** | ❌ **EKSİK**  | `SeferService.add_sefer` metodu, tahmin servisini **ÇAĞIRMIYOR**.                               |
| **Database Model**      | ✅ **MEVCUT** | `Sefer` tablosunda `tahmini_tuketim` kolonu var.                                                |
| **API Schema**          | ❌ **EKSİK**  | `SeferResponse` şemasında `tahmini_tuketim` alanı tanımlı **DEĞİL**. API bu veriyi dönmüyor.    |

**Özet**: Algoritmalar var ama **BAĞLI DEĞİL**. Motor çalışıyor ama tekerleklere güç gitmiyor.

---

## 2. Test Senaryoları (Doğrulama Adımları)

Aşağıdaki testler, onarım yapıldıktan sonra çalıştırılacaktır.

### A. Algoritma Doğrulama (Unit Test)

Fizik motorunun mantıklı sonuçlar ürettiğini teyit eder.

1.  **Senaryo 1: Boş Araç / Düz Yol**
    - Araç: `Mercedes Actros` (Boş Ağırlık: 8000kg)
    - Yük: 0 ton
    - Yol: 100km, 0m tırmanış
    - _Beklenen_: ~22-25 Litre

2.  **Senaryo 2: Tam Yüklü / Düz Yol**
    - Yük: 24 ton (Topbar: 32 ton)
    - Yol: 100km
    - _Beklenen_: ~32-36 Litre (Yük etkisi)

3.  **Senaryo 3: Yüklü / Dağlık Yol**
    - Yük: 24 ton
    - Yol: 100km, **1000m Tırmanış**
    - _Beklenen_: ~45-55 Litre (Yük + Yerçekimi etkisi)

### B. Entegrasyon Doğrulama

Backend entegrasyonu tamir edildikten sonra kontrol edilecekler:

1.  **Yeni Sefer Kaydı**:
    - Yeni sefer oluşturulduğunda `tahmini_tuketim` DB'ye otomatik yazılıyor mu?
2.  **API Yanıtı**:
    - `GET /trips` çağrısında `tahmini_tuketim` alanı JSON içinde geliyor mu?

---

## 3. Onarım Planı (Action Plan)

Testlerin başarılı olması için aşağıdaki kod değişiklikleri **ZORUNLUDUR**:

1.  **Schema Update**: `app/schemas/sefer.py` dosyasına `tahmini_tuketim` alanı ekle.
2.  **Service Integration**: `app/core/services/sefer_service.py` içinde `add_sefer` metoduna `prediction_service.predict_consumption` çağrısını ekle.
3.  **Frontend Display**: Arayüzde bu veriyi gösterecek alanı ekle/güncelle.

---

Bu planı onaylarsanız, **Onarım Planı**'nı uygulamaya başlayacağım.
