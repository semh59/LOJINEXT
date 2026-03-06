# LojiNext — Seferler Modülü Tam Denetim, Düzeltme ve Test Promptu

> **Bu prompt bir AI coding agent'a veya kıdemli geliştirici incelemesine yönelik yazılmıştır.**
> Seferler modülünün tüm katmanlarını (veritabanı, backend servis, API, frontend, güvenlik, performans) sırayla denetle, hataları ve eksikleri tespit et, düzelt ve test et.
> Her aşamayı tamamlamadan bir sonrakine geçme.

---

## GENEL TALİMATLAR

- Her aşamada önce **denetle**, sonra **düzelt**, sonra **test et**.
- Düzeltme yapmadan önce mevcut kodu tam oku — varsayımla hareket etme.
- Bir hata bulduğunda sadece o satırı değil, **aynı pattern'in başka yerlerde de geçip geçmediğini** kontrol et.
- Her düzeltme sonrası ilgili testi çalıştır, testi geçmeden ilerme.
- Bulguları `## BULGULAR` bölümüne kaydet: `[HATA]`, `[EKSİK]`, `[UYARI]`, `[TAMAM]` etiketleriyle.

---

## AŞAMA 1 — VERİTABANI KATMANI DENETİMİ

### 1.1 Şema Bütünlüğü

Aşağıdaki her maddeyi `seferler` tablosu ve migration dosyaları üzerinde kontrol et:

```
[ ] sefer_no alanında UNIQUE constraint var mı?
[ ] net_kg = dolu_agirlik_kg - bos_agirlik_kg tutarsızlığı oluşabilir mi?
    → Eğer computed column değilse, trigger veya CHECK constraint ile korunuyor mu?
[ ] mesafe_km için CHECK (mesafe_km > 0) kısıtı var mı?
[ ] bos_agirlik_kg, dolu_agirlik_kg için negatif değer engeli var mı?
[ ] ascent_m, descent_m alanları NULL kabul ediyor mu? Kabul ediyorsa varsayılan değer 0 mu?
[ ] tahmini_tuketim alanı NULL kabul ediyor mu? Ne zaman doluyor?
[ ] is_real alanının DEFAULT değeri nedir? True mu False mu?
[ ] rota_detay alanı JSONB mi, JSON mi? JSONB olmalı.
[ ] created_at, updated_at alanlarında DEFAULT now() ve ON UPDATE trigger var mı?
[ ] created_by_id, updated_by_id alanları var mı? FK ile users tablosuna bağlı mı?
[ ] iptal_nedeni alanı var mı? Sadece durum='İptal' olduğunda doluyor mu?
[ ] seferler_log audit tablosu var mı? Her UPDATE/DELETE'de trigger çalışıyor mu?
```

**Kontrol Sorguları — Çalıştır ve Sonuçları Kaydet:**

```sql
-- Unique constraint kontrolü
SELECT conname, contype FROM pg_constraint
WHERE conrelid = 'seferler'::regclass AND contype IN ('u', 'p');

-- Check constraint kontrolü
SELECT conname, consrc FROM pg_constraint
WHERE conrelid = 'seferler'::regclass AND contype = 'c';

-- Index listesi
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'seferler';

-- Trigger listesi
SELECT trigger_name, event_manipulation, action_timing
FROM information_schema.triggers WHERE event_object_table = 'seferler';

-- JSONB kontrolü
SELECT column_name, data_type, udt_name
FROM information_schema.columns
WHERE table_name = 'seferler' AND column_name = 'rota_detay';
```

**Beklenen Sonuçlar ve Düzeltmeler:**

Eğer `rota_detay` JSONB değil JSON ise:
```sql
-- Migration oluştur:
ALTER TABLE seferler ALTER COLUMN rota_detay TYPE JSONB
USING rota_detay::JSONB;
```

Eğer GIN index yoksa:
```sql
CREATE INDEX idx_seferler_rota_detay ON seferler USING GIN (rota_detay);
```

Eğer `sefer_no` UNIQUE değilse:
```sql
-- Önce duplicate kontrol et
SELECT sefer_no, COUNT(*) FROM seferler GROUP BY sefer_no HAVING COUNT(*) > 1;
-- Duplicate yoksa:
ALTER TABLE seferler ADD CONSTRAINT uq_seferler_sefer_no UNIQUE (sefer_no);
```

Eğer `net_kg` tutarsızlık riski varsa:
```sql
-- Tutarsız kayıt kontrolü
SELECT id, sefer_no, bos_agirlik_kg, dolu_agirlik_kg, net_kg
FROM seferler
WHERE net_kg != (dolu_agirlik_kg - bos_agirlik_kg)
  AND bos_agirlik_kg IS NOT NULL
  AND dolu_agirlik_kg IS NOT NULL;
```

### 1.2 Audit Log Tablosu

Eğer `seferler_log` tablosu ve trigger mevcut değilse oluştur:

