from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any
import time

from backend.database.database import get_db

router = APIRouter(prefix="/api/agent", tags=["agent"])

class DiskInfo(BaseModel):
    mount_point: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    utilization_pct: float

class AgentPayload(BaseModel):
    token: str
    disk_info: DiskInfo
    file_count: int = 0
    dir_count: int = 0
    daily_growth_bytes: int = 0

VALID_TOKEN = "default-dev-token"

@router.post("/upload")
async def upload_metrics(payload: AgentPayload, db=Depends(get_db)):
    if payload.token != VALID_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid agent token")
        
    await db.execute("""
            INSERT INTO storage_snapshots(
                recorded_at, mount_point, total_bytes, used_bytes, free_bytes,
                file_count, dir_count, new_files_today, deleted_files_today,
                daily_growth_bytes, utilization_pct
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            time.time(),
            payload.disk_info.mount_point,
            payload.disk_info.total_bytes,
            payload.disk_info.used_bytes,
            payload.disk_info.free_bytes,
            payload.file_count,
            payload.dir_count,
            0, # new_files
            0, # deleted_files
            payload.daily_growth_bytes,
            payload.disk_info.utilization_pct,
        ))
    await db.commit()
        
    return {"status": "success"}
