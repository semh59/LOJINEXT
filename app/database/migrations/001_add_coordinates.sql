-- Migration 001: Koordinat ve Güzergah Geliştirmeleri
-- TIR Yakıt Takip Sistemi
-- Tarih: 2026-01-05

-- Lokasyonlar tablosuna koordinat alanları ekle
ALTER TABLE lokasyonlar ADD COLUMN cikis_lat REAL;
ALTER TABLE lokasyonlar ADD COLUMN cikis_lon REAL;
ALTER TABLE lokasyonlar ADD COLUMN varis_lat REAL;
ALTER TABLE lokasyonlar ADD COLUMN varis_lon REAL;

-- API'den alınan mesafe ve süre (cache)
ALTER TABLE lokasyonlar ADD COLUMN api_mesafe_km INTEGER;
ALTER TABLE lokasyonlar ADD COLUMN api_sure_saat REAL;

-- Tahmini yakıt tüketimi (formülden)
ALTER TABLE lokasyonlar ADD COLUMN tahmini_yakit_lt REAL;

-- Son API çağrısı tarihi (cache invalidation için)
ALTER TABLE lokasyonlar ADD COLUMN last_api_call DATETIME;

-- Araç bazlı yakıt formül tablosu (AI/ML için)
CREATE TABLE IF NOT EXISTS yakit_formul (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arac_id INTEGER NOT NULL,
    base_consumption REAL NOT NULL DEFAULT 0.32,  -- L/km base tüketim
    weight_factor REAL NOT NULL DEFAULT 0.015,    -- Ton başına ek tüketim faktörü
    route_difficulty REAL NOT NULL DEFAULT 1.0,   -- Güzergah zorluğu çarpanı
    r_squared REAL DEFAULT 0,                     -- Model doğruluğu (R²)
    sample_count INTEGER DEFAULT 0,               -- Eğitimde kullanılan örnek sayısı
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (arac_id) REFERENCES araclar(id),
    UNIQUE(arac_id)
);

-- İndeks oluştur
CREATE INDEX IF NOT EXISTS idx_lokasyon_koordinat ON lokasyonlar(cikis_lat, cikis_lon, varis_lat, varis_lon);