```sql
CREATE TABLE IF NOT EXISTS seferler_log (
    id            BIGSERIAL PRIMARY KEY,
    sefer_id      INTEGER NOT NULL,
    operation     VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT','UPDATE','DELETE')),
    changed_by    INTEGER REFERENCES users(id),
    changed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    old_data      JSONB,
    new_data      JSONB
);

CREATE INDEX idx_seferler_log_sefer_id ON seferler_log(sefer_id);
CREATE INDEX idx_seferler_log_changed_at ON seferler_log(changed_at DESC);

CREATE OR REPLACE FUNCTION fn_seferler_audit()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO seferler_log(sefer_id, operation, changed_by, old_data, new_data)
    VALUES (
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        COALESCE(NEW.updated_by_id, OLD.updated_by_id),
        CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE row_to_json(OLD)::JSONB END,
        CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE row_to_json(NEW)::JSONB END
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_seferler_audit ON seferler;
CREATE TRIGGER trg_seferler_audit
AFTER INSERT OR UPDATE OR DELETE ON seferler
FOR EACH ROW EXECUTE FUNCTION fn_seferler_audit();
```

### 1.3 Materialized View Doğrulama

```sql
-- MV varlığını kontrol et
SELECT matviewname, definition FROM pg_matviews WHERE matviewname = 'sefer_istatistik_mv';

-- CONCURRENTLY için unique index zorunlu — kontrol et
SELECT indexname FROM pg_indexes
WHERE tablename = 'sefer_istatistik_mv' AND indexdef LIKE '%UNIQUE%';
```

Eğer unique index yoksa:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_sefer_istatistik_mv_id
ON sefer_istatistik_mv (id);  -- veya MV'nin primary key alanı
```

Refresh prosedürünü test et:
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY sefer_istatistik_mv;
-- Hata alınıyorsa CONCURRENTLY olmadan çalıştır ve unique index sorununu çöz
```

---

## AŞAMA 2 — BACKEND MODEL VE ŞEMA DENETİMİ

### 2.1 SQLAlchemy Model (`app/models/sefer.py`)

```
[ ] Tüm DB alanları model ile eşleşiyor mu? (created_by_id, updated_by_id, iptal_nedeni dahil)
[ ] relationship tanımları lazy="select" mi? N+1 riski için gözden geçir.
[ ] __repr__ metodu var mı? Debug kolaylığı için.
[ ] model üzerinde @validates decorator ile alan validasyonları var mı?
    → mesafe_km için: assert value > 0
    → net_kg için: dolu - bos kontrolü
[ ] Enum alanlar (durum) Python Enum sınıfı ile mi tanımlanmış?
    → String karşılaştırma hatalarını önler
```

**Kontrol Edilecek Kod Pattern'leri:**

```python
# YANLIŞ — String enum riski:
durum = Column(String, default="Planlandı")

# DOĞRU — Enum ile:
class SeferDurum(str, Enum):
    PLANLA = "Planlandı"
    YOLDA  = "Devam Ediyor"
    TAMAM  = "Tamam"
    IPTAL  = "İptal"

durum = Column(SQLEnum(SeferDurum), default=SeferDurum.PLANLA, nullable=False)
```

```python
# YANLIŞ — lazy loading ile N+1:
arac = relationship("Arac")

# DOĞRU — explicit lazy tanımı:
arac = relationship("Arac", lazy="select")  # veya "joined" ihtiyaca göre
```

### 2.2 Pydantic Şema (`app/schemas/sefer.py`)

```
[ ] SeferCreate şemasında hangi alanlar zorunlu, hangileri opsiyonel?
    → sefer_no: opsiyonel (backend üretiyor) mu, zorunlu mu? Tutarlı mı?
[ ] SeferUpdate şeması Optional alanlarla mı tanımlanmış?
[ ] SeferResponse şemasında ilişkisel alanlar (arac_plaka, sofor_ad) var mı?
[ ] Validator'lar eksiksiz mi?
    → cikis_yeri, varis_yeri için XSS temizleme validator'ı
    → mesafe_km > 0 kontrolü
    → tarih alanı future date kabul ediyor mu? Kabul etmemeli.
[ ] model_config = ConfigDict(from_attributes=True) tanımı var mı?
[ ] SeferBulkUpdateRequest şeması var mı? (Bulk Actions için)
[ ] BulkOperationResponse şeması var mı?
```

**Test Edilecek Validasyon Senaryoları:**

```python
# Negatif mesafe testi
data = SeferCreate(mesafe_km=-100, ...)
# → ValidationError bekleniyor

# XSS testi
data = SeferCreate(cikis_yeri="<script>alert('xss')</script>", ...)
# → Temizlenmiş string bekleniyor, hata değil

# Geçmiş tarih testi (geçerli olmalı)
data = SeferCreate(tarih=date(2020, 1, 1), ...)
# → Geçerli, sefer geçmişe eklenebilmeli

# Gelecek tarih testi (ne yapılıyor? Karar verilmeli)
data = SeferCreate(tarih=date(2030, 1, 1), ...)
# → Kabul mü, ret mi? Belirsizse kural koy.
```

---

## AŞAMA 3 — BACKEND SERVİS KATMANI DENETİMİ

### 3.1 SeferReadService

```
[ ] get_all metodunda pagination çalışıyor mu?
    → page=0 veya negatif page girilince ne olur?
    → limit=0 veya limit=10000 girilince ne olur? Üst limit var mı?
[ ] Filtreler SQL injection'a karşı korunuyor mu?
    → SQLAlchemy parametrik sorgu mu, string concat mi?
[ ] is_real=True filtresi listeleme sorgusunda var mı?
    → Sentetik veriler kullanıcıya görünmemeli
[ ] get_by_id metodunda sefer bulunamazsa ne dönüyor?
    → None mu, 404 exception mu? Tutarlı mı?
[ ] Soft delete edilmiş seferler listelemeye dahil ediliyor mu?
    → deleted_at IS NULL filtresi var mı?
```

