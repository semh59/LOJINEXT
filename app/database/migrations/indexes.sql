-- Phase 9: Database Indexes for Optimization
-- Improves filter performance on main tables

-- Seferler: Date filtering is most common
CREATE INDEX IF NOT EXISTS idx_seferler_tarih ON seferler(tarih DESC);

-- Seferler: Driver/Vehicle filtering
CREATE INDEX IF NOT EXISTS idx_seferler_sofor_id ON seferler(sofor_id);
CREATE INDEX IF NOT EXISTS idx_seferler_arac_id ON seferler(arac_id);

-- Yakit: Vehicle filtering and Date sorting
CREATE INDEX IF NOT EXISTS idx_yakit_arac_tarih ON yakit_alimlari(arac_id, tarih DESC);

-- Sofor: SearchByName
CREATE INDEX IF NOT EXISTS idx_soforler_ad_soyad ON soforler(ad_soyad);

-- Analiz: Faster lookups
CREATE INDEX IF NOT EXISTS idx_yakit_periyodu_arac ON yakit_periyotlari(arac_id, alim1_tarih DESC);
