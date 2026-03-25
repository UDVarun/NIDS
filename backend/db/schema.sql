-- NIDS Sentinel Database Schema — SQLite 3

CREATE TABLE IF NOT EXISTS alerts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     REAL    NOT NULL,
    datetime_str  TEXT    NOT NULL,
    src_ip        TEXT    DEFAULT '0.0.0.0',
    dst_ip        TEXT    DEFAULT '0.0.0.0',
    protocol      TEXT    DEFAULT 'OTHER',
    prediction    TEXT    NOT NULL,
    attack_type   TEXT,
    confidence    REAL    DEFAULT 0.0,
    anomaly_score REAL    DEFAULT 0.0,
    is_attack     INTEGER DEFAULT 0,
    raw_features  TEXT
);

CREATE INDEX IF NOT EXISTS idx_timestamp   ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_is_attack   ON alerts(is_attack);
CREATE INDEX IF NOT EXISTS idx_attack_type ON alerts(attack_type);
CREATE INDEX IF NOT EXISTS idx_src_ip      ON alerts(src_ip);
