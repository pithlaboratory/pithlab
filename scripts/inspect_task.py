#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "episodes.db"


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def shorten(text: str | None, limit: int = 220) -> str:
    if text is None:
        return "-"
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + " …"


def shorten_json(metadata_json: str | None, limit: int = 220) -> str:
    if not metadata_json:
        return "-"
    try:
        obj: Any = json.loads(metadata_json)
        text = json.dumps(obj, ensure_ascii=False)
    except Exception:
        text = metadata_json
    text = text.strip()
    return text if len(text) <= limit else text[:limit] + " …"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect episodes in data/episodes.db by text, task_id, trace_id, role, workspace, user."
    )
    parser.add_argument(
        "needle",
        nargs="?",
        default=None,
        help="Text fragment to search in content/metadata_json/workspace_id/user_id",
    )
    parser.add_argument(
        "--task-id",
        help="Exact task_id match from metadata_json",
    )
    parser.add_argument(
        "--trace-id",
        help="Exact trace_id match from metadata_json",
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB),
        help="Path to sqlite db (default: data/episodes.db)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max rows to show",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Show full content (not truncated)",
    )
    parser.add_argument(
        "--role",
        choices=["user", "assistant"],
        help="Filter by role",
    )
    parser.add_argument(
        "--workspace",
        help="Filter by workspace_id prefix",
    )
    parser.add_argument(
        "--user",
        help="Filter by user_id",
    )
    args = parser.parse_args()

    if not args.needle and not args.task_id and not args.trace_id:
        parser.error("Provide either needle, --task-id, or --trace-id")

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 1

    conn = connect(db_path)

    where_clauses = []
    params: list[Any] = []

    if args.needle:
        where_clauses.append(
            "("
            "COALESCE(content, '') LIKE ? "
            "OR COALESCE(metadata_json, '') LIKE ? "
            "OR COALESCE(workspace_id, '') LIKE ? "
            "OR COALESCE(user_id, '') LIKE ?"
            ")"
        )
        params.extend([f"%{args.needle}%"] * 4)

    if args.task_id:
        where_clauses.append(
            "("
            "json_valid(COALESCE(metadata_json, '')) = 1 "
            "AND json_extract(metadata_json, '$.task_id') = ?"
            ")"
        )
        params.append(args.task_id)

    if args.trace_id:
        where_clauses.append(
            "("
            "json_valid(COALESCE(metadata_json, '')) = 1 "
            "AND json_extract(metadata_json, '$.trace_id') = ?"
            ")"
        )
        params.append(args.trace_id)

    if args.role:
        where_clauses.append("role = ?")
        params.append(args.role)

    if args.workspace:
        where_clauses.append("workspace_id LIKE ?")
        params.append(f"{args.workspace}%")

    if args.user:
        where_clauses.append("user_id = ?")
        params.append(args.user)

    where_sql = " AND ".join(where_clauses)

    sql = f"""
        SELECT id, ts, user_id, workspace_id, role, content, metadata_json
        FROM episodes
        WHERE {where_sql}
        ORDER BY id DESC
        LIMIT ?
    """
    params.append(args.limit)

    rows = conn.execute(sql, params).fetchall()

    if not rows:
        q = args.needle or args.task_id or args.trace_id
        print(f"No matches found for: {q}")
        return 2

    for row in rows:
        print(
            f"\n[id={row['id']}] ts={row['ts']} "
            f"user_id={row['user_id']} workspace={row['workspace_id'] or '-'} "
            f"role={row['role']}"
        )
        content = row["content"] if args.full else shorten(row["content"])
        print(f"content: {content}")
        print(f"metadata: {shorten_json(row['metadata_json'])}")

    print(f"\nDone. Rows shown: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())