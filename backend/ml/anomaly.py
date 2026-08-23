"""
DiskMind – Anomaly Detection
Uses Isolation Forest to detect abnormal storage growth patterns.
"""
from __future__ import annotations

import json
import time
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies(snapshots: list[dict]) -> list[dict[str, Any]]:
    """
    Run Isolation Forest on storage snapshot history.
    Returns list of anomalous snapshot records.
    """
    if len(snapshots) < 5:
        return []

    df = pd.DataFrame(snapshots)
    df = df.sort_values("recorded_at").copy()
    df["daily_growth"] = df["used_bytes"].diff().fillna(0)
    df["growth_acceleration"] = df["daily_growth"].diff().fillna(0)
    df["7d_avg"] = df["daily_growth"].rolling(7, min_periods=1).mean()
    df["deviation"] = df["daily_growth"] - df["7d_avg"]

    feature_cols = ["daily_growth", "growth_acceleration", "deviation"]
    X = df[feature_cols].fillna(0).values

    # Isolation Forest: contamination=0.1 means ~10% of samples are anomalies
    clf = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
    predictions = clf.fit_predict(X)
    scores = clf.score_samples(X)

    anomalies = []
    for i, (pred, score) in enumerate(zip(predictions, scores)):
        if pred == -1:  # anomaly
            row = df.iloc[i]
            anomalies.append({
                "snapshot_id": int(row.get("id", i)),
                "recorded_at": float(row["recorded_at"]),
                "anomaly_score": round(float(-score), 4),  # higher = more anomalous
                "growth_gb": round(float(row["daily_growth"]) / 1e9, 3),
                "description": _describe_anomaly(row),
                "utilization_pct": float(row.get("utilization_pct", 0)),
            })

    return sorted(anomalies, key=lambda x: x["anomaly_score"], reverse=True)


def _describe_anomaly(row: pd.Series) -> str:
    growth_gb = row.get("daily_growth", 0) / 1e9
    if growth_gb > 5:
        return f"Abnormal storage growth: +{growth_gb:.1f} GB in a single day"
    elif growth_gb < -2:
        return f"Unusual deletion event: {growth_gb:.1f} GB removed"
    else:
        return f"Storage pattern deviation detected ({growth_gb:+.2f} GB)"


async def run_anomaly_detection(db) -> dict[str, Any]:
    """Load snapshot history and detect anomalies."""
    from backend.database.database import fetchall

    snapshots = await fetchall(db, """
        SELECT id, recorded_at, total_bytes, used_bytes, free_bytes,
               daily_growth_bytes as daily_growth, utilization_pct
        FROM storage_snapshots
        ORDER BY recorded_at ASC
        LIMIT 90
    """)

    if len(snapshots) < 5:
        return {"anomalies": [], "message": "Need at least 5 days of history for anomaly detection."}

    anomalies = detect_anomalies(snapshots)

    # Persist anomalies to DB
    for a in anomalies:
        await db.execute("""
            INSERT INTO anomalies(detected_at, snapshot_id, anomaly_score, growth_gb, description)
            VALUES(?,?,?,?,?)
            ON CONFLICT DO NOTHING
        """, (
            time.time(),
            a.get("snapshot_id"),
            a["anomaly_score"],
            a["growth_gb"],
            a["description"],
        ))
    await db.commit()

    return {
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
    }
