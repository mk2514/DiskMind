"""
DiskMind – Inactivity Scoring
Computes a weighted inactivity score (0=active, 100=inactive) for each file.
"""
from __future__ import annotations

import time
from typing import Any

# ── Weighting coefficients ────────────────────────────────────────────────────
W_ACCESS_AGE        = 0.30
W_MODIFICATION_AGE  = 0.20
W_ACCESS_FREQUENCY  = 0.15   # lower freq → higher score
W_DUPLICATE_STATUS  = 0.15
W_FILE_TYPE         = 0.10
W_APP_RELEVANCE     = 0.10   # lower relevance → higher score

# File type inactivity biases (0=likely active, 1=likely inactive)
FILE_TYPE_BIAS: dict[str, float] = {
    "cache": 0.90,
    "log": 0.75,
    "build_artifact": 0.80,
    "archive": 0.60,
    "media": 0.50,
    "document": 0.30,
    "source_code": 0.20,
    "config": 0.10,
    "system": 0.05,
    "other": 0.40,
}

# Max ages for normalization (seconds)
MAX_ACCESS_AGE_SECS      = 365 * 24 * 3600   # 1 year
MAX_MODIFICATION_AGE_SECS = 365 * 24 * 3600


def _normalize_age(age_secs: float, max_secs: float) -> float:
    """0 = just accessed, 1 = very old."""
    return min(age_secs / max_secs, 1.0) if max_secs > 0 else 0.0


def compute_inactivity_score(file_meta: dict[str, Any], now: float | None = None) -> float:
    """
    Returns inactivity score 0–100.
    Higher = more inactive = more suitable for cleanup.
    """
    if now is None:
        now = time.time()

    # Access age
    accessed_at = file_meta.get("accessed_at") or file_meta.get("modified_at") or now
    access_age = _normalize_age(now - accessed_at, MAX_ACCESS_AGE_SECS)

    # Modification age
    modified_at = file_meta.get("modified_at") or now
    mod_age = _normalize_age(now - modified_at, MAX_MODIFICATION_AGE_SECS)

    # Access frequency (not tracked in schema directly — use modified_at proxy)
    # If accessed recently relative to modification: frequently used
    freq_ratio = max(0.0, min(1.0, (now - accessed_at) / max(now - modified_at + 1, 1)))
    freq_score = freq_ratio  # high ratio = low access frequency

    # Duplicate status
    is_dup = 1.0 if file_meta.get("duplicate_group") else 0.0

    # File type bias
    ftype = file_meta.get("file_type", "other")
    type_bias = FILE_TYPE_BIAS.get(ftype, 0.40)

    # Application relevance (0=irrelevant app=inactive, 1=active app)
    app = file_meta.get("application")
    app_relevance = 0.3 if app else 0.0  # known-app files have slightly more relevance
    inv_app_relevance = 1.0 - app_relevance

    score = (
        W_ACCESS_AGE       * access_age
        + W_MODIFICATION_AGE * mod_age
        + W_ACCESS_FREQUENCY * freq_score
        + W_DUPLICATE_STATUS * is_dup
        + W_FILE_TYPE        * type_bias
        + W_APP_RELEVANCE    * inv_app_relevance
    )

    return round(min(score * 100, 100.0), 2)


async def score_all_files(db) -> int:
    """Compute and update inactivity scores for all files in DB. Returns count updated."""
    from backend.database.database import fetchall

    files = await fetchall(db, "SELECT * FROM files WHERE is_protected = 0")
    now = time.time()
    updated = 0

    for f in files:
        score = compute_inactivity_score(dict(f), now)
        await db.execute(
            "UPDATE files SET inactivity_score=? WHERE id=?",
            (score, f["id"]),
        )
        updated += 1

    await db.commit()
    return updated
