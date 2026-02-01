-- Migration 004: Composite Indexler
-- Tarih: 2026-01-07
-- Amaç: Sorgu performansını artırmak için composite indexler

-- 1. Sefer sorguları için (araç + tarih)
CREATE INDEX IF NOT EXISTS idx_sefer_arac_tarih ON seferler(arac_id, tarih DESC);

-- 2. Şoför seferleri için (şoför + tarih)
CREATE INDEX IF NOT EXISTS idx_sefer_sofor_tarih ON seferler(sofor_id, tarih DESC);

-- 3. Yakıt alımları için (araç + km)
CREATE INDEX IF NOT EXISTS idx_yakit_arac_km ON yakit_alimlari(arac_id, km_sayac);

-- 4. Tüketim sorguları için (partial index - sadece tüketim olanlar)
CREATE INDEX IF NOT EXISTS idx_sefer_tuketim ON seferler(tuketim) WHERE tuketim IS NOT NULL;

-- 5. Güzergah sorguları için
CREATE INDEX IF NOT EXISTS idx_sefer_guzergah ON seferler(cikis_yeri, varis_yeri);

-- 6. Lokasyon route lookup için
CREATE INDEX IF NOT EXISTS idx_lokasyon_route ON lokasyonlar(cikis_yeri, varis_yeri);
