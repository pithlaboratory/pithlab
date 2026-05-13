from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from core.observability.trace_store import TraceStore
from core.schemas import TaskRecord, TaskState

logger = logging.getLogger(__name__)


class TaskService:
    """
    v1.6.4: minimal in-memory task service + SQLite persistence bridge.
    Preserves domain logic while adding durable storage.

    Trace integration (v1.1 cleanup):
    - task_started() -> при регистрации задачи в runtime (не при старте исполнения!)
    - task_finished() / task_failed() -> при смене статуса
    - Все trace-вызовы обёрнуты в try/except для graceful degradation
    - trace_id correlation: хранится в metadata_json (без миграции БД, без присваивания атрибутов)
    """

    def __init__(self, db_path: str = "data/episodes.db") -> None:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._tasks: Dict[str, TaskRecord] = {}
        self.db_path = db_path
        self._ensure_table()
        self._trace_store = TraceStore(Path(db_path))

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _execute(self, sql: str, params: tuple) -> int:
        """
        Helper to execute SQL with proper connection lifecycle and rollback on error.
        Returns: number of rows affected (for rowcount checks).
        """
        conn = self._get_conn()
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.rowcount
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
        trace_id: Optional[str] = None,
    ) -> TaskRecord:
        task = TaskRecord(
            workspace_id=workspace_id,
            owner_id=user_id,
            source_interface=source_interface,
            input_text=input_text,
            intent_type=intent_type,
        )

        task.metadata["source_interface"] = source_interface
        if intent_type:
            task.metadata["intent_type"] = intent_type
        if trace_id:
            task.metadata["trace_id"] = trace_id

        self._tasks[task.task_id] = task

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
                    task.created_at.isoformat()
                    if task.created_at
                    else datetime.utcnow().isoformat(),
                    task.finished_at.isoformat()
                    if getattr(task, "finished_at", None)
                    else None,
                    json.dumps(task.metadata or {}),
                ),
            )
        except sqlite3.IntegrityError:
            logger.warning(
                "Task %s already exists in DB; possible duplicate create_task call",
                task.task_id,
            )

        try:
            self._trace_store.task_started(
                task_id=task.task_id,
                workspace_id=task.workspace_id,
            )
        except Exception:
            logger.exception(
                "TraceStore.task_started failed for task %s — continuing without trace",
                task.task_id,
            )

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

        try:
            task.status = TaskState(row[4])
        except ValueError:
            task.status = TaskState.pending
            logger.warning(
                "Invalid status '%s' for task %s, defaulting to pending",
                row[4],
                task_id,
            )

        task.created_at = datetime.fromisoformat(row[6]) if row[6] else task.created_at
        task.finished_at = datetime.fromisoformat(row[7]) if row[7] else None
        task.metadata = metadata

        task.runtime_version = metadata.get("runtime_version") or row[5]
        task.model_id = metadata.get("model_id")
        task.model_lane = metadata.get("model_lane")
        task.cost_usd = metadata.get("cost_usd", 0.0)
        task.latency_ms = metadata.get("latency_ms", 0)
        task.error_message = metadata.get("error_message")
        task.started_at = (
            datetime.fromisoformat(metadata["started_at"])
            if "started_at" in metadata
            else None
        )
        task.updated_at = (
            datetime.fromisoformat(metadata["updated_at"])
            if "updated_at" in metadata
            else None
        )

        task.source_interface = metadata.get(
            "source_interface",
            getattr(task, "source_interface", None),
        )
        task.intent_type = metadata.get(
            "intent_type",
            getattr(task, "intent_type", None),
        )

        self._tasks[task.task_id] = task
        return task

    def update_status(
        self,
        task_id: str,
        new_status: TaskState,
        error_message: Optional[str] = None,
    ) -> Optional[TaskRecord]:
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

        if new_status in (
            TaskState.completed,
            TaskState.failed,
            TaskState.cancelled,
        ):
            task.finished_at = now

        if error_message:
            task.error_message = error_message
            task.metadata["error_message"] = error_message

        if task.started_at:
            task.metadata["started_at"] = task.started_at.isoformat()
        if task.updated_at:
            task.metadata["updated_at"] = task.updated_at.isoformat()

        self._tasks[task_id] = task

        rows_affected = self._execute(
            "UPDATE tasks SET status = ?, completed_at = ?, metadata_json = ? WHERE id = ?",
            (
                task.status.value,
                task.finished_at.isoformat()
                if getattr(task, "finished_at", None)
                else None,
                json.dumps(task.metadata or {}),
                task.task_id,
            ),
        )
        if rows_affected == 0:
            logger.warning(
                "UPDATE tasks affected 0 rows for task_id=%s — possible race or missing record",
                task_id,
            )

        try:
            if new_status == TaskState.completed:
                duration_ms = None
                if task.started_at and task.finished_at:
                    duration_ms = int(
                        (task.finished_at - task.started_at).total_seconds() * 1000
                    )
                self._trace_store.task_finished(
                    task.task_id,
                    duration_ms=duration_ms,
                )

            elif new_status in (TaskState.failed, TaskState.cancelled):
                duration_ms = None
                if task.started_at and task.finished_at:
                    duration_ms = int(
                        (task.finished_at - task.started_at).total_seconds() * 1000
                    )
                self._trace_store.task_failed(
                    task.task_id,
                    error_type=new_status.value,
                    duration_ms=duration_ms,
                )
        except Exception:
            logger.exception(
                "TraceStore finalization failed for task %s — task state updated, trace skipped",
                task_id,
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
        trace_id: Optional[str] = None,
    ) -> Optional[TaskRecord]:
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

        task.metadata["model_id"] = model_id
        task.metadata["model_lane"] = model_lane
        task.metadata["cost_usd"] = cost_usd
        task.metadata["latency_ms"] = latency_ms
        task.metadata["runtime_version"] = task.runtime_version
        if trace_id:
            task.metadata["trace_id"] = trace_id

        self._tasks[task_id] = task

        rows_affected = self._execute(
            "UPDATE tasks SET metadata_json = ? WHERE id = ?",
            (json.dumps(task.metadata or {}), task.task_id),
        )
        if rows_affected == 0:
            logger.warning(
                "UPDATE tasks metadata affected 0 rows for task_id=%s",
                task_id,
            )

        return task