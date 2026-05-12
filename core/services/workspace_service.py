"""WorkspaceService — управление workspaces."""
import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional

from core.entities import Workspace

logger = logging.getLogger(__name__)


class WorkspaceService:
    """
    v1.5: workspace service с SQLite persistence.
    Сохраняет domain-модель Workspace и async-интерфейс.
    """

    def __init__(self, db_path: str = "data/episodes.db") -> None:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.db_path = db_path
        self._ensure_table()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_table(self) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workspaces (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT,
                    UNIQUE(user_id, name)
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _parse_metadata(self, raw: Optional[str]) -> dict:
        """Безопасный парсинг metadata_json с fallback на пустой dict."""
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in workspace metadata, returning empty dict")
            return {}

    async def resolve(self, user_id: str, workspace_id: Optional[str] = None) -> Workspace:
        if workspace_id:
            ws = await self.get(workspace_id)
            if ws:
                return ws

        default_name = f"personal_{user_id}"
        ws = await self.get_by_name(user_id, default_name)
        if ws:
            return ws

        return await self.create(user_id, default_name)

    async def get(self, workspace_id: str) -> Optional[Workspace]:
        conn = self._get_conn()
        try:
            cur = conn.execute(
                "SELECT id, name, user_id, created_at, metadata_json FROM workspaces WHERE id = ?",
                (workspace_id,)
            )
            row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            return None

        return Workspace(
            id=row[0],
            name=row[1],
            user_id=row[2],
            created_at=datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3],
            metadata=self._parse_metadata(row[4])
        )

    async def get_by_name(self, user_id: str, name: str) -> Optional[Workspace]:
        conn = self._get_conn()
        try:
            cur = conn.execute(
                "SELECT id, name, user_id, created_at, metadata_json FROM workspaces WHERE user_id = ? AND name = ?",
                (user_id, name)
            )
            row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            return None

        return Workspace(
            id=row[0],
            name=row[1],
            user_id=row[2],
            created_at=datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3],
            metadata=self._parse_metadata(row[4])
        )

    async def create(self, user_id: str, name: str, metadata: Optional[dict] = None) -> Workspace:
        ws = Workspace(user_id=user_id, name=name, metadata=metadata or {})

        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO workspaces (id, name, user_id, created_at, metadata_json) VALUES (?, ?, ?, ?, ?)",
                (
                    ws.id,
                    ws.name,
                    ws.user_id,
                    ws.created_at.isoformat(),
                    json.dumps(ws.metadata, ensure_ascii=False)
                )
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # UNIQUE(user_id, name) нарушен → возвращаем уже существующий workspace
            logger.debug("Workspace conflict for user=%s, name=%s. Fetching existing.", user_id, name)
            existing = await self.get_by_name(user_id, name)
            if existing:
                return existing
            raise
        finally:
            conn.close()

        return ws