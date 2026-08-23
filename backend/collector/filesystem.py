"""
DiskMind – Filesystem Collector
Walks the filesystem, extracts file metadata, and performs two-phase
duplicate hashing (size → partial_hash → full SHA-256).
"""
from __future__ import annotations

import hashlib
import os
import platform
import sqlite3
import time
from pathlib import Path
from typing import Iterator

# ── Protected paths (never recommend deletion) ────────────────────────────────
PROTECTED_PATHS: set[str] = {
    "/boot", "/etc", "/usr", "/bin", "/sbin", "/lib", "/lib64",
    "/dev", "/proc", "/sys", "/run", "/snap",
    "/.ssh", "/.gnupg", "/.config/systemd",
}

PROTECTED_SUFFIXES: tuple[str, ...] = (
    "/.ssh", "/.gnupg", "/.pki",
)

SYSTEM_PATH_PREFIXES: tuple[str, ...] = (
    "/boot", "/etc", "/usr", "/bin", "/sbin", "/lib", "/lib64",
    "/dev", "/proc", "/sys", "/run", "/var/lib/dpkg",
)

# ── File type classification map ──────────────────────────────────────────────
EXTENSION_TYPE_MAP: dict[str, str] = {
    # Media
    ".mp4": "media", ".mkv": "media", ".avi": "media", ".mov": "media",
    ".mp3": "media", ".flac": "media", ".wav": "media",
    ".jpg": "media", ".jpeg": "media", ".png": "media", ".gif": "media",
    ".webp": "media", ".bmp": "media", ".svg": "media",
    # Documents
    ".pdf": "document", ".doc": "document", ".docx": "document",
    ".xls": "document", ".xlsx": "document", ".ppt": "document",
    ".pptx": "document", ".odt": "document", ".txt": "document",
    ".md": "document",
    # Archives
    ".zip": "archive", ".tar": "archive", ".gz": "archive", ".bz2": "archive",
    ".xz": "archive", ".rar": "archive", ".7z": "archive",
    # Source code
    ".py": "source_code", ".js": "source_code", ".ts": "source_code",
    ".tsx": "source_code", ".jsx": "source_code", ".go": "source_code",
    ".rs": "source_code", ".c": "source_code", ".cpp": "source_code",
    ".h": "source_code", ".java": "source_code", ".rb": "source_code",
    ".php": "source_code", ".swift": "source_code", ".kt": "source_code",
    # Config
    ".json": "config", ".yaml": "config", ".yml": "config", ".toml": "config",
    ".ini": "config", ".cfg": "config", ".conf": "config", ".env": "config",
    # Logs
    ".log": "log",
    # Build artifacts / cache
    ".pyc": "build_artifact", ".o": "build_artifact", ".class": "build_artifact",
    ".so": "build_artifact", ".dll": "build_artifact", ".exe": "build_artifact",
    ".whl": "build_artifact", ".egg": "build_artifact",
    # Temp / cache
    ".tmp": "cache", ".cache": "cache", ".bak": "cache", ".swp": "cache",
}

PATH_TYPE_HINTS: dict[str, str] = {
    "__pycache__": "build_artifact",
    "node_modules": "build_artifact",
    ".cache": "cache",
    "Cache": "cache",
    "cache": "cache",
    "tmp": "cache",
    ".tmp": "cache",
    "Trash": "cache",
    "target": "build_artifact",      # Rust/Maven
    "build": "build_artifact",       # Generic build dirs
    "dist": "build_artifact",
    ".gradle": "build_artifact",
    "logs": "log",
    "log": "log",
}

APPLICATION_HINTS: dict[str, str] = {
    ".docker": "docker",
    "Docker": "docker",
    "node_modules": "npm",
    ".npm": "npm",
    ".cache/pip": "pip",
    ".local/lib/python": "pip",
    "site-packages": "pip",
    ".cache/yarn": "yarn",
    "snap": "snap",
    "flatpak": "flatpak",
    ".venv": "python_venv",
    "venv": "python_venv",
    ".conda": "conda",
    "anaconda": "conda",
    ".gradle": "gradle",
    ".m2": "maven",
    ".cargo": "cargo",
}


def _is_protected(path: str) -> bool:
    p = path.lower()
    for prot in PROTECTED_PATHS:
        if p == prot or p.startswith(prot + "/"):
            return True
    for suf in PROTECTED_SUFFIXES:
        if suf in p:
            return True
    return False


def _is_system_path(path: str) -> bool:
    for prefix in SYSTEM_PATH_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _classify_file_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in EXTENSION_TYPE_MAP:
        return EXTENSION_TYPE_MAP[ext]
    for hint, ftype in PATH_TYPE_HINTS.items():
        if hint in str(path):
            return ftype
    return "other"


def _detect_application(path: str) -> str | None:
    for hint, app in APPLICATION_HINTS.items():
        if hint in path:
            return app
    return None


