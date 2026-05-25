#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "episodes.db"

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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List suspicious/error-like episodes from episodes.db"
    )
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to sqlite db")
    parser.add_argument("--limit", type=int, default=20, help="Max rows to show")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 1

    conn = connect(db_path)

    where = " OR ".join(["LOWER(COALESCE(content, '')) LIKE ?"] * len(BAD_PATTERNS))
    rows = conn.execute(
        f"""
        SELECT id, ts, role, workspace_id, content
        FROM episodes
        WHERE {where}
        ORDER BY id DESC
        LIMIT ?
        """,
        [p.lower() for p in BAD_PATTERNS] + [args.limit],
    ).fetchall()

    if not rows:
        print("No suspicious rows found.")
        return 0

    for row in rows:
        print(
            f"- id={row['id']} ts={row['ts']} role={row['role']} "
            f"workspace={row['workspace_id'] or '-'}"
        )
        print(f"  content: {shorten(row['content'])}")

    print(f"\nDone. Suspicious rows shown: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())