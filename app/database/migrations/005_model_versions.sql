-- Migration 005: Model Versiyonlama
-- Tarih: 2026-01-07
-- Amaç: ML model versiyonlarını sakla ve karşılaştır

CREATE TABLE IF NOT EXISTS model_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arac_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    model_type TEXT NOT NULL,  -- 'ensemble', 'kalman', 'physics'
    params_json TEXT,
    r2_score REAL,
    mae REAL,
    sample_count INTEGER,
    is_active INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (arac_id) REFERENCES araclar(id),
    UNIQUE(arac_id, version, model_type)
);

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_model_arac ON model_versions(arac_id);
CREATE INDEX IF NOT EXISTS idx_model_active ON model_versions(is_active) WHERE is_active = 1;
