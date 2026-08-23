"""
DiskMind – Trash/Cleanup Actions
Safe file operations: move to Trash (XDG-compliant on Linux).
"""
from __future__ import annotations

import os
import platform
import shutil
import time
from pathlib import Path
from typing import Any


def _get_trash_dir() -> Path:
    """Return the XDG Trash directory (Linux) or OS-appropriate trash."""
    system = platform.system()
    if system == "Linux":
        xdg_data = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        return Path(xdg_data) / "Trash"
    elif system == "Darwin":
        return Path.home() / ".Trash"
    else:
        # Windows / demo mode: use a local trash folder
        return Path(__file__).parent.parent.parent / "demo_trash"


async def move_to_trash(db, paths: list[str], recommendation_id: int | None = None) -> dict[str, Any]:
    """
    Move files to the system Trash. Records action in audit log.
    Returns {"success": [...], "failed": [...]}.
    """
    trash_dir = _get_trash_dir()
    (trash_dir / "files").mkdir(parents=True, exist_ok=True)

    success = []
    failed = []

    for path in paths:
        src = Path(path)
        if not src.exists():
            failed.append({"path": path, "error": "File not found"})
            continue

        dest = trash_dir / "files" / src.name
        # Handle name collisions
        counter = 1
        while dest.exists():
            dest = trash_dir / "files" / f"{src.stem}_{counter}{src.suffix}"
            counter += 1

        try:
            size = src.stat().st_size
            shutil.move(str(src), str(dest))
            success.append({"path": path, "dest": str(dest), "size_bytes": size})

            # Log to DB
            await db.execute("""
                INSERT INTO actions_log(executed_at, action, source_path, dest_path,
                    size_bytes, recommendation_id, status)
                VALUES(?,?,?,?,?,?,?)
            """, (time.time(), "trash", path, str(dest), size, recommendation_id, "SUCCESS"))

        except (OSError, PermissionError) as e:
            failed.append({"path": path, "error": str(e)})
            await db.execute("""
                INSERT INTO actions_log(executed_at, action, source_path,
                    recommendation_id, status, error_msg)
                VALUES(?,?,?,?,?,?)
            """, (time.time(), "trash", path, recommendation_id, "FAILED", str(e)))

    await db.commit()
    return {"success": success, "failed": failed, "recovered_bytes": sum(s["size_bytes"] for s in success)}


async def undo_action(db, action_id: int) -> dict[str, Any]:
    """Restore a file from Trash back to its original location."""
    from backend.database.database import fetchone

    action = await fetchone(db, "SELECT * FROM actions_log WHERE id = ?", (action_id,))
    if not action:
        return {"error": "Action not found"}
    if action["status"] == "UNDONE":
        return {"error": "Action already undone"}

    dest = Path(action["dest_path"])
    src = Path(action["source_path"])

    if not dest.exists():
        return {"error": "Trashed file no longer exists at trash location"}

    try:
        src.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dest), str(src))
        await db.execute(
            "UPDATE actions_log SET status='UNDONE', undone_at=? WHERE id=?",
            (time.time(), action_id),
        )
        await db.commit()
        return {"restored": str(src), "from": str(dest)}
    except (OSError, PermissionError) as e:
        return {"error": str(e)}
