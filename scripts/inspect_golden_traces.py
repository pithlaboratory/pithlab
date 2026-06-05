#!/usr/bin/env python3
import argparse
import sqlite3
from pathlib import Path
from textwrap import shorten

DB_PATH = Path("data/episodes.db")

def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise SystemExit(f"DB file not found: {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def _fmt_ms(v):
    """Format duration_ms: '123 ms' or 'n/a'."""
    return f"{int(v)} ms" if isinstance(v, (int, float)) else "n/a"

def _fmt_cost(v):
    """Format cost_estimate_usd: '0.000123' or 'n/a'."""
    return f"{v:.6f}" if isinstance(v, (int, float)) else "n/a"

def print_row(row: sqlite3.Row, fields):
    parts = []
    for f in fields:
        v = row[f]
        if isinstance(v, str) and len(v) > 120:
            v = shorten(v, width=120, placeholder="…")
        parts.append(f"{f}={v}")
    print(" | ".join(parts))

def list_golden_tasks(conn: sqlite3.Connection, limit: int):
    cur = conn.execute(
        """
        SELECT id, workspace_id, user_id, status, created_at, completed_at, metadata_json
        FROM tasks
        WHERE workspace_id = 'eval_single_golden'
          AND json_extract(metadata_json, '$.golden_id') IS NOT NULL
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    for row in cur:
        print_row(row, ["id", "workspace_id", "user_id", "status", "created_at", "completed_at"])
        print(f"  metadata_json={row['metadata_json']}")
        print()

def list_golden_traces(conn: sqlite3.Connection, limit: int):
    cur = conn.execute(
        """
        SELECT task_id, workspace_id, status, runtime_mode, task_type,
               score_final, duration_ms, cost_estimate_usd, trace_id
        FROM task_traces
        WHERE workspace_id = 'eval_single_golden'
        ORDER BY started_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    for row in cur:
        parts = [
            f"task_id={row['task_id']}",
            f"status={row['status']}",
            f"runtime_mode={row['runtime_mode']}",
            f"task_type={row['task_type']}",
            f"score_final={row['score_final']}",
            f"duration_ms={_fmt_ms(row['duration_ms'])}",
            f"cost_estimate_usd={_fmt_cost(row['cost_estimate_usd'])}",
            f"trace_id={row['trace_id']}",
        ]
        print(" | ".join(parts))

def show_by_golden_id(conn: sqlite3.Connection, golden_id: str):
    cur = conn.execute(
        """
        SELECT id, workspace_id, user_id, status, created_at, completed_at, metadata_json
        FROM tasks
        WHERE workspace_id = 'eval_single_golden'
          AND json_extract(metadata_json, '$.golden_id') = ?
        ORDER BY created_at DESC
        """,
        (golden_id,),
    )
    tasks = cur.fetchall()
    if not tasks:
        print(f"No tasks found for golden_id={golden_id}")
        return
    for row in tasks:
        print_row(row, ["id", "status", "created_at", "completed_at"])
        print(f"  metadata_json={row['metadata_json']}")
        print()
        tcur = conn.execute(
            """
            SELECT task_id, status, runtime_mode, task_type,
                   score_final, duration_ms, cost_estimate_usd, trace_id
            FROM task_traces
            WHERE task_id = ?
            """,
            (row["id"],),
        )
        trace = tcur.fetchone()
        if trace:
            print("  trace:")
            print("    " + " | ".join([
                f"status={trace['status']}",
                f"runtime_mode={trace['runtime_mode']}",
                f"task_type={trace['task_type']}",
                f"score_final={trace['score_final']}",
                f"duration_ms={_fmt_ms(trace['duration_ms'])}",
                f"cost_estimate_usd={_fmt_cost(trace['cost_estimate_usd'])}",
                f"trace_id={trace['trace_id']}",
            ]))
        print()

def show_by_trace_id(conn: sqlite3.Connection, trace_id: str):
    tcur = conn.execute(
        """
        SELECT task_id, workspace_id, status, runtime_mode, task_type,
               score_final, duration_ms, cost_estimate_usd, trace_id
        FROM task_traces
        WHERE trace_id = ?
        """,
        (trace_id,),
    )
    trace = tcur.fetchone()
    if not trace:
        print(f"No trace found for trace_id={trace_id}")
        return
    print("trace_traces row:")
    parts = [
        f"task_id={trace['task_id']}",
        f"workspace_id={trace['workspace_id']}",
        f"status={trace['status']}",
        f"runtime_mode={trace['runtime_mode']}",
        f"task_type={trace['task_type']}",
        f"score_final={trace['score_final']}",
        f"duration_ms={_fmt_ms(trace['duration_ms'])}",
        f"cost_estimate_usd={_fmt_cost(trace['cost_estimate_usd'])}",
        f"trace_id={trace['trace_id']}",
    ]
    print(" | ".join(parts))
    print()

    cur = conn.execute(
        """
        SELECT id, workspace_id, user_id, status, created_at, completed_at, metadata_json
        FROM tasks
        WHERE id = ?
        """,
        (trace["task_id"],),
    )
    task = cur.fetchone()
    if task:
        print("tasks row:")
        print_row(task, ["id", "workspace_id", "user_id", "status", "created_at", "completed_at"])
        print(f"  metadata_json={task['metadata_json']}")

def main():
    parser = argparse.ArgumentParser(description="Inspect golden eval traces in episodes.db")
    parser.add_argument(
        "mode",
        choices=["tasks", "traces", "golden", "trace"],
        help="tasks=recent golden tasks, traces=recent golden traces, "
             "golden=details by golden_id, trace=details by trace_id",
    )
    parser.add_argument("--limit", type=int, default=10, help="Max rows for tasks/traces listing")
    parser.add_argument("--golden-id", type=str, help="Golden ID (for mode=golden)")
    parser.add_argument("--trace-id", type=str, help="Trace ID (for mode=trace)")
    args = parser.parse_args()

    conn = connect(DB_PATH)
    try:
        if args.mode == "tasks":
            list_golden_tasks(conn, args.limit)
        elif args.mode == "traces":
            list_golden_traces(conn, args.limit)
        elif args.mode == "golden":
            if not args.golden_id:
                raise SystemExit("--golden-id is required for mode=golden")
            show_by_golden_id(conn, args.golden_id)
        elif args.mode == "trace":
            if not args.trace_id:
                raise SystemExit("--trace-id is required for mode=trace")
            show_by_trace_id(conn, args.trace_id)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