**Limit Güvenlik Testi:**

```python
# Maksimum limit aşımı
result = sefer_read_service.get_all(page=1, limit=99999)
# → MAX_PAGE_LIMIT'e (örn. 500) clip edilmeli

# Negatif sayfa
result = sefer_read_service.get_all(page=-1, limit=20)
# → page=1 olarak normalize edilmeli veya ValidationError
```

### 3.2 SeferWriteService

**`add_sefer` Metodu:**

```
[ ] sefer_no üretimi çakışma güvenli mi?
    → Race condition: İki eş zamanlı istek aynı sefer_no'yu üretebilir mi?
    → DB UNIQUE constraint son savunma hattı olarak çalışıyor mu?
[ ] created_by_id kaydediliyor mu?
[ ] iptal_nedeni sadece durum='İptal' olduğunda zorunlu tutuluyor mu?
    → Diğer durumlarda iptal_nedeni gönderilirse ne olur? Temizleniyor mu?
```

**`update_sefer` Metodu:**

```
[ ] Partial update destekliyor mu? (sadece gönderilen alanlar güncelleniyor mu?)
[ ] updated_by_id güncelleniyor mu?
[ ] updated_at güncelleniyor mu? (trigger değil, uygulama katmanında da set edilmeli)
[ ] durum değişikliği geçerli transition'larla mı sınırlandırılmış?
```

**Geçerli Durum Geçiş Matrisi — Kontrol Et:**

```
Planlandı   → Devam Ediyor ✅
Planlandı   → İptal        ✅
Planlandı   → Tamam        ❓ (doğrudan geçiş mantıklı mı?)
Devam Ediyor → Tamam       ✅
Devam Ediyor → İptal       ✅
Devam Ediyor → Planlandı   ❌ (geri alınamaz)
Tamam        → herhangi   ❌ (final state)
İptal        → herhangi   ❌ (final state)
```

Eğer state machine uygulanmamışsa ekle:

```python
VALID_TRANSITIONS = {
    "Planlandı":      ["Devam Ediyor", "İptal"],
    "Devam Ediyor":   ["Tamam", "İptal"],
    "Tamam":          [],
    "İptal":          [],
}

def validate_status_transition(current: str, new: str) -> None:
    if new not in VALID_TRANSITIONS.get(current, []):
        raise ValueError(f"'{current}' → '{new}' geçişi geçersiz.")
```

**`delete_sefer` Metodu:**

```
[ ] Soft delete mi, hard delete mi?
[ ] Soft delete ise deleted_at ve deleted_by_id set ediliyor mu?
[ ] FK bağımlılık kontrolü yapılıyor mu? (yakıt kartları, analiz raporları)
[ ] Bağımlı kayıt varsa anlaşılır hata mesajı dönüyor mu?
```

**`create_return_trip` Metodu:**

```
[ ] sefer_no sonuna '-D' ekleniyor mu?
[ ] Kaynak sefer zaten '-D' ile bitiyorsa (dönüş seferinin dönüşü):
    → '-D-D' oluşmaması için guard var mı?
[ ] ascent_m ve descent_m ters çevriliyor mu?
[ ] bos_sefer=True set ediliyor mu?
[ ] bos_agirlik_kg ve dolu_agirlik_kg sıfırlanıyor mu?
[ ] net_kg ve ton sıfırlanıyor mu?
[ ] created_by_id audit için set ediliyor mu?
[ ] Kaynak sefer bulunamazsa 404 dönüyor mu?
[ ] Aynı seferden birden fazla dönüş seferi oluşturulabilir mi?
    → Buna izin verilmeli mi? Kural belirlenmeli.
```

**Test Senaryoları — create_return_trip:**

```python
# Normal senaryo
ref_sefer = Sefer(sefer_no="SF-2025-001", cikis_yeri="Ankara", varis_yeri="İzmir",
                  mesafe_km=600, ascent_m=1200, descent_m=800,
                  dolu_agirlik_kg=25000, net_kg=15000)
donus = create_return_trip(ref_sefer.id, user_id=1)

assert donus.sefer_no == "SF-2025-001-D"
assert donus.cikis_yeri == "İzmir"
assert donus.varis_yeri == "Ankara"
assert donus.mesafe_km == 600         # Aynı kalır
assert donus.ascent_m == 800          # Ters çevrildi
assert donus.descent_m == 1200        # Ters çevrildi
assert donus.bos_sefer == True
assert donus.dolu_agirlik_kg == 0
assert donus.net_kg == 0

# '-D' tekrar senaryosu — guard testi
donus_seferi = Sefer(sefer_no="SF-2025-001-D", ...)
donus2 = create_return_trip(donus_seferi.id, user_id=1)
assert donus2.sefer_no == "SF-2025-001-D-R"  # veya hata fırlat — kural ne?
```

### 3.3 SeferAnalizService

```
[ ] reconcile_costs metodu async mi çalışıyor?
    → Eğer sync ise FastAPI BackgroundTasks veya Celery'e taşı
[ ] Anomali tespiti eşiği hardcode mu, configüre edilebilir mi?
[ ] Anomali tespit edildiğinde DB'ye flag yazılıyor mu?
[ ] Anomali sonrası bildirim tetikleniyor mu? (NotificationService çağrısı)
[ ] is_real=False veriler analiz kapsamına dahil ediliyor mu?
    → Dahil edilmemelidir
```

