# Güvenlik ve Yetkilendirme İyileştirme Planı

Bu plan, tespit edilen "Veri İzolasyonu" ve "Yetki Aşımı" açıklarını kapatmayı hedefler.

## 🎯 Hedefler

1.  **Row Level Security (RLS)**: Şoförlerin sadece kendi seferlerini görmesini sağlamak.
2.  **Role Mapping**: Kullanıcı (Account) ile Şoför (Entity) arasındaki bağı kurmak.
3.  **Veri Sızıntısını Önleme**: API yanıtlarından şifre hash'lerini tamamen temizlemek.

---

## 🛠️ Önerilen Değişiklikler

### 1. Veritabanı ve Model Güncellemesi

- **[MODIFY] [models.py](file:///D:/PROJECT/LOJINEXT/app/database/models.py)**:
  - `Kullanici` tablosuna `sofor_id` (ForeignKey, Optional) alanı eklenecek.
  - _Neden?_: Bir kullanıcının hangi şoför olduğunu bilmeden verisini izole edemeyiz.

### 2. API Şemaları

- **[MODIFY] [user.py](file:///D:/PROJECT/LOJINEXT/app/schemas/user.py)**:
  - `KullaniciCreate` ve `KullaniciRead` modellerine `sofor_id` eklenecek.

### 3. Backend Servis Katmanı

- **[MODIFY] [sefer_service.py](file:///D:/PROJECT/LOJINEXT/app/core/services/sefer_service.py)**:
  - `get_all_paged` metoduna `current_user` objesi delege edilecek.
  - Eğer kullanıcı rolü `user` ise, filtreler arasına otomatik olarak `sofor_id = current_user.sofor_id` eklenecek.

### 4. API Endpoints

- **[MODIFY] [trips.py](file:///D:/PROJECT/LOJINEXT/app/api/v1/endpoints/trips.py)**:
  - `read_seferler` (List) ve `read_sefer` (Detail) endpointleri kullanıcı rolüne göre filtreleme yapacak.
  - Eğer bir `user` başkasının ID'sini talep ederse `403 Forbidden` dönecek.

---

## 🧪 Doğrulama Planı

1.  **Migration Test**: Yeni kolonun hatasız eklendiğini doğrula.
2.  **Isolation Test**: `test_boundaries.py` scriptini tekrar çalıştır.
    - Beklenen: `USER saw 0 trips` (veya sadece kendine atananları).
    - Beklenen: `403 Forbidden` (Başkasına ait ID istendiğinde).
3.  **Sanitization Test**: `GET /users` sonucunda hash gelmediğini doğrula.

---

> [!IMPORTANT]
> Bu değişiklikler geriye dönük olarak mevcut kullanıcıların `sofor_id` alanlarını boş bırakacaktır. Admin panelinden bu eşleştirmelerin yapılması gerekecektir.

## Phase 2G: ML Model Data Enrichment & Retraining

### Goal

Improve fuel prediction accuracy by incorporating detailed route analysis features (motorway %, steepness, etc.) into the ML model.

### Steps

1.  **Data Enrichment**:
    - Script: `scripts/enrich_existing_data.py`
    - Action: Iterate through completed `Sefer` records.
    - Logic: Use `OpenRouteClient` to fetch route details if missing.
    - Output: Update `Sefer.rota_detay` with `route_analysis` (road types, gradients).

2.  **ML Model Upgrade**:
    - Update `EnsembleFuelPredictor.prepare_features`:
      - Extract `motorway_ratio`, `trunk_ratio`, `residential_ratio`.
      - Extract `ascent_m`, `descent_m`.
    - Script: `scripts/train_model_with_route_features.py`
    - Metric: Compare R² score before and after.

3.  **Verification**:

## Phase 7: Financial Integration (FinTech & Fuel Cards)

### Goal

Eliminate manual data entry and prevent fraud by integrating directly with Fuel Card providers (Shell TTS, Opet Otobil, BP Taşıtmatik) and automating invoice reconciliation.

### Proposed Architecture

1.  **Fuel Card Adapter Pattern**:
    - `FuelProviderAdapter` (Interface): `fetch_transactions(start_date, end_date)`
    - `ShellAdapter`: Implements Shell API logic.
    - `OpetAdapter`: Implements Opet WEB Service logic.
    - `ExcelAdapter`: Fallback for providers without API (Upload Excel).

2.  **Reconciliation Engine (`ReconciliationService`)**:
    - **Matching Logic**: Fuzzy match `Plate + Date (+/- 30 mins) + Amount (+/- 1%)`.
    - **Discrepancy Detection**:
      - _Missing in System_: Driver didn't enter the receipt -> Auto-create "Draft" record.
      - _Mismatch_: Driver entered 500L, Card says 450L -> Flag as "Suspicious".
      - _Phantom Fill_: Card used at station X, GPS says vehicle was at Y -> Flag as "Theft".

### Implementation Steps

1.  **Database Updates**:
    - New Table: `FuelCardTransaction` (Raw data from API).
    - Update `YakitAlimi`: Add `matched_transaction_id` and `reconciliation_status` (Matched, Mismatch, Pending).

2.  **Background Jobs**:
    - `sync_fuel_transactions.py`: Runs nightly to fetch data from APIs.
    - `run_reconciliation.py`: Runs after sync to match records.

3.  **UI Updates**:
    - **Finansal Mutabakat Ekranı**: Dashboard to compare "System vs Invoice".
