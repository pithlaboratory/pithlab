import logging
import sqlite3
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class VectorMemory:
    """Заглушка для векторной памяти (в реальности Chroma)."""
    def __init__(self):
        self._store = []

    def add(self, doc_id: str, text: str, metadata: Dict[str, Any]) -> None:
        self._store.append({"id": doc_id, "text": text, "metadata": metadata})

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        results = []
        query_words = query.lower().split()
        for item in self._store:
            if any(word in item["text"].lower() for word in query_words):
                results.append(item)
        return results[:k]


class MemoryManager:
    def __init__(self, db_path: Path = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "episodes.db"
        self.db_path = db_path
        # ✅ Создаём директорию перед подключением к БД
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_memory = VectorMemory()
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT NOT NULL,
                    workspace_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS llm_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    model_name TEXT,
                    tokens_prompt INTEGER,
                    tokens_completion INTEGER,
                    cost REAL,
                    task_type TEXT,
                    topology TEXT,
                    request_id TEXT
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS failure_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    episode_id INTEGER,
                    failure_type TEXT,
                    details_json TEXT,
                    status TEXT DEFAULT 'new'
                )"""
            )

    def save_episode(
        self,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO episodes (user_id, workspace_id, role, content, metadata_json) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    user_id,
                    workspace_id,
                    role,
                    content,
                    json.dumps(metadata, ensure_ascii=False) if metadata else None,
                ),
            )
            return cur.lastrowid

    def update_episode_metadata(self, episode_id: int, patch: Dict[str, Any]) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute(
                    "SELECT metadata_json FROM episodes WHERE id = ?", (episode_id,)
                )
                row = cur.fetchone()
                if not row:
                    logger.warning("Episode %s not found", episode_id)
                    return False

                current_metadata = {}
                if row[0]:
                    try:
                        current_metadata = json.loads(row[0])
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON in metadata for episode %s", episode_id)
                        current_metadata = {}

                current_metadata.update(patch)

                conn.execute(
                    "UPDATE episodes SET metadata_json = ? WHERE id = ?",
                    (json.dumps(current_metadata, ensure_ascii=False), episode_id)
                )
                return True
        except Exception:
            logger.exception("Failed to update episode metadata for episode %s", episode_id)
            return False

    def find_episode_by_task_id(self, user_id: str, task_id: str, role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Находит последний эпизод пользователя по task_id внутри metadata_json."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                query = "SELECT * FROM episodes WHERE user_id = ?"
                params = [user_id]
                if role:
                    query += " AND role = ?"
                    params.append(role)
                query += " ORDER BY ts DESC"

                cur = conn.execute(query, params)
                rows = cur.fetchall()

                for row in rows:
                    if row["metadata_json"]:
                        try:
                            meta = json.loads(row["metadata_json"])
                            if meta.get("task_id") == task_id:
                                return {
                                    "id": row["id"],
                                    "user_id": row["user_id"],
                                    "role": row["role"],
                                    "content": row["content"],
                                    "ts": row["ts"],
                                    "metadata": meta
                                }
                        except json.JSONDecodeError:
                            continue
            return None
        except Exception:
            logger.exception("Failed to find episode by task_id %s for user %s", task_id, user_id)
            return None

    def get_recent_episodes(
        self,
        user_id: str,
        limit: int = 5,
        workspace_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            if workspace_id is not None:
                sql = (
                    "SELECT ts, role, content, metadata_json FROM episodes "
                    "WHERE user_id = ? AND workspace_id = ? "
                    "ORDER BY ts DESC LIMIT ?"
                )
                params = (user_id, workspace_id, limit)
            else:
                sql = (
                    "SELECT ts, role, content, metadata_json FROM episodes "
                    "WHERE user_id = ? "
                    "ORDER BY ts DESC LIMIT ?"
                )
                params = (user_id, limit)

            cur = conn.execute(sql, params)
            rows = cur.fetchall()
            episodes = []
            for row in reversed(rows):
                ep = {"ts": row[0], "role": row[1], "content": row[2]}
                if row[3]:
                    try:
                        ep["metadata"] = json.loads(row[3])
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON in recent episodes for user %s", user_id)
                        ep["metadata"] = {}
                episodes.append(ep)
            return episodes

    @staticmethod
    def _build_context_from_episodes(episodes: List[Dict[str, Any]]) -> str:
        if not episodes:
            return ""
        lines = ["[ПАМЯТЬ: ПОСЛЕДНИЕ ДИАЛОГИ]"]
        for ep in episodes[-5:]:
            lines.append(f"{ep['role']}: {ep['content'][:200]}")
        return "\n".join(lines)

    def build_context(self, user_id: str, current_query: str) -> str:
        # current_query оставлен для совместимости интерфейсов
        episodes = self.get_recent_episodes(user_id, 5)
        return self._build_context_from_episodes(episodes)

    def find_procedures(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        try:
            results = self.vector_memory.search(query, k=limit)
            procedures = []
            for r in results:
                procedures.append({
                    "id": r.get("id"),
                    "name": r.get("metadata", {}).get("name", ""),
                    "description": r.get("text", "")[:200],
                    "triggers": json.loads(r.get("metadata", {}).get("triggers", "[]"))
                })
            return procedures
        except Exception:
            logger.exception("Failed to find procedures")
            return []

    def add_procedure(self, procedure: dict) -> bool:
        try:
            text_to_embed = f"{procedure.get('name', '')} {procedure.get('description', '')} {procedure.get('body', '')}"
            if not text_to_embed.strip():
                return False

            self.vector_memory.add(
                doc_id=procedure.get("id", str(uuid.uuid4())),
                text=text_to_embed,
                metadata={
                    "type": "procedure",
                    "name": procedure.get("name", ""),
                    "triggers": json.dumps(procedure.get("triggers", []))
                }
            )
            return True
        except Exception:
            logger.exception("Failed to add procedure")
            return False


_memory_manager: Optional[MemoryManager] = None


def get_memory() -> MemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
