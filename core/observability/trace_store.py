import sqlite3
from typing import Optional
from pathlib import Path

DB_PATH = Path("data/episodes.db")


class TraceStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self):
        with sqlite3.connect(self.db_path) as conn:
            # 1. Создаём таблицу, если её ещё нет (базовая схема)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_traces (
                    task_id             TEXT PRIMARY KEY,
                    workspace_id        TEXT,
                    status              TEXT NOT NULL DEFAULT 'running',
                    error_type          TEXT,
                    score_final         REAL,
                    started_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    finished_at         TIMESTAMP,
                    duration_ms         INTEGER
                )
            """)

            # 2. Безопасная миграция: проверяем существующие колонки и добавляем отсутствующие
            existing_cols = {
                row[1] for row in conn.execute("PRAGMA table_info(task_traces)")
            }

            required_columns = {
                "failure_class": "TEXT",
                "error_code": "TEXT",
                "runtime_mode": "TEXT",
                "task_type": "TEXT",
                "cost_estimate_usd": "REAL",
                "runtime_config_ver": "TEXT",
            }

            for col_name, col_type in required_columns.items():
                if col_name not in existing_cols:
                    conn.execute(
                        f"ALTER TABLE task_traces ADD COLUMN {col_name} {col_type}"
                    )

    def task_started(
        self,
        task_id: str,
        workspace_id: Optional[str] = None,
        runtime_mode: Optional[str] = None,
        task_type: Optional[str] = None,
        runtime_config_ver: Optional[str] = None,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            # Создаём запись, если её нет
            conn.execute(
                """
                INSERT OR IGNORE INTO task_traces (
                    task_id, workspace_id, status, runtime_mode, task_type, runtime_config_ver
                ) VALUES (?, ?, 'running', ?, ?, ?)
                """,
                (task_id, workspace_id, runtime_mode, task_type, runtime_config_ver),
            )
            # Мягкая дозапись metadata без overwrite уже заполненных значений
            conn.execute(
                """
                UPDATE task_traces
                SET workspace_id = COALESCE(workspace_id, ?),
                    runtime_mode = COALESCE(runtime_mode, ?),
                    task_type = COALESCE(task_type, ?),
                    runtime_config_ver = COALESCE(runtime_config_ver, ?)
                WHERE task_id = ?
                """,
                (workspace_id, runtime_mode, task_type, runtime_config_ver, task_id),
            )

    def task_finished(
        self,
        task_id: str,
        duration_ms: Optional[int] = None,
        cost_estimate_usd: Optional[float] = None,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE task_traces
                SET status='ok',
                    finished_at=CURRENT_TIMESTAMP,
                    duration_ms=?,
                    cost_estimate_usd=?
                WHERE task_id=?
                """,
                (duration_ms, cost_estimate_usd, task_id),
            )

    def task_failed(
        self,
        task_id: str,
        error_type: Optional[str] = None,
        failure_class: Optional[str] = None,
        error_code: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE task_traces
                SET status='error',
                    error_type=?,
                    failure_class=?,
                    error_code=?,
                    finished_at=CURRENT_TIMESTAMP,
                    duration_ms=?
                WHERE task_id=?
                """,
                (error_type, failure_class, error_code, duration_ms, task_id),
            )

    def evaluator_score(self, task_id: str, score: float) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE task_traces SET score_final=? WHERE task_id=?",
                (score, task_id),
            )