---

## AŞAMA 4 — API ENDPOINT DENETİMİ

### 4.1 Genel Kontroller

Her endpoint için kontrol et:

```
[ ] HTTP method doğru mu? (GET/POST/PATCH/DELETE)
[ ] Response status code doğru mu?
    → Oluşturma: 201 Created
    → Güncelleme: 200 OK
    → Silme: 204 No Content
    → Async işlem başlatma: 202 Accepted
    → Bulunamadı: 404 Not Found
    → Yetki hatası: 403 Forbidden
    → Validasyon hatası: 422 Unprocessable Entity
[ ] Tüm endpoint'lerde authentication dependency var mı?
[ ] Kritik endpoint'lerde authorization (rol kontrolü) var mı?
[ ] Response şeması Pydantic model ile tanımlı mı? (dict dönmüyor)
[ ] Error response formatı tutarlı mı?
```

**Eksik veya Kontrol Edilmesi Gereken Endpoint'ler:**

```
GET    /api/v1/seferler                    → Listeleme (pagination, filtreler)
GET    /api/v1/seferler/{id}               → Tekil sefer
POST   /api/v1/seferler                    → Oluşturma
PATCH  /api/v1/seferler/{id}               → Güncelleme
DELETE /api/v1/seferler/{id}               → Silme
POST   /api/v1/seferler/{id}/return        → Dönüş seferi oluşturma
GET    /api/v1/seferler/stats              → İstatistikler (MV'den)
GET    /api/v1/seferler/{id}/timeline      → Zaman çizelgesi
GET    /api/v1/seferler/excel/export       → Excel export
POST   /api/v1/seferler/excel/import       → Toplu import
PATCH  /api/v1/seferler/bulk/status        → Toplu durum güncelleme
PATCH  /api/v1/seferler/bulk/cancel        → Toplu iptal
DELETE /api/v1/seferler/bulk               → Toplu silme
```

### 4.2 Export Endpoint Denetimi

```
[ ] MAX_EXPORT_LIMIT = 5000 uygulanıyor mu?
[ ] Limit aşıldığında 400 Bad Request + anlaşılır mesaj dönüyor mu?
[ ] StreamingResponse kullanılıyor mu?
[ ] Content-Disposition: attachment header set ediliyor mu?
[ ] Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
[ ] Dosya adı dinamik mi? (seferler_2025-03-04.xlsx gibi)
[ ] Filtreler export'a yansıyor mu? (sadece filtrelenmiş veri)
[ ] is_real=False kayıtlar export'a dahil mi? (edilmemeli)
```

**Export Yük Testi:**

```python
# 5001 satır isteği
response = client.get("/api/v1/seferler/excel/export?limit=5001")
assert response.status_code == 400
assert "5000" in response.json()["detail"]

# 5000 satır isteği (sınır değer)
response = client.get("/api/v1/seferler/excel/export?limit=5000")
assert response.status_code == 200
assert response.headers["content-type"] == "application/vnd.openxmlformats-..."
```

### 4.3 Import Endpoint Denetimi

```
[ ] Dosya tipi kontrolü var mı? (.xlsx dışı reddediliyor mu?)
[ ] Dosya boyutu limiti var mı?
[ ] Her satır bağımsız validate ediliyor mu?
[ ] Hata response'u satır bazında detay veriyor mu?
[ ] Başarılı/başarısız sayısı response'ta var mı?
[ ] Import transaction'ı: Hatalı satırlar atlanıp başarılılar commit mi,
    yoksa hepsi ya da hiç mi?
[ ] Import sonrası cache/MV güncelleniyor mu?
```

**Beklenen Import Response:**

```json
{
  "total_rows": 50,
  "success_count": 47,
  "failed_count": 3,
  "errors": [
    {"row": 5,  "field": "mesafe_km",  "value": "-100", "reason": "Pozitif değer olmalı"},
    {"row": 12, "field": "tarih",      "value": "abc",  "reason": "Geçersiz tarih formatı"},
    {"row": 31, "field": "arac_id",    "value": "9999", "reason": "Araç bulunamadı"}
  ]
}
```

### 4.4 Stats Endpoint Denetimi

```
[ ] MV'den mi, canlı tablodan mı çekiyor?
[ ] Yanıt süresi < 100ms mi? (EXPLAIN ANALYZE ile ölç)
[ ] last_updated timestamp dönüyor mu?
[ ] Filtre parametreleri MV'ye uygulanabiliyor mu?
    → MV önceden hesaplıysa dinamik filtre desteklenmiyor olabilir
    → Bu durumda fallback stratejisi nedir?
```

---

## AŞAMA 5 — GÜVENLİK DENETİMİ

### 5.1 Authentication ve Authorization

```
[ ] /seferler endpoint'leri anonim erişime kapalı mı?
[ ] JWT token doğrulama her istekte yapılıyor mu?
[ ] Token süresi dolmuşsa 401 mi dönüyor?
[ ] Silme endpoint'i sadece ADMIN rolüne açık mı?
[ ] İptal endpoint'i ADMIN ve SUPERVISOR'a açık mı?
[ ] Toplu işlem endpoint'leri yetki kontrolüne sahip mi?
[ ] Bir kullanıcı başka kullanıcının işlemini yapabilir mi?
    → user_id parametresi URL/body'de geçiliyorsa override riski var
```