def _partial_hash(filepath: Path, chunk_size: int = 65536) -> str | None:
    """Hash first 64 KB of file for fast pre-grouping."""
    try:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            chunk = f.read(chunk_size)
            if not chunk:
                return None
            h.update(chunk)
            h.update(str(filepath.stat().st_size).encode())
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def _full_hash(filepath: Path) -> str | None:
    """SHA-256 of full file content."""
    try:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(524288), b""):  # 512 KB chunks
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def _path_hash(path: str) -> str:
    return hashlib.sha256(path.encode()).hexdigest()


def walk_filesystem(
    root: Path,
    max_depth: int = 10,
    min_file_size: int = 0,
) -> Iterator[dict]:
    """
    Yield file metadata dicts for every regular file under root.
    Skips unreadable paths and protected system directories.
    """
    root_str = str(root).replace("\\", "/")

    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        # Depth pruning
        depth = dirpath.replace("\\", "/").replace(root_str, "").count("/")
        if depth >= max_depth:
            dirnames.clear()
            continue

        for filename in filenames:
            try:
                filepath = Path(dirpath) / filename
                if not filepath.is_file() or filepath.is_symlink():
                    continue

                stat = filepath.stat()
                size = stat.st_size
                if size < min_file_size:
                    continue

                path_str = str(filepath).replace("\\", "/")
                is_prot = _is_protected(path_str)
                is_sys = _is_system_path(path_str)

                yield {
                    "path_hash": _path_hash(path_str),
                    "path": path_str,
                    "filename": filename,
                    "extension": filepath.suffix.lower(),
                    "size_bytes": size,
                    "created_at": stat.st_ctime,
                    "modified_at": stat.st_mtime,
                    "accessed_at": stat.st_atime,
                    "is_hidden": int(filename.startswith(".")),
                    "is_system_path": int(is_sys),
                    "is_protected": int(is_prot),
                    "file_type": _classify_file_type(filepath),
                    "application": _detect_application(path_str),
                    "last_scanned_at": time.time(),
                }
            except (OSError, PermissionError):
                continue


def compute_duplicate_hashes(db: sqlite3.Connection) -> int:
    """
    Two-phase hashing:
      1. Group by size → compute partial hashes for size-duplicates
      2. Group by partial_hash → compute full SHA-256 for candidates
    Returns number of duplicate groups found.
    """
    cur = db.cursor()

    # Phase 1: Find files sharing the same size (min 2)
    cur.execute("""
        SELECT size_bytes FROM files
        WHERE is_protected = 0 AND size_bytes > 1024
        GROUP BY size_bytes HAVING COUNT(*) > 1
    """)
    candidate_sizes = [r[0] for r in cur.fetchall()]

    if not candidate_sizes:
        return 0

    # Phase 2: Compute partial hashes for candidates
    placeholders = ",".join("?" * len(candidate_sizes))
    cur.execute(f"SELECT id, path FROM files WHERE size_bytes IN ({placeholders})", candidate_sizes)
    size_candidates = cur.fetchall()

    for file_id, path in size_candidates:
        ph = _partial_hash(Path(path))
        if ph:
            cur.execute("UPDATE files SET partial_hash=? WHERE id=?", (ph, file_id))

    db.commit()

    # Phase 3: Find files sharing partial hash → compute full hash
    cur.execute("""
        SELECT partial_hash FROM files
        WHERE partial_hash IS NOT NULL
        GROUP BY partial_hash HAVING COUNT(*) > 1
    """)
    candidate_partial = [r[0] for r in cur.fetchall()]

    if not candidate_partial:
        return 0

    placeholders = ",".join("?" * len(candidate_partial))
    cur.execute(f"SELECT id, path FROM files WHERE partial_hash IN ({placeholders})", candidate_partial)
    partial_candidates = cur.fetchall()

    for file_id, path in partial_candidates:
        fh = _full_hash(Path(path))
        if fh:
            cur.execute("UPDATE files SET content_hash=? WHERE id=?", (fh, file_id))

    db.commit()

    # Phase 4: Find confirmed duplicate groups (same full hash)
    cur.execute("""
        SELECT content_hash FROM files
        WHERE content_hash IS NOT NULL
        GROUP BY content_hash HAVING COUNT(*) > 1
    """)
    dup_groups = [r[0] for r in cur.fetchall()]

    # Mark duplicate_group and upsert into duplicate_groups table
    for dg in dup_groups:
        cur.execute("""
            SELECT MIN(id), COUNT(*), MIN(size_bytes), MIN(file_type)
            FROM files WHERE content_hash=?
        """, (dg,))
        row = cur.fetchone()
        if row:
            _, count, size, ftype = row
            wasted = (count - 1) * size

            cur.execute("UPDATE files SET duplicate_group=? WHERE content_hash=?", (dg, dg))
            cur.execute("""
                INSERT INTO duplicate_groups(content_hash, file_count, total_wasted_bytes, size_bytes, file_type)
                VALUES(?,?,?,?,?)
                ON CONFLICT(content_hash) DO UPDATE SET
                  file_count=excluded.file_count,
                  total_wasted_bytes=excluded.total_wasted_bytes
            """, (dg, count, wasted, size, ftype or "other"))

    db.commit()
    return len(dup_groups)
