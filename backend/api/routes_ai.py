"""
DiskMind – AI & Recommendations API Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.database.database import get_db, fetchall

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatRequest(BaseModel):
    messages: list[dict]
    session_id: str = "default"


class SimulateRequest(BaseModel):
    recommendation_ids: list[int]


@router.post("/chat")
async def chat_endpoint(req: ChatRequest, db=Depends(get_db)):
    from backend.ai.assistant import chat
    result = await chat(db, req.messages)
    return result


@router.get("/recommendations")
async def get_recommendations(db=Depends(get_db)):
    from backend.ai.recommendations import generate_recommendations

    # Check if there are existing pending recommendations
    existing = await fetchall(db, """
        SELECT * FROM recommendations WHERE status = 'PENDING'
        ORDER BY size_bytes DESC LIMIT 30
    """)

    if existing:
        return existing

    # Generate fresh recommendations
    return await generate_recommendations(db)


@router.post("/simulate")
async def simulate_endpoint(req: SimulateRequest, db=Depends(get_db)):
    from backend.actions.simulator import simulate_recommendations
    return await simulate_recommendations(db, req.recommendation_ids)


@router.get("/health-score")
async def get_health_score(db=Depends(get_db)):
    from backend.ai.tools import tool_get_storage_summary
    from backend.ai.recommendations import compute_storage_health_score
    summary = await tool_get_storage_summary(db)
    return {"health_score": summary.get("health_score", 0), "summary": summary}
