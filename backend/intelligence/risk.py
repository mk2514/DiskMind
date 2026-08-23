"""
DiskMind – Risk Engine
Computes cleanup risk levels (LOW / MEDIUM / HIGH / PROTECTED) for files
using a weighted multi-factor scoring model.
"""
from __future__ import annotations

from typing import Any

# ── Risk factor weights ───────────────────────────────────────────────────────
# Positive weights INCREASE risk (file is important/dangerous to delete)
# Negative weights DECREASE risk (file is safe to delete)

W_SYSTEM_PATH          =  40.0
W_PROTECTED_FLAG       =  50.0
W_APP_DEPENDENCY       =  20.0
W_RECENT_ACCESS        =  15.0   # accessed in last 7 days
W_CONFIG_FILE          =  10.0

# Negative (reduces risk → safer to delete)
W_DUPLICATE_CONFIDENCE = -25.0
W_CACHE_TYPE           = -20.0
W_LOG_TYPE             = -15.0
W_BUILD_ARTIFACT       = -18.0
W_INACTIVITY           = -10.0   # scales with inactivity score


RISK_THRESHOLDS = {
    "PROTECTED": 45.0,
    "HIGH":      25.0,
    "MEDIUM":    10.0,
    "LOW":       -999.0,
}

# Applications whose files are considered high-risk to delete
HIGH_RISK_APPS = {"docker", "snap", "flatpak", "conda"}


def compute_risk_score(file_meta: dict[str, Any]) -> tuple[float, str]:
    """
    Returns (risk_score: float, risk_level: str).
    risk_score is unbounded; risk_level is one of LOW/MEDIUM/HIGH/PROTECTED.
    """
    score = 0.0

    # Absolute protection
    if file_meta.get("is_protected"):
        return 100.0, "PROTECTED"

    if file_meta.get("is_system_path"):
        score += W_SYSTEM_PATH

    # Application dependency risk
    app = file_meta.get("application")
    if app in HIGH_RISK_APPS:
        score += W_APP_DEPENDENCY

    # Config file risk
    ftype = file_meta.get("file_type", "other")
    if ftype == "config":
        score += W_CONFIG_FILE

    # Recent access (accessed in last 7 days)
    import time
    now = time.time()
    accessed_at = file_meta.get("accessed_at") or 0
    if (now - accessed_at) < 7 * 86400:
        score += W_RECENT_ACCESS

    # Risk reducers
    if file_meta.get("duplicate_group"):
        score += W_DUPLICATE_CONFIDENCE  # negative = reduces risk

    if ftype == "cache":
        score += W_CACHE_TYPE
    elif ftype == "log":
        score += W_LOG_TYPE
    elif ftype == "build_artifact":
        score += W_BUILD_ARTIFACT

    inactivity = file_meta.get("inactivity_score", 0.0)
    score += W_INACTIVITY * (inactivity / 100.0)  # negative, scales with inactivity

    # Determine level
    level = "LOW"
    for lvl, threshold in RISK_THRESHOLDS.items():
        if score >= threshold:
            level = lvl
            break

    return round(score, 2), level


async def score_all_risks(db) -> int:
    """Update risk scores for all files. Returns count updated."""
    from backend.database.database import fetchall

    files = await fetchall(db, "SELECT * FROM files")
    updated = 0

    for f in files:
        risk_score, risk_level = compute_risk_score(dict(f))
        await db.execute(
            "UPDATE files SET risk_score=?, risk_level=? WHERE id=?",
            (risk_score, risk_level, f["id"]),
        )
        updated += 1

    await db.commit()
    return updated