**RBAC Kontrol Matrisi — Her Endpoint'i Test Et:**

```python
# Dispatcher rolü silme denemesi
headers = {"Authorization": f"Bearer {dispatcher_token}"}
response = client.delete("/api/v1/seferler/1", headers=headers)
assert response.status_code == 403

# Supervisor rolü iptal
headers = {"Authorization": f"Bearer {supervisor_token}"}
response = client.patch("/api/v1/seferler/1",
                        json={"durum": "İptal", "iptal_nedeni": "Test"},
                        headers=headers)
assert response.status_code == 200

# Anonim erişim
response = client.get("/api/v1/seferler")
assert response.status_code == 401
```

### 5.2 Input Validasyon ve Injection

```
[ ] Tüm string girdiler Pydantic ile validate ediliyor mu?
[ ] SQLAlchemy ORM kullanılıyor — raw SQL var mı?
    → Varsa parametrik mi, string concat mi?
[ ] stats endpoint'indeki raw text() sorgusu parametre injection'a kapalı mı?
[ ] File upload (import) — dosya içeriği sanitize ediliyor mu?
    → Excel formula injection: =CMD("rm -rf /") gibi değerler
[ ] Hata mesajları stack trace içeriyor mu? (production'da içermemeli)
```

**SQL Injection Testi:**

```python
# Filtre parametresine injection denemesi
response = client.get("/api/v1/seferler?durum=Tamam' OR '1'='1")
assert response.status_code in [200, 422]
# 200 ise sadece "Tamam" statüsündeki seferler gelmeli, tüm seferler değil

# sefer_no injection
response = client.get("/api/v1/seferler?sefer_no='; DROP TABLE seferler;--")
assert response.status_code in [200, 422]
# Tablo hâlâ var mı?
```

**Excel Formula Injection Testi:**

```python
# Import dosyasında formül içeren hücre
# Excel'de A1 = =HYPERLINK("http://evil.com","click")
# Import sonrası DB'de değer ne olarak kaydedilmeli?
# → Ham string olarak: "=HYPERLINK(..." değil, temizlenmiş değer
```

### 5.3 Rate Limiting

```
[ ] Import endpoint'inde rate limit var mı?
    → Aynı IP'den dakikada X istek sınırı
[ ] Export endpoint'inde rate limit var mı?
[ ] Bulk işlem endpoint'lerinde rate limit var mı?
```

---

## AŞAMA 6 — PERFORMANS DENETİMİ

### 6.1 Sorgu Performansı

Her kritik sorguyu `EXPLAIN ANALYZE` ile çalıştır:

```sql
-- Listeleme sorgusu (100k kayıtla test)
EXPLAIN ANALYZE
SELECT s.*, a.plaka, sf.ad, d.kodu
FROM seferler s
LEFT JOIN araclar a ON s.arac_id = a.id
LEFT JOIN soforler sf ON s.sofor_id = sf.id
LEFT JOIN dorseler d ON s.dorse_id = d.id
WHERE s.durum = 'Tamam'
  AND s.tarih BETWEEN '2025-01-01' AND '2025-03-31'
  AND s.is_real = TRUE
  AND s.deleted_at IS NULL
ORDER BY s.tarih DESC
LIMIT 50 OFFSET 0;
```

**Beklenen:**
- Seq Scan yoksa ✅
- Index Scan veya Bitmap Index Scan varsa ✅
- Execution time < 50ms (100k kayıt için)

Eğer Seq Scan varsa eksik index'leri ekle:

```sql
-- Sık filtrelenen alanlar için composite index
CREATE INDEX IF NOT EXISTS idx_seferler_durum_tarih
ON seferler(durum, tarih DESC)
WHERE deleted_at IS NULL AND is_real = TRUE;

-- Tarih bazlı sorgular için
CREATE INDEX IF NOT EXISTS idx_seferler_tarih
ON seferler(tarih DESC)
WHERE deleted_at IS NULL;
```

### 6.2 N+1 Sorgu Kontrolü

```python
# SQLAlchemy query log'larını aç
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# 20 sefer listele — kaç SQL sorgusu gönderildi?
seferler = sefer_read_service.get_all(page=1, limit=20)
# Beklenen: 1 sorgu (joinedload ile)
# Hatalı: 1 + 20*4 = 81 sorgu (her sefer için arac, sofor, dorse, guzergah ayrı ayrı)
```

### 6.3 Stats Endpoint Hız Testi

```python
import time

start = time.time()
response = client.get("/api/v1/seferler/stats")
elapsed = time.time() - start

assert response.status_code == 200
assert elapsed < 0.1  # 100ms altında olmalı
print(f"Stats yanıt süresi: {elapsed*1000:.1f}ms")
```

### 6.4 Export Bellek Testi

```python
import tracemalloc

tracemalloc.start()
response = client.get("/api/v1/seferler/excel/export?limit=5000")
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"Peak bellek: {peak / 1024 / 1024:.1f} MB")
assert peak < 100 * 1024 * 1024  # 100MB altında olmalı
```

---

## AŞAMA 7 — FRONTEND KATMANI DENETİMİ

### 7.1 React Query Konfigürasyonu

