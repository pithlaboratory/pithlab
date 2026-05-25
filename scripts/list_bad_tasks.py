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

BAD_PATTERNS = [
    "%error%",
    "%exception%",
    "%traceback%",
    "%failed%",
    "%failure%",
    "%orchestration%",
    "%model access unavailable%",
    "%governance refusal%",
    "%data exfiltration%",
    "%workspace isolation%",
    "%dangerous delete%",
]


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
        description="List suspicious/error-like episodes from data/episodes.db"
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

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 1

    conn = connect(db_path)

    # условия по паттернам
    pattern_clause = "(" + " OR ".join(
        [
            "LOWER(COALESCE(content, '')) LIKE ?",
            "LOWER(COALESCE(metadata_json, '')) LIKE ?",
        ]
    ) + ")"

    where_clauses = [pattern_clause]
    params: list[Any] = []

    # для каждого BAD_PATTERN кладём два раза (content, metadata_json)
    for p in BAD_PATTERNS:
        lower = p.lower()
        params.append(lower)
        params.append(lower)

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
        print("No suspicious rows found.")
        return 0

    for row in rows:
        print(
            f"- id={row['id']} ts={row['ts']} user_id={row['user_id']} "
            f"workspace={row['workspace_id'] or '-'} role={row['role']}"
        )
        print(f"  content:  {shorten(row['content'])}")
        print(f"  metadata: {shorten_json(row['metadata_json'])}")

    print(f"\nDone. Suspicious rows shown: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
