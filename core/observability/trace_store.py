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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_traces (
                    task_id      TEXT PRIMARY KEY,
                    workspace_id TEXT,
                    status       TEXT NOT NULL DEFAULT 'running',
                    error_type   TEXT,
                    score_final  REAL,
                    started_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    finished_at  TIMESTAMP,
                    duration_ms  INTEGER
                )
            """)

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def task_started(self, task_id: str, workspace_id: Optional[str] = None) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO task_traces (task_id, workspace_id, status) VALUES (?, ?, 'running')",
                (task_id, workspace_id),
            )

    def task_finished(self, task_id: str, duration_ms: Optional[int] = None) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE task_traces SET status='ok', finished_at=CURRENT_TIMESTAMP, duration_ms=? WHERE task_id=?",
                (duration_ms, task_id),
            )

    def task_failed(self, task_id: str, error_type: Optional[str] = None, duration_ms: Optional[int] = None) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE task_traces SET status='error', error_type=?, finished_at=CURRENT_TIMESTAMP, duration_ms=? WHERE task_id=?",
                (error_type, duration_ms, task_id),
            )

    def evaluator_score(self, task_id: str, score: float) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE task_traces SET score_final=? WHERE task_id=?",
                (score, task_id),
            )
