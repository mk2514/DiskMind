"""
DiskMind – AI Tool Implementations
All tools available to the LLM copilot. These query SQLite and return structured data.
The LLM never gets raw file contents, only metadata.
"""
from __future__ import annotations

import json
from typing import Any


async def tool_get_storage_summary(db) -> dict[str, Any]:
    from backend.database.database import fetchone, fetchall
    from backend.ai.recommendations import compute_storage_health_score

    snap = await fetchone(db, """
        SELECT * FROM storage_snapshots ORDER BY recorded_at DESC LIMIT 1
    """)

    dup = await fetchone(db, """
        SELECT SUM(total_wasted_bytes) as wasted FROM duplicate_groups
    """)

    inactive = await fetchone(db, """
        SELECT SUM(size_bytes) as total FROM files WHERE inactivity_score >= 60
    """)

    cache = await fetchone(db, """
        SELECT SUM(size_bytes) as total FROM files WHERE file_type = 'cache'
    """)

    recs = await fetchone(db, """
        SELECT COUNT(*) as cnt, SUM(size_bytes) as total_recoverable
        FROM recommendations WHERE status = 'PENDING'
    """)

    anomaly_count = (await fetchone(db, "SELECT COUNT(*) as cnt FROM anomalies WHERE is_resolved = 0") or {}).get("cnt", 0)

    if not snap:
        return {"error": "No storage data available. Run a scan first."}

    util = snap["utilization_pct"]
    total = snap["total_bytes"]
    dup_bytes = (dup or {}).get("wasted") or 0
    dup_pct = dup_bytes / total * 100 if total > 0 else 0

    forecast = await fetchone(db, """
        SELECT recorded_at FROM storage_snapshots ORDER BY recorded_at DESC LIMIT 1
    """)

    # Quick days-until-90 estimate from snapshots
    snaps_list = await fetchall(db, """
        SELECT used_bytes, recorded_at FROM storage_snapshots ORDER BY recorded_at ASC LIMIT 7
    """)
    days_until_90 = 999
    if len(snaps_list) >= 2:
        first, last = snaps_list[0], snaps_list[-1]
        days_diff = max((last["recorded_at"] - first["recorded_at"]) / 86400, 1)
        daily_growth = (last["used_bytes"] - first["used_bytes"]) / days_diff
        target_90 = total * 0.90
        if daily_growth > 0 and snap["used_bytes"] < target_90:
            days_until_90 = int((target_90 - snap["used_bytes"]) / daily_growth)

    health = compute_storage_health_score(util, dup_pct, anomaly_count, days_until_90)

    return {
        "health_score": health,
        "utilization_pct": util,
        "used_bytes": snap["used_bytes"],
        "free_bytes": snap["free_bytes"],
        "total_bytes": snap["total_bytes"],
        "used_gb": round(snap["used_bytes"] / 1e9, 2),
        "free_gb": round(snap["free_bytes"] / 1e9, 2),
        "total_gb": round(snap["total_bytes"] / 1e9, 2),
        "duplicate_wasted_bytes": int(dup_bytes),
        "duplicate_wasted_gb": round(dup_bytes / 1e9, 2),
        "inactive_bytes": int((inactive or {}).get("total") or 0),
        "cache_bytes": int((cache or {}).get("total") or 0),
        "anomaly_count": anomaly_count,
        "pending_recommendations": (recs or {}).get("cnt", 0),
        "total_recoverable_bytes": int((recs or {}).get("total_recoverable") or 0),
        "total_recoverable_gb": round(((recs or {}).get("total_recoverable") or 0) / 1e9, 2),
        "days_until_90pct": days_until_90,
    }


async def tool_get_largest_files(db, limit: int = 10) -> list[dict]:
    from backend.database.database import fetchall
    return await fetchall(db, """
        SELECT path, filename, size_bytes, file_type, risk_level,
               inactivity_score, accessed_at, modified_at
        FROM files WHERE is_protected = 0
        ORDER BY size_bytes DESC LIMIT ?
    """, (limit,))


