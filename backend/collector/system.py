"""
DiskMind – System Collector
Uses psutil to collect disk usage and record storage snapshots.
"""
from __future__ import annotations

import time
from typing import Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def get_disk_info(path: str = "/") -> dict[str, Any]:
    """Return disk usage info for the given path."""
    if not PSUTIL_AVAILABLE:
        # Fallback for non-Linux demo environments
        import shutil
        total, used, free = shutil.disk_usage(path)
        return {
            "mount_point": path,
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "utilization_pct": round(used / total * 100, 2) if total > 0 else 0,
        }

    usage = psutil.disk_usage(path)
    return {
        "mount_point": path,
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "utilization_pct": round(usage.percent, 2),
    }


def get_all_disk_info() -> list[dict[str, Any]]:
    """Return usage info for all mounted partitions."""
    if not PSUTIL_AVAILABLE:
        return [get_disk_info("/")]

    results = []
    for part in psutil.disk_partitions(all=False):
        try:
            info = get_disk_info(part.mountpoint)
            info["device"] = part.device
            info["fstype"] = part.fstype
            results.append(info)
        except (OSError, PermissionError):
            continue
    return results


def record_snapshot(db, file_count: int = 0, dir_count: int = 0,
                    new_files: int = 0, deleted_files: int = 0,
                    daily_growth_bytes: int = 0, path: str = "/") -> int:
    """Insert a storage snapshot into the DB. Returns snapshot id."""
    info = get_disk_info(path)
    cur = db.cursor()
    cur.execute("""
        INSERT INTO storage_snapshots(
            recorded_at, mount_point, total_bytes, used_bytes, free_bytes,
            file_count, dir_count, new_files_today, deleted_files_today,
            daily_growth_bytes, utilization_pct
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        time.time(),
        info["mount_point"],
        info["total_bytes"],
        info["used_bytes"],
        info["free_bytes"],
        file_count, dir_count, new_files, deleted_files,
        daily_growth_bytes,
        info["utilization_pct"],
    ))
    db.commit()
    return cur.lastrowid
