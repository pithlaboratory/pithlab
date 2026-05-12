from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Dict, Optional

from core.schemas import TaskRecord, TaskState

logger = logging.getLogger(__name__)


class TaskService:
    """
    v1.5: minimal in-memory task service + SQLite persistence bridge.
    Preserves domain logic while adding durable storage.
    """

    def __init__(self, db_path: str = "data/episodes.db") -> None:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._tasks: Dict[str, TaskRecord] = {}
        self.db_path = db_path
        self._ensure_table()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _execute(self, sql: str, params: tuple) -> None:
        """Helper to execute SQL with proper connection lifecycle and rollback on error."""
        conn = self._get_conn()
        try:
            conn.execute(sql, params)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_table(self) -> None:
        """Создаёт таблицу tasks, если её ещё нет."""
        conn = self._get_conn()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    status TEXT NOT NULL,
                    runtime_version_id TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    metadata_json TEXT
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def create_task(
        self,
        workspace_id: str,
        user_id: str,
        source_interface: str,
        input_text: str,
        intent_type: Optional[str] = None,
    ) -> TaskRecord:
        task = TaskRecord(
            workspace_id=workspace_id,
            owner_id=user_id,
            source_interface=source_interface,
            input_text=input_text,
            intent_type=intent_type,
        )
        
        # ✅ Сохраняем source_interface и intent_type в metadata для БД
        task.metadata["source_interface"] = source_interface
        if intent_type:
            task.metadata["intent_type"] = intent_type

        self._tasks[task.task_id] = task

        # --- SQLite persistence ---
        try:
            self._execute(
                """
                INSERT INTO tasks (
                    id, workspace_id, user_id, query, status, runtime_version_id,
                    created_at, completed_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.task_id,
                    task.workspace_id,
                    task.owner_id,
                    task.input_text,
                    task.status.value,
                    None,
                    task.created_at.isoformat() if task.created_at else datetime.utcnow().isoformat(),
                    task.finished_at.isoformat() if getattr(task, "finished_at", None) else None,
                    json.dumps(task.metadata or {}),
                ),
            )
        except sqlite3.IntegrityError:
            # Задача уже существует в БД (race condition / повторный вызов)
            pass

        return task

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        task = self._tasks.get(task_id)
        if task:
            return task

        conn = self._get_conn()
        try:
            cur = conn.execute(
                """
                SELECT id, workspace_id, user_id, query, status, runtime_version_id,
                       created_at, completed_at, metadata_json
                FROM tasks
                WHERE id = ?
                """,
                (task_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            return None

        metadata = json.loads(row[8]) if row[8] else {}

        task = TaskRecord(
            task_id=row[0],
            workspace_id=row[1],
            owner_id=row[2],
            input_text=row[3],
        )
        
        # ✅ Безопасное восстановление статуса с логированием fallback
        try:
            task.status = TaskState(row[4])
        except ValueError:
            task.status = TaskState.pending
            logger.warning("Invalid status '%s' for task %s, defaulting to pending", row[4], task_id)

        task.created_at = datetime.fromisoformat(row[6]) if row[6] else task.created_at
        task.finished_at = datetime.fromisoformat(row[7]) if row[7] else None
        task.metadata = metadata

        # Restore bridge fields from metadata if present
        task.runtime_version = metadata.get("runtime_version") or row[5]
        task.model_id = metadata.get("model_id")
        task.model_lane = metadata.get("model_lane")
        task.cost_usd = metadata.get("cost_usd", 0.0)
        task.latency_ms = metadata.get("latency_ms", 0)
        task.error_message = metadata.get("error_message")
        task.started_at = datetime.fromisoformat(metadata["started_at"]) if "started_at" in metadata else None
        task.updated_at = datetime.fromisoformat(metadata["updated_at"]) if "updated_at" in metadata else None
        
        # ✅ Восстанавливаем source_interface и intent_type из metadata
        task.source_interface = metadata.get("source_interface", getattr(task, "source_interface", None))
        task.intent_type = metadata.get("intent_type", getattr(task, "intent_type", None))

        self._tasks[task.task_id] = task
        return task

    def update_status(
        self,
        task_id: str,
        new_status: TaskState,
        error_message: Optional[str] = None,
    ) -> Optional[TaskRecord]:
        # ✅ Fallback на БД, если задачи нет в памяти
        task = self._tasks.get(task_id)
        if not task:
            task = self.get_task(task_id)
        if not task:
            return None

        now = datetime.utcnow()
        task.status = new_status
        task.updated_at = now

        if new_status == TaskState.executing and not task.started_at:
            task.started_at = now

        if new_status in (TaskState.completed, TaskState.failed, TaskState.cancelled):
            task.finished_at = now

        if error_message:
            task.error_message = error_message
            task.metadata["error_message"] = error_message

        if task.started_at:
            task.metadata["started_at"] = task.started_at.isoformat()
        if task.updated_at:
            task.metadata["updated_at"] = task.updated_at.isoformat()

        self._tasks[task_id] = task

        # --- SQLite persistence via helper ---
        self._execute(
            "UPDATE tasks SET status = ?, completed_at = ?, metadata_json = ? WHERE id = ?",
            (
                task.status.value,
                task.finished_at.isoformat() if getattr(task, "finished_at", None) else None,
                json.dumps(task.metadata or {}),
                task.task_id,
            ),
        )
        return task

    def attach_execution_result(
        self,
        task_id: str,
        *,
        model_id: Optional[str],
        model_name: Optional[str],
        model_lane: Optional[str],
        cost_usd: float,
        tokens_prompt: int,
        tokens_completion: int,
        latency_ms: int,
    ) -> Optional[TaskRecord]:
        # ✅ Fallback на БД, если задачи нет в памяти
        task = self._tasks.get(task_id)
        if not task:
            task = self.get_task(task_id)
        if not task:
            return None

        task.model_id = model_id
        task.model_lane = model_lane
        task.runtime_version = task.runtime_version or "v5"
        task.cost_usd = cost_usd
        task.latency_ms = latency_ms
        task.metadata["model_name"] = model_name
        task.metadata["tokens_prompt"] = tokens_prompt
        task.metadata["tokens_completion"] = tokens_completion

        # Enrich metadata for persistence bridge
        task.metadata["model_id"] = model_id
        task.metadata["model_lane"] = model_lane
        task.metadata["cost_usd"] = cost_usd
        task.metadata["latency_ms"] = latency_ms
        task.metadata["runtime_version"] = task.runtime_version

        self._tasks[task_id] = task

        # --- SQLite persistence via helper ---
        self._execute(
            "UPDATE tasks SET metadata_json = ? WHERE id = ?",
            (json.dumps(task.metadata or {}), task.task_id),
        )
        return task