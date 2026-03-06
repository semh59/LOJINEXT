# Skill: Database Migration (Alembic)

## Ne Zaman Yükle
- Tablo yapısı değiştiğinde
- Yeni tablo eklendiğinde
- Index veya Constraint eklenirken

## Bu Skill Ne Bilir

### Standartlar
- `alembic/versions/` altındaki dosyaları incele.
- `alembic revision --autogenerate -m "mesaj"` ile başla.
- Üretilen scripti mutlaka review et (Batch mode gerekebilir).
- Downgrade adımlarını boş bırakma.

### Workflow
1. `models.py` güncelle.
2. Migrasyon oluştur.
3. Migrasyonu test et (`alembic upgrade head`).
4. `models.py` ve migrasyonu birlikte commit et.

## Yapma
- Doğrudan DB üzerinde manuel şema değişikliği yapma.
- Mevcut migrasyon dosyalarını modifiye etme (Yeni revision oluştur).
