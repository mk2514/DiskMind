"""
DiskMind – FastAPI Application Entry Point
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from backend.database.database import init_db
from backend.api.routes_storage import router as storage_router
from backend.api.routes_ai import router as ai_router
from backend.api.routes_forecast import router as forecast_router
from backend.api.routes_cleanup import router as cleanup_router
from backend.api.routes_agent import router as agent_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup."""
    await init_db()
    yield


app = FastAPI(
    title="DiskMind API",
    description="Predictive AI Storage Copilot for Linux",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Wildcard for hackathon dev, restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(storage_router)
app.include_router(ai_router)
app.include_router(forecast_router)
app.include_router(cleanup_router)
app.include_router(agent_router)


@app.get("/")
async def root():
    return {
        "name": "DiskMind",
        "version": "1.0.0",
        "description": "Predictive AI Storage Copilot for Linux",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
