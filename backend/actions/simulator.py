"""
DiskMind – What-If Simulator
Estimates the storage impact of executing a set of recommendations.
"""
from __future__ import annotations

from typing import Any


async def simulate_recommendations(db, recommendation_ids: list[int]) -> dict[str, Any]:
    """
    Given a list of recommendation IDs, calculate:
    - Total bytes that would be recovered
    - New utilization percentage
    - New days until 90%/95%/100%
    Returns before/after comparison dict.
    """
    from backend.database.database import fetchall, fetchone
    from backend.ml.forecast import run_forecast

    if not recommendation_ids:
        return {"error": "No recommendations selected"}

    # Get selected recommendations
    placeholders = ",".join("?" * len(recommendation_ids))
    recs = await fetchall(db, f"""
        SELECT id, action, target_path, size_bytes, confidence, risk_level, reason, category
        FROM recommendations WHERE id IN ({placeholders}) AND status = 'PENDING'
    """, tuple(recommendation_ids))

    if not recs:
        return {"error": "No valid pending recommendations found"}

    total_recoverable = sum(r["size_bytes"] for r in recs)

    # Current state
    snap = await fetchone(db, """
        SELECT total_bytes, used_bytes, free_bytes, utilization_pct
        FROM storage_snapshots ORDER BY recorded_at DESC LIMIT 1
    """)

    if not snap:
        return {"error": "No storage snapshot available"}

    total = snap["total_bytes"]
    current_used = snap["used_bytes"]
    current_util = snap["utilization_pct"]

    # After cleanup
    new_used = max(0, current_used - total_recoverable)
    new_free = total - new_used
    new_util = round(new_used / total * 100, 2) if total > 0 else 0

    # Forecast impact
    forecast = await run_forecast(db)
    avg_daily = forecast.get("avg_daily_growth_bytes", 0)

    def days_until_pct(used: int, target_pct: float) -> int:
        target = total * target_pct / 100
        if used >= target:
            return 0
        if avg_daily <= 0:
            return 999
        return int((target - used) / avg_daily)

    before_90 = days_until_pct(current_used, 90)
    after_90 = days_until_pct(new_used, 90)
    before_95 = days_until_pct(current_used, 95)
    after_95 = days_until_pct(new_used, 95)
    before_100 = days_until_pct(current_used, 100)
    after_100 = days_until_pct(new_used, 100)

    days_gained = after_90 - before_90

    return {
        "selected_recommendations": len(recs),
        "total_recoverable_bytes": int(total_recoverable),
        "total_recoverable_gb": round(total_recoverable / 1e9, 2),
        "before": {
            "used_bytes": int(current_used),
            "free_bytes": int(snap["free_bytes"]),
            "utilization_pct": current_util,
            "used_gb": round(current_used / 1e9, 2),
            "free_gb": round(snap["free_bytes"] / 1e9, 2),
            "days_until_90pct": before_90,
            "days_until_95pct": before_95,
            "days_until_100pct": before_100,
        },
        "after": {
            "used_bytes": int(new_used),
            "free_bytes": int(new_free),
            "utilization_pct": new_util,
            "used_gb": round(new_used / 1e9, 2),
            "free_gb": round(new_free / 1e9, 2),
            "days_until_90pct": after_90,
            "days_until_95pct": after_95,
            "days_until_100pct": after_100,
        },
        "impact": {
            "days_gained_until_90pct": days_gained,
            "utilization_reduction_pct": round(current_util - new_util, 2),
        },
        "recommendations": [
            {
                "id": r["id"],
                "category": r["category"],
                "reason": r["reason"],
                "size_gb": round(r["size_bytes"] / 1e9, 2),
                "risk_level": r["risk_level"],
            }
            for r in recs
        ],
    }
