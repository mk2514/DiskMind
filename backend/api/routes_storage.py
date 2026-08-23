"""
DiskMind – Storage API Routes
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi import APIRouter, Depends, BackgroundTasks

from backend.database.database import get_db, fetchall, fetchone

router = APIRouter(prefix="/api/storage", tags=["storage"])


@router.get("/overview")
async def get_overview(db=Depends(get_db)):
    from backend.ai.tools import tool_get_storage_summary
    from backend.ai.recommendations import compute_storage_health_score
    from backend.ml.forecast import run_forecast

    summary = await tool_get_storage_summary(db)
    forecast = await run_forecast(db)

    thresholds = forecast.get("thresholds", {})
    days_until_90 = thresholds.get("days_until_90pct", 999)
    dup_pct = (summary.get("duplicate_wasted_bytes", 0) / max(summary.get("total_bytes", 1), 1)) * 100
    anomaly_count = summary.get("anomaly_count", 0)

    health = compute_storage_health_score(
        summary.get("utilization_pct", 0),
        dup_pct,
        anomaly_count,
        days_until_90,
    )
    summary["health_score"] = health

    return {
        "summary": summary,
        "forecast": forecast,
    }


@router.get("/snapshots")
async def get_snapshots(limit: int = 30, db=Depends(get_db)):
    return await fetchall(db, """
        SELECT * FROM storage_snapshots ORDER BY recorded_at DESC LIMIT ?
    """, (limit,))


@router.get("/tree")
async def get_directory_tree(db=Depends(get_db)):
    from backend.intelligence.classification import get_file_type_breakdown, get_directory_tree
    file_types = await get_file_type_breakdown(db)

    # Build tree from files table
    dirs = await fetchall(db, """
        SELECT 
            CASE 
                WHEN INSTR(SUBSTR(path, 2), '/') > 0
                THEN SUBSTR(path, 1, INSTR(SUBSTR(path, 2), '/') + 1)
                ELSE path
            END as top_dir,
            SUM(size_bytes) as total_size,
            COUNT(*) as file_count
        FROM files
        GROUP BY top_dir
        ORDER BY total_size DESC
        LIMIT 20
    """)
    return {"directories": dirs, "file_types": file_types}


@router.post("/scan")
async def trigger_scan(background_tasks: BackgroundTasks, db=Depends(get_db)):
    """Trigger a background filesystem scan."""
    scan_path = os.getenv("SCAN_PATH", "/home")
    demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"

    if demo_mode:
        return {"message": "Demo mode active. Use demo data generator.", "demo_mode": True}

    background_tasks.add_task(_run_scan, scan_path)
    return {"message": f"Scan started for {scan_path}", "demo_mode": False}


async def _run_scan(scan_path: str):
    """Background scan task."""
    from backend.collector.filesystem import walk_filesystem, compute_duplicate_hashes
    from backend.collector.system import record_snapshot
    from backend.intelligence.inactivity import score_all_files
    from backend.intelligence.risk import score_all_risks
    from backend.database.database import init_db
    import aiosqlite

    async with aiosqlite.connect("diskmind.db") as db:
        db.row_factory = aiosqlite.Row
        for file_meta in walk_filesystem(Path(scan_path)):
            await db.execute("""
                INSERT INTO files(path_hash, path, filename, extension, size_bytes,
                    created_at, modified_at, accessed_at, is_hidden, is_system_path,
                    is_protected, file_type, application, last_scanned_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(path_hash) DO UPDATE SET
                    size_bytes=excluded.size_bytes,
                    modified_at=excluded.modified_at,
                    accessed_at=excluded.accessed_at,
                    last_scanned_at=excluded.last_scanned_at
            """, (
                file_meta["path_hash"], file_meta["path"], file_meta["filename"],
                file_meta["extension"], file_meta["size_bytes"],
                file_meta["created_at"], file_meta["modified_at"], file_meta["accessed_at"],
                file_meta["is_hidden"], file_meta["is_system_path"], file_meta["is_protected"],
                file_meta["file_type"], file_meta["application"], file_meta["last_scanned_at"],
            ))

        await db.commit()
        await score_all_files(db)
        await score_all_risks(db)

        import sqlite3
        sync_db = sqlite3.connect("diskmind.db")
        compute_duplicate_hashes(sync_db)
        sync_db.close()

        record_snapshot_sync(scan_path)


def record_snapshot_sync(path: str):
    from backend.collector.system import get_disk_info
    import sqlite3
    info = get_disk_info(path)
    db = sqlite3.connect("diskmind.db")
    db.execute("""
        INSERT INTO storage_snapshots(recorded_at, mount_point, total_bytes, used_bytes,
            free_bytes, utilization_pct)
        VALUES(?,?,?,?,?,?)
    """, (time.time(), info["mount_point"], info["total_bytes"], info["used_bytes"],
          info["free_bytes"], info["utilization_pct"]))
    db.commit()
    db.close()