async def tool_get_duplicate_groups(db) -> list[dict]:
    from backend.intelligence.duplicates import get_duplicate_groups
    return await get_duplicate_groups(db)


async def tool_get_inactive_files(db, min_score: float = 60.0) -> list[dict]:
    from backend.intelligence.classification import get_inactive_files
    return await get_inactive_files(db, min_score=min_score, limit=20)


async def tool_get_storage_forecast(db) -> dict:
    from backend.ml.forecast import run_forecast
    return await run_forecast(db)


async def tool_get_anomalies(db) -> dict:
    from backend.database.database import fetchall
    anomalies = await fetchall(db, """
        SELECT * FROM anomalies WHERE is_resolved = 0
        ORDER BY anomaly_score DESC LIMIT 10
    """)
    return {"anomalies": anomalies, "count": len(anomalies)}


async def tool_get_recommendations(db) -> list[dict]:
    from backend.database.database import fetchall
    return await fetchall(db, """
        SELECT * FROM recommendations WHERE status = 'PENDING'
        ORDER BY size_bytes DESC LIMIT 20
    """)


async def tool_get_directory_breakdown(db) -> list[dict]:
    from backend.database.database import fetchall
    return await fetchall(db, """
        SELECT file_type, COUNT(*) as file_count, SUM(size_bytes) as total_bytes,
               ROUND(SUM(size_bytes) / 1073741824.0, 3) as total_gb
        FROM files
        GROUP BY file_type ORDER BY total_bytes DESC
    """)


async def tool_simulate_cleanup(db, recommendation_ids: list[int]) -> dict:
    from backend.actions.simulator import simulate_recommendations
    return await simulate_recommendations(db, recommendation_ids)


# ── Tool registry for LLM ──────────────────────────────────────────────────────
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_storage_summary",
            "description": "Get current disk usage stats, health score, duplicate sizes, inactive data, and days until 90% full",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_largest_files",
            "description": "Get the N largest files with risk and inactivity scores",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max number of files to return (default 10)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_duplicate_groups",
            "description": "Get groups of duplicate files and total wasted space",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_inactive_files",
            "description": "Get files that haven't been accessed recently (high inactivity score)",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_score": {"type": "number", "description": "Minimum inactivity score 0-100 (default 60)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_storage_forecast",
            "description": "Get ML-powered storage forecast: predicted utilization at 7, 14, 30, 60, 90 days and days until critical thresholds",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_anomalies",
            "description": "Get detected abnormal storage growth events",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recommendations",
            "description": "Get AI-generated cleanup and archive recommendations with confidence scores and risk levels",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_directory_breakdown",
            "description": "Get storage breakdown by file type and directory",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_cleanup",
            "description": "Simulate the storage impact of executing selected recommendations (what-if analysis)",
            "parameters": {
                "type": "object",
                "properties": {
                    "recommendation_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of recommendation IDs to simulate",
                    },
                },
                "required": ["recommendation_ids"],
            },
        },
    },
]

TOOL_DISPATCH: dict = {
    "get_storage_summary": lambda db, args: tool_get_storage_summary(db),
    "get_largest_files": lambda db, args: tool_get_largest_files(db, **args),
    "get_duplicate_groups": lambda db, args: tool_get_duplicate_groups(db),
    "get_inactive_files": lambda db, args: tool_get_inactive_files(db, **args),
    "get_storage_forecast": lambda db, args: tool_get_storage_forecast(db),
    "get_anomalies": lambda db, args: tool_get_anomalies(db),
    "get_recommendations": lambda db, args: tool_get_recommendations(db),
    "get_directory_breakdown": lambda db, args: tool_get_directory_breakdown(db),
    "simulate_cleanup": lambda db, args: tool_simulate_cleanup(db, args.get("recommendation_ids", [])),
}
