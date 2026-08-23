"""
DiskMind – Database Layer
Async SQLite wrapper using aiosqlite.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import aiosqlite

DB_PATH = Path(__file__).parent.parent.parent / "diskmind.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


async def get_db() -> aiosqlite.Connection:
    """FastAPI dependency: yields an async DB connection."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        yield db


async def init_db() -> None:
    """Create all tables from schema.sql if they don't exist."""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript(schema)
        await db.commit()


# ── Generic helpers ────────────────────────────────────────────────────────────

async def fetchall(db: aiosqlite.Connection, sql: str, params: tuple = ()) -> list[dict]:
    async with db.execute(sql, params) as cur:
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def fetchone(db: aiosqlite.Connection, sql: str, params: tuple = ()) -> dict | None:
    async with db.execute(sql, params) as cur:
        row = await cur.fetchone()
        return dict(row) if row else None


async def execute(db: aiosqlite.Connection, sql: str, params: tuple = ()) -> int:
    """Execute a write statement, return lastrowid."""
    async with db.execute(sql, params) as cur:
        await db.commit()
        return cur.lastrowid


async def get_state(db: aiosqlite.Connection, key: str, default: Any = None) -> Any:
    row = await fetchone(db, "SELECT value FROM app_state WHERE key = ?", (key,))
    if row is None:
        return default
    try:
        return json.loads(row["value"])
    except (json.JSONDecodeError, TypeError):
        return row["value"]


async def set_state(db: aiosqlite.Connection, key: str, value: Any) -> None:
    serialized = json.dumps(value) if not isinstance(value, str) else value
    await db.execute(
        "INSERT INTO app_state(key, value, updated_at) VALUES(?,?,unixepoch()) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
        (key, serialized),
    )
    await db.commit()


# ── Sync helpers for non-async contexts (demo generator) ──────────────────────

def get_sync_db(path: Path = DB_PATH) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db_sync(path: Path = DB_PATH) -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    db = get_sync_db(path)
    db.executescript(schema)
    db.commit()
    db.close()
