# API Güvenlik ve Yetkilendirme Test Planı (Detaylı)

## 🛡️ Test Stratejisi

Bu plan, uygulamanın güvenlik katmanını şansa bırakmadan, sistematik olarak (Automated + Manual) test etmeyi hedefler. Sadece "çalışıyor mu" değil, "kırılıyor mu" sorusunu soracağız.

---

## 1. Test Matrisi (Role-Based Access Control - RBAC)

Aşağıdaki matris, hangi rolün hangi işleme yetkisi olduğunu tanımlar:

| Endpoint             | Metod  | Anonim   | User (Şoför)     | Admin | Beklenen Güvenlik                       |
| -------------------- | ------ | -------- | ---------------- | ----- | --------------------------------------- |
| `/api/v1/login`      | POST   | ✅       | ✅               | ✅    | Rate Limit (5 req/min)                  |
| `/api/v1/trips`      | GET    | ❌ (401) | ✅ (Read Only)\* | ✅    | \*User sadece kendi seferlerini görmeli |
| `/api/v1/trips`      | POST   | ❌ (401) | ❌ (403)         | ✅    | Sadece Admin sefer atayabilir           |
| `/api/v1/trips/{id}` | PUT    | ❌ (401) | ❌ (403)         | ✅    | Sadece Admin güncelleyebilir            |
| `/api/v1/trips/{id}` | DELETE | ❌ (401) | ❌ (403)         | ✅    | Hard Delete Sadece Admin                |
| `/api/v1/users`      | GET    | ❌ (401) | ❌ (403)         | ✅    | Hassas veri (User List)                 |
| `/api/v1/audit/logs` | GET    | ❌ (401) | ❌ (403)         | ✅    | Audit logları gizli olmalı              |

---

## 2. Detaylı Senaryolar & Edge Case'ler

### A. Kimlik Doğrulama (Authentication) - "Kapı Kontrolü"

_Amaç: Geçersiz kimliklerle içeri girilemediğini kanıtlamak._

1.  **Null Token Testi**: Header olmadan istek at. -> `401 Unauthorized`
2.  **Malformed Token**: `Authorization: Bearer bozuk.token.yapisi` -> `401 Unauthorized` (422 değil!)
3.  **Expired Token**: Süresi dolmuş token ile işlem yap. -> `401 Unauthorized`
4.  **Wrong Secret**: Başka bir secret key ile imzalanmış (ama yapısı geçerli) token. -> `401 Unauthorized`

### B. Yetkilendirme (Authorization) - "Oda Kontrolü"

_Amaç: İçeri girenin sadece yetkisi olan odaya girebildiğini kanıtlamak._

1.  **Yetki Yükseltme (Privilege Escalation)**:
    - `User` rolündeki token ile `/api/v1/users` (Admin only) endpointine erişmeyi dene.
    - _Başarı Kriteri_: Kesinlikle `403 Forbidden` dönmeli. Veri ASLA dönmemeli.
2.  **ID Enumeration (ID Tarama)**:
    - `User` rolüyle `/api/v1/trips/99999` (Başkasına ait veya olmayan sefer) iste.
    - _Başarı Kriteri_: `404 Not Found` (Güvenli) veya `403 Forbidden`.

### C. Veri Bütünlüğü ve Validasyon

1.  **SQL Injection Denemesi**:
    - Login endpointine `username: "admin' OR '1'='1"` gönder.
    - _Başarı Kriteri_: Giriş BAŞARISIZ olmalı.
2.  **XSS / Payload Denemesi**:
    - Sefer oluştururken `cikis_yeri: "<script>alert(1)</script>"` gönder.
    - _Başarı Kriteri_: Veri temizlenmeli veya olduğu gibi text olarak saklanmalı (çalışmamalı).
3.  **Negatif Sayı Kontrolü**:
    - `mesafe_km: -100` gönder.
    - _Başarı Kriteri_: `422 Unprocessable Entity` (Pydantic validasyonu).

---

## 3. Otomasyon Scripti Taslağı (`tests/security/run_auth_tests.py`)

Manuel test hataya açıktır. Aşağıdaki script ile tüm senaryolar saniyeler içinde taranacak:

```python
def run_security_suite():
    print("🚀 Güvenlik Testleri Başlıyor...")

    # 1. Admin & User Token Al
    admin_token = login("admin", "admin123")
    user_token = login("sofor1", "123456")

    # 2. Yetkisiz Erişim Testi
    assert_status(get("/trips", token=None), 401, "No Token")
    assert_status(get("/trips", token="invalid"), 401, "Bad Token")

    # 3. RBAC Testi (User admin endpointine gidiyor)
    assert_status(delete("/trips/1", token=user_token), 403, "User cannot delete")
    assert_status(post("/trips", token=user_token, data={...}), 403, "User cannot create")

    # 4. Veri Gizliliği
    response = get("/users", token=admin_token)
    assert "password" not in response.text, "Password hash leak detected!"

    print("✅ Tüm güvenlik testleri BAŞARILI.")
```

---

## 4. Eksiklik Analizi (Gap Analysis)

Şu anki kodda tespit edilen potansiyel riskler:

- **Rate Limiting**: `create_trip` dışında diğer endpointlerde (örn. Login) hız sınırı var mı?
- **User Isolation**: `get_sefer_service().get_all_paged` metodunda `current_user` rolüne göre filtreleme (Row Level Security) yapılıyor mu? (Kontrol Edilecek)

Bu plan onaylandığında, **Otomasyon Scripti** yazılarak çalıştırılacaktır.