```
[ ] useQuery'de staleTime tanımlı mı? Kaç dakika?
[ ] stats query'si için ayrı staleTime var mı?
    → Stats MV'den geliyorsa daha uzun (30dk) olabilir
[ ] refetchIntervalInBackground: false set edilmiş mi?
[ ] Hata durumunda (API down) kullanıcıya anlaşılır mesaj gösteriliyor mu?
[ ] Loading state'leri skeleton loader ile gösteriliyor mu?
[ ] onError callback'leri tanımlı mı?
[ ] invalidateQueries doğru key'lerle çağrılıyor mu?
    → Sefer eklenince hem 'seferler' hem 'sefer-stats' invalidate olmalı
```

**Kontrol Edilecek Query Key'leri:**

```typescript
// Tutarsız key kullanımı riski — tüm useQuery çağrılarını kontrol et
['seferler', filters]           // Listeleme
['sefer', id]                   // Tekil
['sefer-stats', filters]        // İstatistikler
['sefer-timeline', id]          // Timeline
```

**Eğer key'ler tutarsızsa:**

```typescript
// queryKeys.ts dosyası oluştur — merkezi key yönetimi
export const seferKeys = {
  all:      ()              => ['seferler'] as const,
  list:     (filters: any)  => [...seferKeys.all(), 'list', filters] as const,
  detail:   (id: number)    => [...seferKeys.all(), 'detail', id] as const,
  stats:    (filters: any)  => [...seferKeys.all(), 'stats', filters] as const,
  timeline: (id: number)    => [...seferKeys.all(), 'timeline', id] as const,
};
```

### 7.2 Zustand Store Denetimi

```
[ ] useTripStore içinde tanımlı state alanları neler?
[ ] reset() fonksiyonu tüm alanları başlangıç değerine getiriyor mu?
[ ] useEffect içinde reset() mount/unmount'ta çağrılıyor mu?
[ ] Store içinde async işlem (API çağrısı) var mı?
    → Varsa react-query'ye taşınmalı (store sadece UI state tutmalı)
[ ] selectedTripIds için Set<number> mi, number[] mi kullanılıyor?
    → Set daha performanslı (O(1) lookup)
```

**Hatalı Pattern Tespiti:**

```typescript
// YANLIŞ — Store içinde API çağrısı:
const useTripStore = create((set) => ({
  fetchTrips: async () => {
    const data = await api.getTrips();  // ❌ Bu react-query'nin işi
    set({ trips: data });
  }
}));

// DOĞRU — Store sadece UI state:
const useTripStore = create((set) => ({
  selectedIds: new Set<number>(),
  isFormOpen: false,
  activeFilters: defaultFilters,
  reset: () => set(initialState),
  toggleSelect: (id: number) => set(state => {
    const next = new Set(state.selectedIds);
    next.has(id) ? next.delete(id) : next.add(id);
    return { selectedIds: next };
  }),
}));
```

### 7.3 Form ve Validasyon Denetimi

```
[ ] TripFormModal'da form validasyonu client-side var mı?
[ ] Validasyon backend ile tutarlı mı?
    → Backend Pydantic kuralları ile frontend Zod/Yup kuralları eşleşmeli
[ ] Form submit sırasında buton disable ediliyor mu? (çift submit önlemi)
[ ] API hatası formda gösteriliyor mu? (toast + field error)
[ ] İptal edildiğinde form state temizleniyor mu?
[ ] Form açıkken sayfa yenilenirse veri kaybı uyarısı var mı?
```

**Çift Submit Testi:**

```typescript
// Form submit butonuna hızla iki kez tıkla
// İki aynı sefer oluşturulmamalı
// Buton submit sırasında disabled olmalı
const { mutate, isLoading } = useMutation(createSefer);

<button
  onClick={() => mutate(formData)}
  disabled={isLoading}  // Bu satır var mı?
>
  {isLoading ? 'Kaydediliyor...' : 'Kaydet'}
</button>
```

### 7.4 Optimistic Update Denetimi

```
[ ] onMutate: Optimistic update uygulanıyor mu?
[ ] onError: Rollback yapılıyor mu?
[ ] onSettled: invalidateQueries çağrılıyor mu?
[ ] Optimistic update sırasında ID için geçici ID üretiliyor mu?
    → Backend'den gelen gerçek ID ile sonradan eşleşmeli
```

**Kontrol Edilecek useMutation Yapısı:**

```typescript
const mutation = useMutation({
  mutationFn: createSefer,
  onMutate: async (newSefer) => {
    await queryClient.cancelQueries({ queryKey: seferKeys.list(filters) });
    const previousData = queryClient.getQueryData(seferKeys.list(filters));

    queryClient.setQueryData(seferKeys.list(filters), (old: any) => ({
      ...old,
      items: [{ ...newSefer, id: Date.now() }, ...old.items]  // Geçici ID
    }));

    return { previousData };  // rollback için sakla
  },
  onError: (err, newSefer, context) => {
    // Rollback
    queryClient.setQueryData(seferKeys.list(filters), context?.previousData);
    toast.error('Sefer eklenemedi');
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: seferKeys.all() });
  },
});

// Bu yapı tam mı? Eksik adım var mı?
```

### 7.5 TypeScript Tip Güvenliği

```
[ ] any tipi kaç yerde kullanılıyor?
    → Her any için gerçek tip tanımla
[ ] API response tipleri tanımlanmış mı?
[ ] Sefer model interface'i DB şemasıyla tutarlı mı?
    → Yeni eklenen DB alanları (created_by_id, iptal_nedeni) TypeScript'te var mı?
[ ] Enum değerleri TypeScript'te de enum olarak tanımlı mı?
```

