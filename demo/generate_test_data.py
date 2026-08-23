"""
DiskMind – Demo Data Generator
Creates a complete synthetic dataset for demo/judging purposes.
Simulates: duplicates, inactive files, caches, 30 days of snapshots, anomaly event.

Run from project root:
    python demo/generate_test_data.py
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import sqlite3
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.database import init_db_sync, DB_PATH

random.seed(42)

# ── Simulation Parameters ─────────────────────────────────────────────────────
TOTAL_DISK_GB = 512
USED_DISK_GB = 438.6
FREE_DISK_GB = TOTAL_DISK_GB - USED_DISK_GB
UTIL_PCT = USED_DISK_GB / TOTAL_DISK_GB * 100

TOTAL_BYTES = int(TOTAL_DISK_GB * 1e9)
USED_BYTES = int(USED_DISK_GB * 1e9)
FREE_BYTES = TOTAL_BYTES - USED_BYTES

# Demo file tree structure (path, size_gb, file_type, accessed_days_ago, is_dup_group)
DEMO_FILES = [
    # ── Videos ──────────────────────────────────────────────────────────────────
    ("/home/user/Videos/vacation_2023.mp4",     8.2, "media",   400, "dup_movies_a"),
    ("/home/user/Downloads/vacation_2023.mp4",  8.2, "media",   380, "dup_movies_a"),  # duplicate
    ("/home/user/Videos/concert_4k.mkv",        12.4, "media",  300, None),
    ("/home/user/Videos/family_dinner.mp4",     4.1, "media",   250, "dup_movies_b"),
    ("/home/user/Downloads/family_dinner.mp4",  4.1, "media",   260, "dup_movies_b"),  # duplicate
    ("/home/user/Videos/tutorial_series.mkv",   6.7, "media",   180, None),
    ("/home/user/Videos/webinar_recording.mp4", 3.2, "media",   90,  None),
    ("/home/user/Videos/old_movie_2019.avi",    5.8, "media",   700, None),

    # ── Downloads ────────────────────────────────────────────────────────────────
    ("/home/user/Downloads/ubuntu-22.04.iso",   3.8, "archive", 500, "dup_iso"),
    ("/home/user/backup/ubuntu-22.04.iso",      3.8, "archive", 480, "dup_iso"),      # duplicate
    ("/home/user/Downloads/project_backup.zip", 2.1, "archive", 365, None),
    ("/home/user/Downloads/old_dataset.tar.gz", 4.4, "archive", 420, None),
    ("/home/user/Downloads/fonts_pack.zip",     0.8, "archive", 600, "dup_zip"),
    ("/home/user/Documents/fonts_pack.zip",     0.8, "archive", 590, "dup_zip"),      # duplicate

    # ── Projects ─────────────────────────────────────────────────────────────────
    ("/home/user/Projects/ml_project/data/train.csv",    1.8, "document",   10, None),
    ("/home/user/Projects/ml_project/data/test.csv",     0.4, "document",   10, None),
    ("/home/user/Projects/ml_project/models/model.pkl",  0.3, "build_artifact", 5, None),
    ("/home/user/Projects/old_webapp/node_modules/lib.js", 2.2, "build_artifact", 400, None),
    ("/home/user/Projects/old_webapp/dist/bundle.js",    0.9, "build_artifact", 400, None),
    ("/home/user/Projects/rust_app/target/debug/app",    1.4, "build_artifact", 200, None),

    # ── Docker ───────────────────────────────────────────────────────────────────
    ("/home/user/.docker/overlay2/abc123/merged",  18.3, "build_artifact", 5, None),
    ("/home/user/.docker/volumes/db_data/_data",    3.2, "build_artifact", 2, None),

    # ── Caches ───────────────────────────────────────────────────────────────────
    ("/home/user/.cache/pip/wheels/package1.whl",  1.2, "cache", 60, None),
    ("/home/user/.cache/pip/wheels/package2.whl",  0.9, "cache", 90, None),
    ("/home/user/.cache/yarn/packages.tgz",        2.1, "cache", 45, None),
    ("/home/user/.cache/mozilla/cache2/entries",   1.8, "cache", 2,  None),
    ("/home/user/.cache/google-chrome/Cache",      3.4, "cache", 1,  None),

    # ── Logs ─────────────────────────────────────────────────────────────────────
    ("/var/log/docker/container_abc.log",   4.2, "log", 30, None),
    ("/var/log/nginx/access.log",           0.8, "log", 1,  None),
    ("/var/log/kern.log",                   0.3, "log", 3,  None),
    ("/home/user/Projects/ml_project/train.log", 1.1, "log", 2, None),

    # ── Documents ────────────────────────────────────────────────────────────────
    ("/home/user/Documents/resume_v1.pdf",        0.002, "document", 180, "dup_resume"),
    ("/home/user/Documents/resume_final.pdf",     0.002, "document", 90,  "dup_resume"),  # duplicate
    ("/home/user/Documents/resume_final_v2.pdf",  0.002, "document", 30,  None),
    ("/home/user/Documents/report_q1.pdf",        0.05,  "document", 200, None),
    ("/home/user/Documents/report_q2.pdf",        0.04,  "document", 100, None),

    # ── Config / Source ──────────────────────────────────────────────────────────
    ("/home/user/.bashrc",           0.001, "config",      1, None),
    ("/home/user/.ssh/config",       0.001, "config",      5, None),   # protected
    ("/home/user/Projects/ml_project/train.py", 0.02, "source_code", 3, None),
]

# Duplicate groups: content_hash → size_gb
DUPLICATE_GROUPS_META = {
    "dup_movies_a": (8.2,  "media"),
    "dup_movies_b": (4.1,  "media"),
    "dup_iso":      (3.8,  "archive"),
    "dup_zip":      (0.8,  "archive"),
    "dup_resume":   (0.002, "document"),
}

APPLICATION_HINTS = {
    ".docker": "docker",
    "node_modules": "npm",
    ".cache/pip": "pip",
    ".cache/yarn": "yarn",
    ".cache/mozilla": "firefox",
    ".cache/google-chrome": "chrome",
    "/var/log/docker": "docker",
    "/var/log/nginx": "nginx",
    "rust_app/target": "cargo",
}


def _det_app(path: str) -> str | None:
    for hint, app in APPLICATION_HINTS.items():
        if hint in path:
            return app
    return None


def _is_protected(path: str) -> bool:
    return "/.ssh/" in path or "/.gnupg/" in path


def _path_hash(path: str) -> str:
    return hashlib.sha256(path.encode()).hexdigest()


def _content_hash(group: str | None, size_bytes: int) -> str | None:
    if group is None:
        return None
    return hashlib.sha256(f"{group}:{size_bytes}".encode()).hexdigest()


def generate_snapshots(n_days: int = 31) -> list[dict]:
    """
    Generate n_days of storage snapshots with:
    - Normal growth: ~1.3 GB/day
    - Anomaly spike on day 20: +17 GB (Docker logs)
    """
    snapshots = []
    base_used = USED_BYTES - int(1.3e9 * n_days)
    now = time.time()

    for d in range(n_days):
        ts = now - (n_days - d) * 86400

        # Normal daily growth ~1.3 GB with noise
        normal_growth = int(1.3e9 + random.gauss(0, 2e8))

        # Anomaly on day 20
        if d == 20:
            anomaly_growth = int(17e9)  # +17 GB spike
        else:
            anomaly_growth = 0

        used = base_used + int(1.3e9 * d) + anomaly_growth
        used = max(0, min(used, TOTAL_BYTES))
        free = TOTAL_BYTES - used
        util = round(used / TOTAL_BYTES * 100, 2)
        daily = normal_growth + anomaly_growth if d > 0 else 0

        snapshots.append({
            "recorded_at": ts,
            "mount_point": "/",
            "total_bytes": TOTAL_BYTES,
            "used_bytes": used,
            "free_bytes": free,
            "file_count": 45000 + d * 50 + random.randint(-10, 10),
            "dir_count": 8000 + d * 2,
            "new_files_today": random.randint(10, 80),
            "deleted_files_today": random.randint(0, 20),
            "daily_growth_bytes": daily,
            "utilization_pct": util,
        })

    return snapshots


def generate_recommendations() -> list[dict]:
    """Generate realistic AI recommendations."""
    return [
        {
            "action": "CLEANUP",
            "target_path": json.dumps([
                "/home/user/Downloads/vacation_2023.mp4",
                "/home/user/Downloads/family_dinner.mp4",
            ]),
            "target_type": "duplicate_group",
            "size_bytes": int(12.3e9),
            "confidence": 0.998,
            "risk_level": "LOW",
            "risk_score": 3.0,
            "reason": "17.8 GB of duplicate video files detected",
            "explanation": "SHA-256 hash confirmed: exact identical copies. Keeping most recently accessed originals in ~/Videos. Moving 2 duplicates in ~/Downloads to Trash recovers 12.3 GB.",
            "duplicate_group": _content_hash("dup_movies_a", int(8.2e9)),
            "category": "duplicates",
            "status": "PENDING",
        },
        {
            "action": "CLEANUP",
            "target_path": "[pip cache files]",
            "target_type": "file_type",
            "size_bytes": int(2.1e9),
            "confidence": 0.97,
            "risk_level": "LOW",
            "risk_score": 5.0,
            "reason": "pip cache consuming 2.1 GB — auto-regenerated by pip",
            "explanation": "Application cache files for pip/yarn. These are automatically regenerated by pip/yarn on next install. Safe to remove.",
            "duplicate_group": None,
            "category": "cache",
            "status": "PENDING",
        },
        {
            "action": "CLEANUP",
            "target_path": "[docker log files]",
            "target_type": "file_type",
            "size_bytes": int(4.2e9),
            "confidence": 0.91,
            "risk_level": "LOW",
            "risk_score": 8.0,
            "reason": "Docker container logs consuming 4.2 GB",
            "explanation": "Docker container log files detected. These were the source of the anomalous +17 GB growth spike detected on day 20. Safe to truncate.",
            "duplicate_group": None,
            "category": "log",
            "status": "PENDING",
        },
        {
            "action": "CLEANUP",
            "target_path": "[npm/cargo build artifacts]",
            "target_type": "file_type",
            "size_bytes": int(4.5e9),
            "confidence": 0.88,
            "risk_level": "LOW",
            "risk_score": 10.0,
            "reason": "Build artifacts (node_modules, Rust target) consuming 4.5 GB",
            "explanation": "Compiled build output and node_modules from old_webapp project (last modified 400 days ago). Can be regenerated with npm install / cargo build.",
            "duplicate_group": None,
            "category": "build_artifact",
            "status": "PENDING",
        },
        {
            "action": "ARCHIVE",
            "target_path": "/home/user/Downloads/old_dataset.tar.gz",
            "target_type": "file",
            "size_bytes": int(4.4e9),
            "confidence": 0.84,
            "risk_level": "MEDIUM",
            "risk_score": 22.0,
            "reason": "Large archive not accessed for 420 days (inactivity: 88/100)",
            "explanation": "4.4 GB compressed dataset not accessed in over a year. Consider archiving to external storage. Not safe to delete without review.",
            "duplicate_group": None,
            "category": "inactive",
            "status": "PENDING",
        },
        {
            "action": "CLEANUP",
            "target_path": json.dumps(["/home/user/backup/ubuntu-22.04.iso"]),
            "target_type": "duplicate_group",
            "size_bytes": int(3.8e9),
            "confidence": 0.999,
            "risk_level": "LOW",
            "risk_score": 2.0,
            "reason": "Duplicate Ubuntu ISO in ~/backup",
            "explanation": "SHA-256 confirmed: identical copy of ubuntu-22.04.iso exists in ~/Downloads. The ~/backup copy is redundant. Moving to Trash recovers 3.8 GB.",
            "duplicate_group": _content_hash("dup_iso", int(3.8e9)),
            "category": "duplicates",
            "status": "PENDING",
        },
        {
            "action": "KEEP",
            "target_path": "/home/user/.ssh/config",
            "target_type": "file",
            "size_bytes": 1024,
            "confidence": 1.0,
            "risk_level": "PROTECTED",
            "risk_score": 100.0,
            "reason": "SSH configuration — PROTECTED",
            "explanation": "SSH configuration file. This path is permanently protected. DiskMind will never recommend deletion of SSH, GPG, or system configuration files.",
            "duplicate_group": None,
            "category": "config",
            "status": "PENDING",
        },
    ]


def main():
    print("🧠 DiskMind — Generating Demo Dataset")
    print(f"   Database: {DB_PATH}")

    # Initialize schema
    init_db_sync()
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # Clear existing demo data
    for table in ["files", "storage_snapshots", "duplicate_groups", "recommendations", "anomalies", "chat_history", "actions_log"]:
        db.execute(f"DELETE FROM {table}")
    db.commit()
    print("   ✓ Database cleared")

    # ── Insert files ──────────────────────────────────────────────────────────
    now = time.time()
    for path, size_gb, ftype, accessed_days_ago, dup_group in DEMO_FILES:
        size_bytes = int(size_gb * 1e9)
        accessed_at = now - accessed_days_ago * 86400
        modified_at = accessed_at - random.randint(0, 30) * 86400
        created_at = modified_at - random.randint(30, 365) * 86400

        is_prot = _is_protected(path)
        content_hash = _content_hash(dup_group, size_bytes) if dup_group else None

        # Inactivity score
        access_age_norm = min(accessed_days_ago / 365, 1.0)
        mod_age_norm = min((now - modified_at) / (365 * 86400), 1.0)
        type_bias = {"cache": 0.9, "log": 0.75, "build_artifact": 0.8, "archive": 0.6, "media": 0.5, "document": 0.3, "source_code": 0.2, "config": 0.1}.get(ftype, 0.4)
        inactivity = min((0.3 * access_age_norm + 0.2 * mod_age_norm + 0.15 * (1 if dup_group else 0) + 0.1 * type_bias) * 100, 100)

        # Risk level
        if is_prot:
            risk_level, risk_score = "PROTECTED", 100.0
        elif ftype in ("cache", "log") and not is_prot:
            risk_level, risk_score = "LOW", 5.0
        elif ftype == "build_artifact":
            risk_level, risk_score = "LOW", 10.0
        elif dup_group:
            risk_level, risk_score = "LOW", 3.0
        elif accessed_days_ago < 7:
            risk_level, risk_score = "HIGH", 30.0
        else:
            risk_level, risk_score = "MEDIUM", 20.0

        db.execute("""
            INSERT INTO files(path_hash, path, filename, extension, size_bytes,
                created_at, modified_at, accessed_at, is_hidden, is_system_path,
                is_protected, file_type, content_hash, duplicate_group,
                inactivity_score, risk_level, risk_score, application, last_scanned_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            _path_hash(path), path, Path(path).name, Path(path).suffix.lower(),
            size_bytes, created_at, modified_at, accessed_at,
            int(Path(path).name.startswith(".")),
            int(path.startswith("/var") or path.startswith("/etc")),
            int(is_prot), ftype, content_hash, content_hash,
            round(inactivity, 2), risk_level, risk_score,
            _det_app(path), now,
        ))

    db.commit()
    print(f"   ✓ {len(DEMO_FILES)} files inserted")

    # ── Insert duplicate groups ───────────────────────────────────────────────
    for group_key, (size_gb, ftype) in DUPLICATE_GROUPS_META.items():
        size_bytes = int(size_gb * 1e9)
        content_hash = _content_hash(group_key, size_bytes)
        file_count = 2
        wasted = (file_count - 1) * size_bytes

        db.execute("""
            INSERT OR REPLACE INTO duplicate_groups(content_hash, file_count, total_wasted_bytes, size_bytes, file_type, confidence)
            VALUES(?,?,?,?,?,?)
        """, (content_hash, file_count, wasted, size_bytes, ftype, 1.0))

    db.commit()
    print(f"   ✓ {len(DUPLICATE_GROUPS_META)} duplicate groups inserted")

    # ── Insert storage snapshots (30 days) ───────────────────────────────────
    snapshots = generate_snapshots(31)
    for s in snapshots:
        db.execute("""
            INSERT INTO storage_snapshots(recorded_at, mount_point, total_bytes, used_bytes,
                free_bytes, file_count, dir_count, new_files_today, deleted_files_today,
                daily_growth_bytes, utilization_pct)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (
            s["recorded_at"], s["mount_point"], s["total_bytes"], s["used_bytes"],
            s["free_bytes"], s["file_count"], s["dir_count"], s["new_files_today"],
            s["deleted_files_today"], s["daily_growth_bytes"], s["utilization_pct"],
        ))
    db.commit()
    print(f"   ✓ {len(snapshots)} storage snapshots inserted (30 days + anomaly)")

    # ── Insert anomaly ────────────────────────────────────────────────────────
    anomaly_snapshot_ts = snapshots[20]["recorded_at"]
    db.execute("""
        INSERT INTO anomalies(detected_at, anomaly_score, growth_gb, description, top_directories)
        VALUES(?,?,?,?,?)
    """, (
        time.time(), 0.87, 17.0,
        "Abnormal storage growth detected: +17.0 GB in a single day",
        json.dumps([
            {"path": "/var/log/docker", "size_bytes": int(8.1e9)},
            {"path": "/home/user/.cache/google-chrome", "size_bytes": int(4.2e9)},
            {"path": "/home/user/Downloads", "size_bytes": int(3.7e9)},
            {"path": "/home/user/Videos", "size_bytes": int(1.0e9)},
        ]),
    ))
    db.commit()
    print("   ✓ Anomaly event inserted (day 20: +17 GB Docker logs)")

    # ── Insert recommendations ────────────────────────────────────────────────
    recs = generate_recommendations()
    for r in recs:
        db.execute("""
            INSERT INTO recommendations(
                action, target_path, target_type, size_bytes, confidence,
                risk_level, risk_score, reason, explanation, duplicate_group, category, status
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            r["action"], r["target_path"], r["target_type"], r["size_bytes"],
            r["confidence"], r["risk_level"], r["risk_score"],
            r["reason"], r["explanation"], r["duplicate_group"], r["category"], r["status"],
        ))
    db.commit()
    print(f"   ✓ {len(recs)} AI recommendations inserted")

    db.close()

    total_rec = sum(r["size_bytes"] for r in recs if r["risk_level"] != "PROTECTED")
    print(f"\n🎉 Demo dataset ready!")
    print(f"   Disk: {USED_DISK_GB:.1f} GB / {TOTAL_DISK_GB} GB ({UTIL_PCT:.1f}%)")
    print(f"   Files: {len(DEMO_FILES)}")
    print(f"   Duplicate groups: {len(DUPLICATE_GROUPS_META)}")
    print(f"   Recoverable: {total_rec/1e9:.1f} GB")
    print(f"   Anomalies: 1 (+17 GB Docker spike on day 20)")
    print(f"\n   Start backend:  uvicorn backend.main:app --reload")
    print(f"   Start frontend: cd frontend && npm run dev")


if __name__ == "__main__":
    main()
