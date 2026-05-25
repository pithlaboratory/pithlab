#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "episodes.db"

BAD_PATTERNS = [
    "%failed%",
    "%error%",
    "%exception%",
    "%traceback%",
    "%orchestrationfailed%",
    "%modelunavailable%",
    "%governancerefusal%",
]


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [r["name"] for r in rows]


def table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
    return [r["name"] for r in rows]


def relevant_columns(columns: list[str]) -> list[str]:
    keys = ("task", "trace", "status", "error", "eval", "metadata", "content", "created", "updated")
    return [c for c in columns if any(k in c.lower() for k in keys)]


def find_bad_rows(conn: sqlite3.Connection, table: str, limit: int) -> list[sqlite3.Row]:
    cols = table_columns(conn, table)
    searchable = relevant_columns(cols)
    if not searchable:
        return []

    clauses = []
    params = []
    for col in searchable:
        for pattern in BAD_PATTERNS:
            clauses.append(f'LOWER(CAST("{col}" AS TEXT)) LIKE ?')
            params.append(pattern.lower())

    sql = f'''
        SELECT * FROM "{table}"
        WHERE {" OR ".join(clauses)}
        LIMIT {int(limit)}
    '''
    try:
        return conn.execute(sql, params).fetchall()
    except Exception:
        return []


def pick(data: dict, *names: str) -> str:
    for name in names:
        if name in data and data[name] not in (None, ""):
            return str(data[name])
    return "-"


def shorten(text: str, size: int = 180) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= size else text[:size] + " …"


def main() -> int:
    parser = argparse.ArgumentParser(description="List suspicious/bad task-like rows from episodes.db")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to sqlite db")
    parser.add_argument("--limit", type=int, default=20, help="Max rows per table")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 1

    conn = connect(db_path)
    total = 0

    for table in list_tables(conn):
        rows = find_bad_rows(conn, table, args.limit)
        if not rows:
            continue

        print(f"\n=== {table} | suspicious rows: {len(rows)} ===")
        for row in rows:
            data = dict(row)
            task_id = pick(data, "task_id", "taskid")
            trace_id = pick(data, "trace_id", "traceid")
            status = pick(data, "status", "state")
            created = pick(data, "created_at", "updated_at", "timestamp")
            preview = pick(data, "error", "content", "metadata", "eval")
            print(
                f"- task={task_id} trace={trace_id} status={status} created={created}\n"
                f"  preview={shorten(preview)}"
            )
            total += 1

    if total == 0:
        print("No suspicious rows found.")
        return 0

    print(f"\nDone. Total suspicious rows shown: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())