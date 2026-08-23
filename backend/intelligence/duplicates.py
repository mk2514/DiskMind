"""
DiskMind – Duplicate Detection
Groups files by exact hash and computes per-group statistics.
"""
from __future__ import annotations

from typing import Any


async def get_duplicate_groups(db) -> list[dict[str, Any]]:
    """Return all duplicate groups with file lists."""
    from backend.database.database import fetchall

    groups = await fetchall(db, """
        SELECT dg.content_hash, dg.file_count, dg.total_wasted_bytes,
               dg.size_bytes, dg.file_type, dg.confidence, dg.detection_type
        FROM duplicate_groups dg
        ORDER BY dg.total_wasted_bytes DESC
    """)

    result = []
    for g in groups:
        files = await fetchall(db, """
            SELECT path, size_bytes, accessed_at, modified_at, risk_level, application
            FROM files WHERE duplicate_group = ?
        """, (g["content_hash"],))
        result.append({
            **g,
            "files": files,
        })
    return result


async def get_duplicate_summary(db) -> dict[str, Any]:
    """Aggregate stats for all duplicate groups."""
    from backend.database.database import fetchone

    row = await fetchone(db, """
        SELECT
            COUNT(*) as group_count,
            SUM(file_count) as total_dup_files,
            SUM(total_wasted_bytes) as total_wasted_bytes
        FROM duplicate_groups
    """)
    return row or {"group_count": 0, "total_dup_files": 0, "total_wasted_bytes": 0}
