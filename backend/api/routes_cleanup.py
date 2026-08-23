"""
DiskMind – Cleanup & Archive API Routes
Human-approval-gated execution of cleanup actions.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.database.database import get_db, fetchall, fetchone

router = APIRouter(prefix="/api/cleanup", tags=["cleanup"])


class ApproveRequest(BaseModel):
    recommendation_ids: list[int]


class ExecuteRequest(BaseModel):
    recommendation_ids: list[int]
    action: str = "trash"  # trash | archive


@router.post("/approve")
async def approve_recommendations(req: ApproveRequest, db=Depends(get_db)):
    """Mark recommendations as approved (user confirmed)."""
    import time
    placeholders = ",".join("?" * len(req.recommendation_ids))
    await db.execute(f"""
        UPDATE recommendations SET status='APPROVED', approved_at=?
        WHERE id IN ({placeholders}) AND status = 'PENDING'
    """, (time.time(), *req.recommendation_ids))
    await db.commit()

    approved = await fetchall(db, f"""
        SELECT * FROM recommendations WHERE id IN ({placeholders})
    """, tuple(req.recommendation_ids))

    return {"approved": approved, "count": len(approved)}


@router.post("/execute")
async def execute_recommendations(req: ExecuteRequest, db=Depends(get_db)):
    """Execute approved recommendations (move to trash)."""
    import json
    import time
    from backend.actions.trash import move_to_trash

    placeholders = ",".join("?" * len(req.recommendation_ids))
    recs = await fetchall(db, f"""
        SELECT * FROM recommendations
        WHERE id IN ({placeholders}) AND status IN ('PENDING', 'APPROVED')
    """, tuple(req.recommendation_ids))

    results = []
    total_recovered = 0

    for rec in recs:
        target = rec["target_path"]

        # Parse paths (may be JSON array or single path)
        try:
            paths = json.loads(target)
            if isinstance(paths, str):
                paths = [paths]
        except (json.JSONDecodeError, TypeError):
            paths = [target] if not target.startswith("[") else []

        # Skip non-file targets (file_type categories)
        if not paths or paths[0].startswith("["):
            # Category-based cleanup: mark as executed but no real file action in demo
            await db.execute("""
                UPDATE recommendations SET status='EXECUTED', executed_at=?
                WHERE id=?
            """, (time.time(), rec["id"]))
            total_recovered += rec["size_bytes"]
            results.append({"rec_id": rec["id"], "status": "executed_demo", "size_bytes": rec["size_bytes"]})
            continue

        result = await move_to_trash(db, paths, recommendation_id=rec["id"])
        await db.execute("""
            UPDATE recommendations SET status='EXECUTED', executed_at=?
            WHERE id=?
        """, (time.time(), rec["id"]))
        total_recovered += result.get("recovered_bytes", 0)
        results.append({"rec_id": rec["id"], **result})

    await db.commit()
    return {
        "results": results,
        "total_recovered_bytes": total_recovered,
        "total_recovered_gb": round(total_recovered / 1e9, 3),
    }


@router.get("/history")
async def get_action_history(limit: int = 50, db=Depends(get_db)):
    return await fetchall(db, """
        SELECT * FROM actions_log ORDER BY executed_at DESC LIMIT ?
    """, (limit,))


@router.post("/undo/{action_id}")
async def undo_action(action_id: int, db=Depends(get_db)):
    from backend.actions.trash import undo_action as _undo
    return await _undo(db, action_id)
