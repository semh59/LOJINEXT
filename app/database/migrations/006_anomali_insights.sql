-- Migration 006: Anomali ve Insight Tabloları
-- Tarih: 2026-01-07
-- Amaç: Anomali tespiti ve otomatik insight kayıtları

-- Anomali kayıtları
CREATE TABLE IF NOT EXISTS anomaliler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tarih DATE NOT NULL,
    tip TEXT NOT NULL,  -- 'tuketim', 'maliyet', 'sefer'
    kaynak_tip TEXT NOT NULL,  -- 'arac', 'sofor', 'sefer', 'yakit'
    kaynak_id INTEGER,
    deger REAL,
    beklenen_deger REAL,
    sapma_yuzde REAL,
    severity TEXT DEFAULT 'medium',  -- 'low', 'medium', 'high', 'critical'
    aciklama TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insight kayıtları
CREATE TABLE IF NOT EXISTS insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tarih DATE NOT NULL,
    tip TEXT NOT NULL,  -- 'uyari', 'iyilesme', 'oneri', 'trend'
    kaynak_tip TEXT,  -- 'arac', 'sofor', 'filo'
    kaynak_id INTEGER,
    mesaj TEXT NOT NULL,
    onem_puani INTEGER DEFAULT 50,  -- 0-100
    okundu INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_anomali_tarih ON anomaliler(tarih DESC);
CREATE INDEX IF NOT EXISTS idx_anomali_kaynak ON anomaliler(kaynak_tip, kaynak_id);
CREATE INDEX IF NOT EXISTS idx_anomali_severity ON anomaliler(severity);
CREATE INDEX IF NOT EXISTS idx_insight_tarih ON insights(tarih DESC);
CREATE INDEX IF NOT EXISTS idx_insight_okunmamis ON insights(okundu) WHERE okundu = 0;
