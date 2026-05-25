#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "episodes.db"


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


def find_candidate_columns(columns: list[str]) -> list[str]:
    wanted = {
        "task_id",
        "trace_id",
        "workspace_id",
        "userid",
        "user_id",
        "role",
        "content",
        "metadata",
        "created_at",
        "updated_at",
        "status",
    }
    out = [c for c in columns if c in wanted]
    if out:
        return out
    return columns[:8]


def maybe_parse_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    s = value.strip()
    if not s:
        return value
    if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
        try:
            return json.loads(s)
        except Exception:
            return value
    return value


def compact(value: Any, max_len: int = 220) -> str:
    value = maybe_parse_json(value)
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, indent=2)
    else:
        text = str(value)
    text = text.strip()
    if len(text) > max_len:
        return text[:max_len] + " …"
    return text


def search_table(conn: sqlite3.Connection, table: str, needle: str) -> list[sqlite3.Row]:
    cols = table_columns(conn, table)
    searchable = [c for c in cols if any(k in c.lower() for k in ("task", "trace", "content", "metadata"))]
    if not searchable:
        return []

    where = " OR ".join([f"CAST(\"{c}\" AS TEXT) LIKE ?" for c in searchable])
    sql = f'SELECT * FROM "{table}" WHERE {where} LIMIT 20'
    params = [f"%{needle}%"] * len(searchable)
    try:
        return conn.execute(sql, params).fetchall()
    except Exception:
        return []


def print_row(table: str, row: sqlite3.Row, full: bool) -> None:
    data = dict(row)
    cols = list(data.keys()) if full else find_candidate_columns(list(data.keys()))
    print(f"\n[{table}]")
    for col in cols:
        print(f"  {col}: {compact(data.get(col), 1200 if full else 220)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect task/trace related records in episodes.db")
    parser.add_argument("needle", help="task_id, trace_id, workspace_id or any identifying fragment")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to sqlite db (default: episodes.db)")
    parser.add_argument("--full", action="store_true", help="Show all columns and larger values")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 1

    conn = connect(db_path)
    tables = list_tables(conn)

    if not tables:
        print("No tables found.")
        return 1

    total_hits = 0
    for table in tables:
        rows = search_table(conn, table, args.needle)
        if not rows:
            continue
        total_hits += len(rows)
        print(f"\n=== table: {table} | hits: {len(rows)} ===")
        for row in rows:
            print_row(table, row, args.full)

    if total_hits == 0:
        print(f"No matches found for: {args.needle}")
        return 2

    print(f"\nDone. Total matched rows: {total_hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())