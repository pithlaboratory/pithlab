from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ArtifactService:
    """
    v1.1: SQLite-backed artifact persistence (async-safe).
    Stores outputs linked to task + workspace.
    """

    def __init__(self, db_path: str = "data/episodes.db") -> None:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    content TEXT,
                    file_path TEXT,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT
                )
                """
            )
            # ✅ Индексы для быстрого поиска
            conn.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_task ON artifacts(task_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_workspace ON artifacts(workspace_id)")
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Конвертирует кортеж БД в единый формат dict."""
        return {
            "id": row[0],
            "task_id": row[1],
            "workspace_id": row[2],
            "artifact_type": row[3],
            "content": row[4],
            "file_path": row[5],
            "created_at": row[6],
            "metadata": json.loads(row[7]) if row[7] else {},
        }

    async def create_artifact(
        self,
        task_id: str,
        workspace_id: str,
        artifact_type: str,
        content: Optional[str] = None,
        file_path: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        artifact_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        metadata = metadata or {}

        def _insert():
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(
                    """
                    INSERT INTO artifacts (
                        id, task_id, workspace_id, artifact_type, content, file_path, created_at, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        artifact_id,
                        task_id,
                        workspace_id,
                        artifact_type,
                        content,
                        file_path,
                        created_at,
                        json.dumps(metadata),
                    ),
                )
                conn.commit()
            finally:
                conn.close()

        try:
            await asyncio.to_thread(_insert)
        except Exception as e:
            logger.error("Failed to create artifact %s: %s", artifact_id, e, exc_info=True)
            raise

        return {
            "id": artifact_id,
            "task_id": task_id,
            "workspace_id": workspace_id,
            "artifact_type": artifact_type,
            "content": content,
            "file_path": file_path,
            "created_at": created_at,
            "metadata": metadata,
        }

    async def get_artifact(self, artifact_id: str) -> Optional[dict]:
        def _fetch():
            conn = sqlite3.connect(self.db_path)
            try:
                cur = conn.execute(
                    "SELECT id, task_id, workspace_id, artifact_type, content, file_path, created_at, metadata_json FROM artifacts WHERE id = ?",
                    (artifact_id,),
                )
                return cur.fetchone()
            finally:
                conn.close()

        try:
            row = await asyncio.to_thread(_fetch)
            return self._row_to_dict(row) if row else None
        except Exception as e:
            logger.error("Failed to fetch artifact %s: %s", artifact_id, e)
            return None

    async def list_by_task(self, task_id: str) -> list[dict]:
        def _fetch_all():
            conn = sqlite3.connect(self.db_path)
            try:
                cur = conn.execute(
                    "SELECT id, task_id, workspace_id, artifact_type, content, file_path, created_at, metadata_json FROM artifacts WHERE task_id = ? ORDER BY created_at ASC",
                    (task_id,),
                )
                return cur.fetchall()
            finally:
                conn.close()

        try:
            rows = await asyncio.to_thread(_fetch_all)
            return [self._row_to_dict(r) for r in rows]
        except Exception as e:
            logger.error("Failed to list artifacts for task %s: %s", task_id, e)
            return []

    async def list_by_workspace(self, workspace_id: str) -> list[dict]:
        def _fetch_all():
            conn = sqlite3.connect(self.db_path)
            try:
                cur = conn.execute(
                    "SELECT id, task_id, workspace_id, artifact_type, content, file_path, created_at, metadata_json FROM artifacts WHERE workspace_id = ? ORDER BY created_at DESC",
                    (workspace_id,),
                )
                return cur.fetchall()
            finally:
                conn.close()

        try:
            rows = await asyncio.to_thread(_fetch_all)
            return [self._row_to_dict(r) for r in rows]
        except Exception as e:
            logger.error("Failed to list artifacts for workspace %s: %s", workspace_id, e)
            return []