```bash
# TypeScript hata sayısını kontrol et
npx tsc --noEmit 2>&1 | grep "error TS" | wc -l
# Hedef: 0
```

### 7.6 Erişilebilirlik (Accessibility)

```
[ ] Tablo başlıklarında scope="col" var mı?
[ ] Butonlarda aria-label tanımlı mı? (sadece ikon olan butonlar için)
[ ] Modal açıldığında focus trap çalışıyor mu?
[ ] Klavye navigasyonu (Tab/Enter/Escape) çalışıyor mu?
[ ] Hata mesajları aria-live region'da mı?
```

---

## AŞAMA 8 — ENTEGRASYON TESTLERİ

### 8.1 Tam Akış Testleri (E2E Senaryolar)

**Senaryo 1: Yeni Sefer Oluşturma ve Dönüş Seferi**

```python
def test_sefer_create_and_return():
    # 1. Sefer oluştur
    response = client.post("/api/v1/seferler", json={
        "cikis_yeri": "Ankara", "varis_yeri": "İzmir",
        "mesafe_km": 600, "tarih": "2025-03-04",
        "arac_id": 1, "sofor_id": 1
    }, headers=admin_headers)
    assert response.status_code == 201
    sefer_id = response.json()["id"]
    sefer_no = response.json()["sefer_no"]

    # 2. Audit log kontrolü
    log = db.query(SeferLog).filter_by(sefer_id=sefer_id, operation="INSERT").first()
    assert log is not None
    assert log.changed_by == admin_user_id

    # 3. Dönüş seferi oluştur
    response = client.post(f"/api/v1/seferler/{sefer_id}/return",
                           headers=admin_headers)
    assert response.status_code == 201
    donus = response.json()
    assert donus["sefer_no"] == f"{sefer_no}-D"
    assert donus["cikis_yeri"] == "İzmir"
    assert donus["varis_yeri"] == "Ankara"
    assert donus["bos_sefer"] == True

    # 4. Stats güncellenmiş mi?
    stats = client.get("/api/v1/seferler/stats").json()
    assert stats["total_count"] >= 2
```

**Senaryo 2: Durum Geçişi ve İptal**

```python
def test_status_transition_and_cancel():
    sefer_id = create_test_sefer()  # Planlandı

    # Geçersiz geçiş — Planlandı → Tamam (izin verilmemeli)
    response = client.patch(f"/api/v1/seferler/{sefer_id}",
                            json={"durum": "Tamam"}, headers=supervisor_headers)
    assert response.status_code == 422  # veya 400

    # Geçerli geçiş — Planlandı → Devam Ediyor
    response = client.patch(f"/api/v1/seferler/{sefer_id}",
                            json={"durum": "Devam Ediyor"}, headers=supervisor_headers)
    assert response.status_code == 200

    # İptal — iptal_nedeni zorunlu
    response = client.patch(f"/api/v1/seferler/{sefer_id}",
                            json={"durum": "İptal"}, headers=supervisor_headers)
    assert response.status_code == 422  # iptal_nedeni eksik

    # İptal — iptal_nedeni ile
    response = client.patch(f"/api/v1/seferler/{sefer_id}",
                            json={"durum": "İptal", "iptal_nedeni": "Araç arızası"},
                            headers=supervisor_headers)
    assert response.status_code == 200
```

**Senaryo 3: Silme Bağımlılık Kontrolü**

```python
def test_delete_with_dependency():
    sefer_id = create_test_sefer_with_fuel_card()  # Yakıt kartı bağlı

    response = client.delete(f"/api/v1/seferler/{sefer_id}",
                             headers=admin_headers)
    assert response.status_code == 409  # Conflict
    assert "yakıt" in response.json()["detail"].lower()

    # Bağımlılığı kaldır
    remove_fuel_card(sefer_id)

    # Tekrar dene
    response = client.delete(f"/api/v1/seferler/{sefer_id}",
                             headers=admin_headers)
    assert response.status_code == 204

    # Soft delete — hâlâ DB'de var mı?
    sefer = db.query(Sefer).filter_by(id=sefer_id).first()
    assert sefer is not None
    assert sefer.deleted_at is not None
```

**Senaryo 4: Yetki Sınırları**

```python
def test_rbac_boundaries():
    roles = {
        "admin":      (admin_token,      {"create": 201, "delete": 204, "cancel": 200, "bulk_delete": 204}),
        "supervisor": (supervisor_token, {"create": 201, "delete": 403, "cancel": 200, "bulk_delete": 403}),
        "dispatcher": (dispatcher_token, {"create": 201, "delete": 403, "cancel": 403, "bulk_delete": 403}),
        "accountant":  (accountant_token, {"create": 403, "delete": 403, "cancel": 403, "bulk_delete": 403}),
    }

    for role, (token, expected) in roles.items():
        headers = {"Authorization": f"Bearer {token}"}
        sefer_id = create_test_sefer()

        r = client.post("/api/v1/seferler", json=valid_sefer_data, headers=headers)
        assert r.status_code == expected["create"], f"{role} create failed"

        r = client.delete(f"/api/v1/seferler/{sefer_id}", headers=headers)
        assert r.status_code == expected["delete"], f"{role} delete failed"
```

---

## AŞAMA 9 — YÜK VE STRES TESTLERİ

### 9.1 Eş Zamanlı İstek Testi

