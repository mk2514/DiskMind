"""
DiskMind – Forecast & Anomaly API Routes
"""
from fastapi import APIRouter, Depends
from backend.database.database import get_db

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


@router.get("/prediction")
async def get_prediction(db=Depends(get_db)):
    from backend.ml.forecast import run_forecast
    return await run_forecast(db)


@router.get("/anomalies")
async def get_anomalies(db=Depends(get_db)):
    from backend.ml.anomaly import run_anomaly_detection
    from backend.database.database import fetchall

    # Return cached anomalies if available
    existing = await fetchall(db, """
        SELECT * FROM anomalies WHERE is_resolved = 0
        ORDER BY anomaly_score DESC LIMIT 10
    """)
    if existing:
        return {"anomalies": existing, "count": len(existing)}

    return await run_anomaly_detection(db)
