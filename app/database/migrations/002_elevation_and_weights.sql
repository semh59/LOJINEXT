-- Migration 002: Yükseklik Profili ve Sefer Ağırlık Detayları
-- TIR Yakıt Takip Sistemi
-- Tarih: 2026-01-05

-- Lokasyonlar tablosuna yükseklik verileri ekle (OpenRouteService elevation)
ALTER TABLE lokasyonlar ADD COLUMN ascent_m REAL DEFAULT 0;    -- Toplam bayır çıkış (metre)
ALTER TABLE lokasyonlar ADD COLUMN descent_m REAL DEFAULT 0;   -- Toplam bayır iniş (metre)

-- Seferler tablosuna detaylı ağırlık bilgileri ekle
-- (Kullanıcı her seferde boş, dolu ve net ağırlık ayrı ayrı girecek)
ALTER TABLE seferler ADD COLUMN bos_agirlik_kg INTEGER DEFAULT 0;   -- Boş araç ağırlığı
ALTER TABLE seferler ADD COLUMN dolu_agirlik_kg INTEGER DEFAULT 0;  -- Dolu araç ağırlığı
-- net_kg zaten mevcut (dolu - bos = net)

-- İndeks
CREATE INDEX IF NOT EXISTS idx_lokasyon_elevation ON lokasyonlar(ascent_m, descent_m);
