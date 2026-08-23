-- DiskMind SQLite Schema
-- Privacy-preserving: stores metadata and hashes only, never file contents

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ── Files Table ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    path_hash       TEXT    NOT NULL UNIQUE,          -- SHA-256 of absolute path
    path            TEXT    NOT NULL,                 -- actual path (local only)
    filename        TEXT    NOT NULL,
    extension       TEXT    DEFAULT '',
    size_bytes      INTEGER NOT NULL DEFAULT 0,
    created_at      REAL,                             -- Unix timestamp
    modified_at     REAL,                             -- Unix timestamp
    accessed_at     REAL,                             -- Unix timestamp
    is_hidden       INTEGER NOT NULL DEFAULT 0,
    is_system_path  INTEGER NOT NULL DEFAULT 0,
    is_protected    INTEGER NOT NULL DEFAULT 0,
    file_type       TEXT    DEFAULT 'unknown',        -- cache/log/media/doc/source/build/config/system
    content_hash    TEXT    DEFAULT NULL,             -- SHA-256 of file content (for exact duplicates)
    partial_hash    TEXT    DEFAULT NULL,             -- first 64KB hash (for fast pre-grouping)
    duplicate_group TEXT    DEFAULT NULL,             -- content_hash of the canonical file
    inactivity_score REAL   DEFAULT 0.0,             -- 0 (active) to 100 (inactive)
    risk_level      TEXT    DEFAULT 'UNKNOWN',        -- LOW / MEDIUM / HIGH / PROTECTED
    risk_score      REAL    DEFAULT 0.0,
    application     TEXT    DEFAULT NULL,             -- e.g. 'docker', 'npm', 'pip'
    last_scanned_at REAL    NOT NULL DEFAULT (unixepoch()),
    scan_version    INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_files_content_hash   ON files(content_hash);
CREATE INDEX IF NOT EXISTS idx_files_duplicate_group ON files(duplicate_group);
CREATE INDEX IF NOT EXISTS idx_files_file_type      ON files(file_type);
CREATE INDEX IF NOT EXISTS idx_files_risk_level     ON files(risk_level);
CREATE INDEX IF NOT EXISTS idx_files_size_bytes     ON files(size_bytes DESC);

-- ── Storage Snapshots (for forecasting) ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS storage_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at         REAL    NOT NULL DEFAULT (unixepoch()),
    mount_point         TEXT    NOT NULL DEFAULT '/',
    total_bytes         INTEGER NOT NULL,
    used_bytes          INTEGER NOT NULL,
    free_bytes          INTEGER NOT NULL,
    file_count          INTEGER NOT NULL DEFAULT 0,
    dir_count           INTEGER NOT NULL DEFAULT 0,
    new_files_today     INTEGER DEFAULT 0,
    deleted_files_today INTEGER DEFAULT 0,
    daily_growth_bytes  INTEGER DEFAULT 0,
    utilization_pct     REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshots_recorded_at ON storage_snapshots(recorded_at DESC);

-- ── Duplicate Groups ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS duplicate_groups (
    content_hash        TEXT    PRIMARY KEY,
    file_count          INTEGER NOT NULL DEFAULT 2,
    total_wasted_bytes  INTEGER NOT NULL DEFAULT 0,  -- (count-1) × size
    size_bytes          INTEGER NOT NULL DEFAULT 0,
    file_type           TEXT    DEFAULT 'unknown',
    detection_type      TEXT    DEFAULT 'exact',     -- exact / perceptual / semantic
    confidence          REAL    NOT NULL DEFAULT 1.0,
    created_at          REAL    NOT NULL DEFAULT (unixepoch())
);

-- ── AI Recommendations ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recommendations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      REAL    NOT NULL DEFAULT (unixepoch()),
    action          TEXT    NOT NULL,                -- CLEANUP / ARCHIVE / KEEP / REVIEW
    target_path     TEXT    NOT NULL,
    target_type     TEXT    NOT NULL,                -- file / directory / duplicate_group / file_type
    size_bytes      INTEGER NOT NULL DEFAULT 0,
    confidence      REAL    NOT NULL DEFAULT 0.0,    -- 0.0 – 1.0
    risk_level      TEXT    NOT NULL DEFAULT 'MEDIUM',
    risk_score      REAL    NOT NULL DEFAULT 50.0,
    reason          TEXT    NOT NULL DEFAULT '',
    explanation     TEXT    NOT NULL DEFAULT '',
    status          TEXT    NOT NULL DEFAULT 'PENDING', -- PENDING / APPROVED / REJECTED / EXECUTED / UNDONE
    approved_at     REAL    DEFAULT NULL,
    executed_at     REAL    DEFAULT NULL,
    duplicate_group TEXT    DEFAULT NULL,
    category        TEXT    DEFAULT NULL             -- duplicates / cache / inactive / build_artifact / log
);

CREATE INDEX IF NOT EXISTS idx_recs_status     ON recommendations(status);
CREATE INDEX IF NOT EXISTS idx_recs_risk_level ON recommendations(risk_level);
CREATE INDEX IF NOT EXISTS idx_recs_created_at ON recommendations(created_at DESC);

-- ── Actions Audit Log ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS actions_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    executed_at     REAL    NOT NULL DEFAULT (unixepoch()),
    action          TEXT    NOT NULL,                -- trash / archive / delete / restore
    source_path     TEXT    NOT NULL,
    dest_path       TEXT    DEFAULT NULL,
    size_bytes      INTEGER NOT NULL DEFAULT 0,
    recommendation_id INTEGER REFERENCES recommendations(id),
    status          TEXT    NOT NULL DEFAULT 'SUCCESS', -- SUCCESS / FAILED / UNDONE
    error_msg       TEXT    DEFAULT NULL,
    undone_at       REAL    DEFAULT NULL
);

-- ── Anomalies ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS anomalies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    detected_at     REAL    NOT NULL DEFAULT (unixepoch()),
    snapshot_id     INTEGER REFERENCES storage_snapshots(id),
    anomaly_score   REAL    NOT NULL,
    growth_gb       REAL    NOT NULL DEFAULT 0.0,
    description     TEXT    NOT NULL DEFAULT '',
    top_directories TEXT    NOT NULL DEFAULT '[]',  -- JSON array of {path, size_bytes}
    is_resolved     INTEGER NOT NULL DEFAULT 0
);

-- ── Chat History ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT    NOT NULL,
    role        TEXT    NOT NULL,   -- user / assistant / tool
    content     TEXT    NOT NULL,
    created_at  REAL    NOT NULL DEFAULT (unixepoch())
);

-- ── App State ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS app_state (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL,
    updated_at REAL NOT NULL DEFAULT (unixepoch())
);
