"""
DiskMind – Storage Forecasting ML Model
Uses LinearRegression → RandomForest to predict future storage utilization.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import joblib

MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)
FORECAST_MODEL_PATH = MODEL_DIR / "forecast_model.pkl"
SCALER_PATH = MODEL_DIR / "forecast_scaler.pkl"

FORECAST_HORIZONS_DAYS = [7, 14, 30, 60, 90]


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer time-series features from snapshot history."""
    df = df.sort_values("recorded_at").copy()
    df["day_index"] = range(len(df))
    df["daily_growth"] = df["used_bytes"].diff().fillna(0)
    df["7d_avg_growth"] = df["daily_growth"].rolling(7, min_periods=1).mean()
    df["30d_avg_growth"] = df["daily_growth"].rolling(30, min_periods=1).mean()
    df["utilization_pct"] = df["used_bytes"] / df["total_bytes"] * 100
    df["file_count"] = df["file_count"].fillna(0)
    return df


def train_forecast_model(snapshots: list[dict]) -> dict[str, Any]:
    """
    Train forecast model on historical snapshots.
    Returns a dict with predictions and model metadata.
    """
    if len(snapshots) < 3:
        return _linear_extrapolation(snapshots)

    df = pd.DataFrame(snapshots)
    df = _build_features(df)

    feature_cols = ["day_index", "daily_growth", "7d_avg_growth", "30d_avg_growth"]
    X = df[feature_cols].fillna(0).values
    y = df["used_bytes"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Use Random Forest if enough data, else Linear Regression
    if len(df) >= 14:
        model = RandomForestRegressor(n_estimators=100, random_state=42)
    else:
        model = LinearRegression()

    model.fit(X_scaled, y)

    # Persist model
    joblib.dump(model, FORECAST_MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    # Generate predictions
    total_bytes = df["total_bytes"].iloc[-1]
    last_idx = df["day_index"].iloc[-1]
    avg_daily = df["7d_avg_growth"].iloc[-1]

    predictions = {}
    for horizon in FORECAST_HORIZONS_DAYS:
        future_idx = last_idx + horizon
        future_X = np.array([[future_idx, avg_daily, avg_daily, avg_daily]])
        future_X_scaled = scaler.transform(future_X)
        pred_used = float(model.predict(future_X_scaled)[0])
        pred_used = max(0, min(pred_used, total_bytes))
        predictions[f"days_{horizon}"] = {
            "used_bytes": int(pred_used),
            "free_bytes": int(total_bytes - pred_used),
            "utilization_pct": round(pred_used / total_bytes * 100, 2) if total_bytes > 0 else 0,
        }

    # Days until 90% / 95% / 100%
    current_used = int(df["used_bytes"].iloc[-1])
    thresholds = {}
    for pct in [90, 95, 100]:
        target = total_bytes * pct / 100
        if avg_daily > 0 and current_used < target:
            days = int((target - current_used) / avg_daily)
        elif current_used >= target:
            days = 0
        else:
            days = 999
        thresholds[f"days_until_{pct}pct"] = days

    # Build daily forecast series (30 days)
    daily_series = []
    for d in range(31):
        future_used = current_used + avg_daily * d
        future_used = max(0, min(future_used, total_bytes))
        daily_series.append({
            "day": d,
            "used_bytes": int(future_used),
            "utilization_pct": round(future_used / total_bytes * 100, 2) if total_bytes > 0 else 0,
        })

    return {
        "model_type": "random_forest" if len(df) >= 14 else "linear_regression",
        "training_samples": len(df),
        "avg_daily_growth_bytes": int(avg_daily),
        "current_used_bytes": current_used,
        "total_bytes": int(total_bytes),
        "predictions": predictions,
        "thresholds": thresholds,
        "daily_series": daily_series,
    }


def _linear_extrapolation(snapshots: list[dict]) -> dict[str, Any]:
    """Simple linear extrapolation when not enough data for ML."""
    if not snapshots:
        return {}

    last = snapshots[-1]
    total = last.get("total_bytes", 1)
    current_used = last.get("used_bytes", 0)

    # Estimate daily growth from available snapshots
    if len(snapshots) >= 2:
        first = snapshots[0]
        days_diff = max((last["recorded_at"] - first["recorded_at"]) / 86400, 1)
        avg_daily = (last["used_bytes"] - first["used_bytes"]) / days_diff
    else:
        avg_daily = total * 0.005  # assume 0.5%/day

    predictions = {}
    for horizon in FORECAST_HORIZONS_DAYS:
        pred_used = current_used + avg_daily * horizon
        pred_used = max(0, min(pred_used, total))
        predictions[f"days_{horizon}"] = {
            "used_bytes": int(pred_used),
            "free_bytes": int(total - pred_used),
            "utilization_pct": round(pred_used / total * 100, 2),
        }

    thresholds = {}
    for pct in [90, 95, 100]:
        target = total * pct / 100
        if avg_daily > 0 and current_used < target:
            days = int((target - current_used) / avg_daily)
        elif current_used >= target:
            days = 0
        else:
            days = 999
        thresholds[f"days_until_{pct}pct"] = days

    daily_series = []
    for d in range(31):
        future_used = current_used + avg_daily * d
        future_used = max(0, min(future_used, total))
        daily_series.append({
            "day": d,
            "used_bytes": int(future_used),
            "utilization_pct": round(future_used / total * 100, 2),
        })

    return {
        "model_type": "linear_extrapolation",
        "training_samples": len(snapshots),
        "avg_daily_growth_bytes": int(avg_daily),
        "current_used_bytes": current_used,
        "total_bytes": int(total),
        "predictions": predictions,
        "thresholds": thresholds,
        "daily_series": daily_series,
    }


async def run_forecast(db) -> dict[str, Any]:
    """Load snapshots from DB and run the forecast model."""
    from backend.database.database import fetchall

    snapshots = await fetchall(db, """
        SELECT recorded_at, total_bytes, used_bytes, free_bytes,
               file_count, daily_growth_bytes
        FROM storage_snapshots
        ORDER BY recorded_at ASC
        LIMIT 90
    """)

    if not snapshots:
        return {"error": "No storage history available. Run a scan first."}

    return train_forecast_model(snapshots)
