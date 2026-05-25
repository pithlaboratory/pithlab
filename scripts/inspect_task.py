#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "episodes.db"


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def shorten(text: str | None, limit: int = 220) -> str:
    if text is None:
        return "-"
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + " …"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect episode records by text fragment, role, or workspace_id."
    )
    parser.add_argument("needle", help="Text fragment to search in content/workspace_id/role")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to sqlite db")
    parser.add_argument("--limit", type=int, default=20, help="Max rows to show")
    parser.add_argument("--full", action="store_true", help="Show full content")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 1

    conn = connect(db_path)
    rows = conn.execute(
        """
        SELECT id, ts, role, workspace_id, content
        FROM episodes
        WHERE COALESCE(content, '') LIKE ?
           OR COALESCE(workspace_id, '') LIKE ?
           OR COALESCE(role, '') LIKE ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (f"%{args.needle}%", f"%{args.needle}%", f"%{args.needle}%", args.limit),
    ).fetchall()

    if not rows:
        print(f"No matches found for: {args.needle}")
        return 2

    for row in rows:
        print(f"\n[id={row['id']}] ts={row['ts']} role={row['role']} workspace={row['workspace_id'] or '-'}")
        content = row["content"] if args.full else shorten(row["content"])
        print(f"content: {content}")

    print(f"\nDone. Rows shown: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())