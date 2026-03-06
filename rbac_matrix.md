# LojiNext: RBAC (Role-Based Access Control) Matrix

LojiNext sisteminde "Sovereign Security Service" üzerinden yönetilen Rol/Yetki matrisi ve kullanım kuralları aşağıda tanımlanmıştır.

## 1. Temel Roller ve Genel Yetki Düzeyleri (Legacy Bitwise)

Varsayılan olarak roller enum (`Permission` sınıfı) bazında atanır.

- **User**: Sadece `Permission.READ`
- **Driver**: Sadece `Permission.READ` (Filtreli izolasyon ile sadece kendisine ait verileri görür)
- **Admin**: `READ | WRITE | DELETE | ADMIN` (Tüm operasyonel işlemler, ancak sistem ayarları değil)
- **SuperAdmin**: `*` (Tüm yetkiler, şirket ayarları, master data değiştirme)

## 2. Granüler Yetki (Granular Permissions) Matrisi

Frontend ve Backend'de bileşen/endpoint gizleme düzeyindeki spesifik string bazlı yetkiler:

| Özellik / Endpoint         | Gerekli Granüler Yetki (String Key)      | Admin |    Driver    | Açıklama                                         |
| :------------------------- | :--------------------------------------- | :---: | :----------: | :----------------------------------------------- |
| **Seferler Listesi**       | `sefer:read`                             |  ✅   | ✅ (Sınırlı) | Şöför sadece atanmış olduğu seferleri görebilir. |
| **Yeni Sefer Ekleme**      | `sefer:write`                            |  ✅   |      ❌      |                                                  |
| **Dönüş Seferi**           | `sefer:write` veya `sefer:action:return` |  ✅   |      ❌      |                                                  |
| **Sefer Silme**            | `sefer:delete`                           |  ✅   |      ❌      |                                                  |
| **Toplu Excel İçe Aktar**  | `sefer:import`                           |  ✅   |      ❌      | Özel bulk aktarım yetkisi.                       |
| **Yakıt Verisi Düzenleme** | `yakit:write`                            |  ✅   |      ❌      |                                                  |

## 3. Backend Entegrasyonu (FastAPI)

Dependency Injection kullanarak route seviyesi erişim kontrolü sağlanmıştır:

```python
from app.api.deps import require_permissions

@router.post("/")
async def create_sefer(
    sefer: SeferCreate,
    current_user: Kullanici = Depends(require_permissions(["sefer:write"]))
):
    ...
```

## 4. Frontend Bileşen Gizleme / Devre Dışı Bırakma (React)

Kullanıcının `roles` veya `permissions` dizisi üzerinden bileşen render engellenmelidir:

```tsx
// useAuth.ts içerisindeki hook üzerinden
const { hasPermission } = useAuth();

// Bileşen UI içinde:
{
  hasPermission("sefer:write") && (
    <Button onClick={handleAddSefer}>Yeni Sefer</Button>
  );
}
```
