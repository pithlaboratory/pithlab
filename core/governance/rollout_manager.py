"""Управление выкатками версий и разрешение рантайм-версий."""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

DB_PATH = Path(__file__).parent.parent.parent / "data" / "episodes.db"

class RolloutManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def start_rollout(self, component_key: str, from_version: str, to_version: str,
                      ring: str, traffic_share: float = 0.05, operator_id: str = "system") -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO patch_rollouts 
                   (component_key, from_version, to_version, ring, traffic_share, status, operator_id)
                   VALUES (?, ?, ?, ?, ?, 'initiated', ?)""",
                (component_key, from_version, to_version, ring, traffic_share, operator_id)
            )
            return cur.lastrowid

    def promote_to_ring(self, rollout_id: int, new_ring: str, traffic_share: float):
        with self._connect() as conn:
            conn.execute(
                "UPDATE patch_rollouts SET ring = ?, traffic_share = ? WHERE id = ?",
                (new_ring, traffic_share, rollout_id)
            )
            self._activate_version(conn, rollout_id, new_ring)

    def complete_rollout(self, rollout_id: int):
        with self._connect() as conn:
            conn.execute(
                "UPDATE patch_rollouts SET status = 'completed', completed_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), rollout_id)
            )

    def rollback(self, rollout_id: int, reason: str):
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT component_key, from_version, ring FROM patch_rollouts WHERE id = ?",
                (rollout_id,)
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Rollout {rollout_id} not found")
            component_key, from_version, ring = row
            conn.execute(
                "UPDATE patch_rollouts SET status = 'rolled_back', rollback_reason = ? WHERE id = ?",
                (reason, rollout_id)
            )
            conn.execute(
                "UPDATE runtime_versions SET active_to = ? WHERE component_key = ? AND ring = ? AND active_to IS NULL",
                (datetime.utcnow().isoformat(), component_key, ring)
            )
            conn.execute(
                "INSERT INTO runtime_versions (component_key, version_ref, ring, deployed_by) VALUES (?, ?, ?, ?)",
                (component_key, from_version, ring, "rollback")
            )

    def _activate_version(self, conn, rollout_id: int, ring: str):
        cur = conn.execute(
            "SELECT component_key, to_version FROM patch_rollouts WHERE id = ?",
            (rollout_id,)
        )
        row = cur.fetchone()
        if not row:
            return
        component_key, to_version = row
        conn.execute(
            "UPDATE runtime_versions SET active_to = ? WHERE component_key = ? AND ring = ? AND active_to IS NULL",
            (datetime.utcnow().isoformat(), component_key, ring)
        )
        conn.execute(
            "INSERT INTO runtime_versions (component_key, version_ref, ring, deployed_by) VALUES (?, ?, ?, ?)",
            (component_key, to_version, ring, f"rollout_{rollout_id}")
        )

class RuntimeResolver:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def resolve(self, component_key: str, ring: str = "full") -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """SELECT version_ref FROM runtime_versions
                   WHERE component_key = ? AND ring = ? AND active_to IS NULL
                   ORDER BY active_from DESC LIMIT 1""",
                (component_key, ring)
            )
            row = cur.fetchone()
            return row[0] if row else None

    def resolve_with_fallback(self, component_key: str, ring: str = "full") -> str:
        for r in [ring, "canary", "owner"]:
            ver = self.resolve(component_key, r)
            if ver:
                return ver
        return "default"
