# Skill: Database & Migrations (Elite)

## Ne Zaman Yükle
- Database şeması, PostgreSQL optimizasyonu veya Alembic migrasyonu yaparken.

## Alembic Standartları
- Migration dosyası oluşturma: `alembic revision --autogenerate -m "mesaj"`
- Migration dosyaları manuel gözden geçirilmelidir.
- `downgrade` fonksiyonları mutlaka yazılmalıdır.

## LOJINEXT Şema Kuralları
- Tüm foreign key'ler için index oluşturulmalıdır.
- Silme işlemleri `aktif: Mapped[bool] = mapped_column(default=True)` ile soft-delete olarak yapılmalıdır.
- Zaman alanları için `created_at` ve `updated_at` zorunludur.

## Yapma
- Manuel "ALTER TABLE" komutu çalıştırma (Alembic kullan).
- Data migration yaparken transaction'ı çok uzun süre açık tutma.
