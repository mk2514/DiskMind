"""
DiskMind – File Classification
Provides directory-tree size aggregation and file-type breakdowns.
"""
from __future__ import annotations

from typing import Any


async def get_directory_tree(db, max_depth: int = 3) -> list[dict[str, Any]]:
    """Return top-level directories with size aggregates."""
    from backend.database.database import fetchall

    rows = await fetchall(db, """
        SELECT
            SUBSTR(path, 1, INSTR(SUBSTR(path, 2), '/') + 1) as top_dir,
            SUM(size_bytes) as total_size,
            COUNT(*) as file_count
        FROM files
        WHERE path LIKE '/%'
        GROUP BY top_dir
        ORDER BY total_size DESC
        LIMIT 50
    """)
    return rows


async def get_file_type_breakdown(db) -> list[dict[str, Any]]:
    """Return storage used by each file type."""
    from backend.database.database import fetchall

    return await fetchall(db, """
        SELECT file_type, COUNT(*) as file_count, SUM(size_bytes) as total_size
        FROM files
        GROUP BY file_type
        ORDER BY total_size DESC
    """)


async def get_largest_files(db, limit: int = 20) -> list[dict[str, Any]]:
    """Return the N largest files."""
    from backend.database.database import fetchall

    return await fetchall(db, """
        SELECT path, filename, size_bytes, file_type, risk_level, inactivity_score,
               accessed_at, modified_at, duplicate_group
        FROM files
        WHERE is_protected = 0
        ORDER BY size_bytes DESC
        LIMIT ?
    """, (limit,))


async def get_inactive_files(db, min_score: float = 60.0, limit: int = 50) -> list[dict[str, Any]]:
    """Return files with high inactivity scores."""
    from backend.database.database import fetchall

    return await fetchall(db, """
        SELECT path, filename, size_bytes, file_type, risk_level,
               inactivity_score, accessed_at, modified_at
        FROM files
        WHERE inactivity_score >= ? AND is_protected = 0
        ORDER BY size_bytes DESC
        LIMIT ?
    """, (min_score, limit))
