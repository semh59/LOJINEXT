-- Migration 003: Depo Durumu ve PRAGMA Optimizasyonları
-- Tarih: 2026-01-07

-- 1. Yakıt alımlarına depo_durumu kolonu ekle
ALTER TABLE yakit_alimlari ADD COLUMN depo_durumu TEXT DEFAULT 'Bilinmiyor';

-- 2. PRAGMA optimizasyonları (her bağlantıda çalıştırılmalı - bu sadece referans)
-- PRAGMA journal_mode = WAL;
-- PRAGMA synchronous = NORMAL;
-- PRAGMA cache_size = -64000;
-- PRAGMA temp_store = MEMORY;
-- PRAGMA mmap_size = 268435456;

-- 3. Yeni indeks: depo durumu ile filtreler için
CREATE INDEX IF NOT EXISTS idx_yakit_depo_durumu ON yakit_alimlari(depo_durumu);

-- 4. Araç yaşı için composite index (performans sorgularında kullanılacak)
CREATE INDEX IF NOT EXISTS idx_sefer_arac_sofor ON seferler(arac_id, sofor_id);
