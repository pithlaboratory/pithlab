#!/usr/bin/env python3
"""Мониторинг canary-выкаток и автоматическое продвижение."""
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))
from core.governance.rollout_manager import RolloutManager

DB_PATH = Path(__file__).parent.parent / "data" / "episodes.db"

def main():
    rm = RolloutManager()
    conn = sqlite3.connect(DB_PATH)
    
    # Находим canary-выкатки старше 24 часов
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    cur = conn.execute("""
        SELECT id, component_key FROM patch_rollouts
        WHERE ring = 'canary' AND status = 'active'
          AND started_at < ?
    """, (cutoff,))
    
    rows = cur.fetchall()
    for rollout_id, component in rows:
        try:
            rm.promote_to_ring(rollout_id, "full", 1.0)
            print(f"[{datetime.utcnow()}] Auto-promoted rollout {rollout_id} ({component}) to full")
        except Exception as e:
            print(f"[{datetime.utcnow()}] ERROR promoting rollout {rollout_id}: {e}")
    
    conn.close()

if __name__ == "__main__":
    main()