```python
import asyncio
import httpx

async def test_concurrent_sefer_create():
    """Aynı sefer_no ile eş zamanlı 10 istek — DB unique constraint çalışıyor mu?"""
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post("/api/v1/seferler",
                        json={**valid_sefer_data, "sefer_no": "CONCURRENT-001"},
                        headers=admin_headers)
            for _ in range(10)
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    success = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 201]
    assert len(success) == 1  # Sadece 1 başarılı olmalı
```

### 9.2 Büyük Veri Testi

```bash
# 100.000 sefer ekle ve performansı ölç
python scripts/seed_test_data.py --count 100000

# Listeleme hızı
time curl "http://localhost:8000/api/v1/seferler?page=1&limit=50"
# Hedef: < 200ms

# Stats hızı
time curl "http://localhost:8000/api/v1/seferler/stats"
# Hedef: < 100ms (MV'den geliyor)

# Export hızı (5000 satır)
time curl "http://localhost:8000/api/v1/seferler/excel/export?limit=5000" -o /dev/null
# Hedef: < 5 saniye
```

---

## AŞAMA 10 — FRONTEND GÖRSEL VE UX DENETİMİ

```
[ ] Tablo boş veri durumunda anlaşılır mesaj gösteriyor mu?
    → "Sefer bulunamadı" + "Yeni Sefer Ekle" CTA butonu
[ ] Hata durumunda (API 500) kullanıcıya ne gösteriliyor?
    → Teknik hata mesajı değil, anlaşılır metin
[ ] Pagination çalışıyor mu? Son sayfada "Sonraki" butonu disable mi?
[ ] Filtreler temizlenince tüm filtreler sıfırlanıyor mu?
[ ] Sütun sıralaması (sort) doğru çalışıyor mu?
    → Ascending → Descending → Sırasız döngüsü
[ ] Uzun metin içeren seferler (uzun cikis_yeri) tabloda taşıyor mu?
    → text-overflow: ellipsis + tooltip uygulanmış mı?
[ ] Yükleme sırasında eski veri mi yoksa skeleton mi gösteriliyor?
[ ] Mobil boyutta (768px) tablo kullanılabilir mi? (mobil uygulama olmasa da tablet olabilir)
[ ] Dark mode desteği var mı? Varsa eksik renk ataması var mı?
```

**Görsel Regresyon Testi:**

```bash
# Playwright veya Cypress ile screenshot al
npx playwright test --reporter=html

# Kritik durumlar için screenshot karşılaştırması:
# - Boş tablo
# - 50 satırlı tablo
# - Filtre uygulanmış tablo
# - Form modal açık
# - Hata durumu
```

---

## BULGULAR — RAPOR ŞABLONU

Bu bölümü denetim tamamlandıkça doldur:

```
## VERİTABANI
[HATA]  sefer_no UNIQUE constraint eksik — migration oluşturuldu
[TAMAM] GIN index mevcut
[EKSİK] seferler_log trigger tablosu yok — oluşturuldu
[UYARI] net_kg computed column değil, trigger ile korunmuyor

## BACKEND MODEL
[TAMAM] Enum kullanımı doğru
[HATA]  updated_by_id model'de yok — eklendi

## SERVİS KATMANI
[HATA]  create_return_trip: '-D' tekrar guard eksik — eklendi
[TAMAM] Soft delete çalışıyor
[EKSİK] Durum geçiş matrisi uygulanmamış — state machine eklendi

## API
[HATA]  Import endpoint satır bazında hata dönmüyor — düzeltildi
[TAMAM] Export limit 5000 uygulanmış
[EKSİK] Timeline endpoint yok — Faz 4'e eklendi

## GÜVENLİK
[TAMAM] JWT auth tüm endpoint'lerde mevcut
[HATA]  Dispatcher rolü seferi silebiliyor — RBAC düzeltildi

## PERFORMANS
[UYARI] Listeleme sorgusunda Seq Scan — composite index eklendi
[TAMAM] Stats < 10ms (MV'den geliyor)

## FRONTEND
[HATA]  queryKey tutarsızlığı — seferKeys.ts oluşturuldu
[TAMAM] Optimistic update + rollback çalışıyor
[EKSİK] TypeScript 14 any kullanımı — tipler tanımlandı
```

---

## TAMAMLANMA KRİTERLERİ

Tüm aşamalar tamamlandığında aşağıdaki kriterlerin tamamı sağlanmış olmalı:

```
[ ] Hiç [HATA] etiketi kalmamış
[ ] Kritik [EKSİK] etiketleri kapatılmış
[ ] Tüm unit testler geçiyor
[ ] Tüm entegrasyon testleri geçiyor
[ ] TypeScript error sayısı: 0
[ ] Listeleme sorgusu < 200ms (100k kayıt)
[ ] Stats endpoint < 100ms
[ ] Export (5000 satır) < 5 saniye ve < 100MB bellek
[ ] Eş zamanlı istek testi: Duplicate sefer oluşturulmuyor
[ ] RBAC matrisi tüm roller için doğrulandı
[ ] Audit log: Her CREATE/UPDATE/DELETE kayıt altında
[ ] Dönüş seferi: '-D' tekrar guard çalışıyor
[ ] Import: Satır bazında hata raporlaması çalışıyor
```

---

*LojiNext — Seferler Modülü Tam Denetim Promptu v1.0 | Gizli — Yalnızca İç Kullanım*
