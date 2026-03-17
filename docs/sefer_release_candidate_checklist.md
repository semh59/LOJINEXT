# Seferler Release Candidate Checklist

> Mevcut Durum (2026-03-15): 49 backend test basarisiz. Bu gate henuz
> karsilanmiyor. Gate kosullari programin sonunda gecerli.

## 1) Disposable Migration Runbook

1. Gerekli env'ler:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `ADMIN_PASSWORD`
   - `SUPER_ADMIN_USERNAME` (opsiyonel, default `skara`)
2. Disposable hedef veritabaninda public schema'yi sifirla.
3. `alembic upgrade head`
4. `alembic heads` (beklenen: tek head = `0002_seed_and_bootstrap`)
5. `alembic current --verbose`
6. `alembic --raiseerr check`
7. Minimum bootstrap dogrulama:
   - `roller` tablosunda `super_admin`
   - `kullanicilar` tablosunda bootstrap admin kullanicisi
   - `alembic_version = 0002_seed_and_bootstrap`

## 2) Recovery Plan

1. Resmi rollback yolu `alembic downgrade -1` degildir.
2. Sorun halinde disposable DB icin resmi yol:
   - public schema reset
   - `alembic upgrade head`
   - bootstrap kayit dogrulama
3. Geri kurulum sonrasi smoke test tekrar calistir.

## 3) Smoke Test Listesi

1. Sefer olusturma/guncelleme/silme.
2. Bulk iptal (`iptal_nedeni` persist).
3. Bulk delete body contract: `{ "sefer_ids": [...] }`.
4. `GET /trips/stats` response key contract.
5. `GET /trips/analytics/fuel-performance` response key contract.
6. `GET /trips/{id}/timeline` normalized event shape.
7. Frontend:
   - Sefer listesi yukleniyor.
   - Hata ekrani (`Veri Yuklenemedi`) + `Yeniden Dene`.
   - Pagination NaN yok.

## 4) Mandatory Gate

- Alembic: `upgrade head`, `heads`, `current --verbose`, `--raiseerr check` yesil.
- Backend: unit + integration + contract testleri yesil.
- Frontend: test + build + lint yesil.
- Sozlesme sapmasi: 0.
