from __future__ import annotations
import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

DB_PATH = "/root/pith_v5/data/episodes.db"

class LLMLogger:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def log_call(
        self,
        *,
        user_id: str,
        agent_name: str,
        channel: str,
        model_id: str,
        model_name: str,
        prompt: str,
        response: str,
        tokens_prompt: int,
        tokens_completion: int,
        cost: float,
        task_type: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO llm_calls (
                    ts, user_id, agent_name, channel, model_id, model_name,
                    prompt, response, tokens_prompt, tokens_completion,
                    cost, task_type, meta_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    user_id,
                    agent_name,
                    channel,
                    model_id,
                    model_name,
                    prompt,
                    response,
                    tokens_prompt,
                    tokens_completion,
                    cost,
                    task_type,
                    json.dumps(meta or {}, ensure_ascii=False),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_daily_cost(self) -> float:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                """
                SELECT COALESCE(SUM(cost), 0.0)
                FROM llm_calls
                WHERE ts >= date('now', 'start of day')
                """
            )
            row = cur.fetchone()
            return float(row[0] or 0.0)
        finally:
            conn.close()

llm_logger = LLMLogger()
