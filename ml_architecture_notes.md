# LojiNext: Yapay Zeka MLOps Stratejisi ve Veri Güvenliği

Bu doküman, LojiNext projesindeki araç yakıt tüketim tahmin modellerinin (ML/AI) zaman içindeki performans düşüşünü (Model Drift) tespit etme ve sentetik verilerin modelin eğitimini zehirlemesini (Data Poisoning) önleme stratejilerini açıklar.

## 1. Veri Zehirlenmesini (Data Poisoning) Önleme Stratejisi

Test, QA ve simülasyon süreçlerinde oluşturulan sefer kayıtlarının model eğitimine girmesi, modelin gerçek hayat verilerinden sapmasına (bias) neden olur.

- **`is_real` Flag Standardı**: `Sefer` (Trips) tablosunda bulunan `is_real` boolean alanı, gerçek fiziksel seferlerle sistemin ürettiği sentetik veya arka plan işlemlerinin ayrılabilmesini sağlar.
- **Repository Koruması**: Backend'in veri çekme katmanında (`SeferRepository.get_for_training`) `include_synthetic=False` varsayılan olarak aktiftir. Bu yapı arka planda `s.is_real = TRUE` SQL şartı ile veri katmanında tam koruma sağlar.
- **Guardrail**: Hiçbir API kullanıcısı veya arayüz özelliği, varsayılan olarak "Tamamlandı" durumuna alınırken "is_real" atamasını manipüle etmemelidir. Backend bunu doğrudan güvence altına almıştır. Sistem test senaryolarında mock işlemler oluşturulurken her zaman `is_real=False` eklenir.

## 2. Model Drift (Sapma) Tespiti ve Eşik Değerleri (Thresholds)

Zamanla araçların yaşlanması, mevsimsel değişiklikler veya operasyonel rotaların değişmesi nedeniyle Yapay Zeka modellerinin öğrenmiş olduğu gerçeklikte kaymalar (Drift) meydana gelecektir.

Sistem, iki temel regresyon metriği ile modelin performans düzenini izleyecektir:

### Kritik Eşikler

1. **R² Skoru (Belirleyicilik Katsayısı)**:
   - **Hedeflenen Değer**: > 0.85
   - **Müdahale Sınırı**: Sürekli olarak (rolling 7 günlük pencerede) **0.85'in altına** düşmesi.
2. **RMSE (Kök Ortalama Kare Hatası)**:
   - **Hedeflenen Değer**: Ortalamanın %10 - %15 altı bir orana oturması.
   - **Müdahale Sınırı**: Önceki versiyon modele göre hata oranında **%15'lik tutarlı bir sapma/artış** görülmesi.

### Yeniden Eğitim (Retraining) Tetikleyicileri

Model drift durumu bir asenkron cron job vasıtasıyla haftalık veya aylık raporlanır.
Belirlenen limitler aşıldığında aşağıdaki aksiyonlar tetiklenir:

1. **Veri Havuzunun Yenilenmesi**: Yalnızca son dönemin en güncel logları (Örn: Son 6 Ay, `is_real=True` kısıtıyla) temel alınacak şekilde `get_for_training` veri seti derlenir.
2. **Outlier Temizliği**: İzole şöför hataları veya sistem bazlı anomali logları eğitim setinden çıkarılır.
3. **Versiyonlama**: Yeni eğitilen model `model_v{N+1}` olarak işaretlenir ve Shadow modda (Live veriler üzerinde, müşteriye yanıt dönmeden asenkron arka planda kalarak) belli bir süre test edildikten sonra A/B Testing ile tam prodüksiyona çekilir.
