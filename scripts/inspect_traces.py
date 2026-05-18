#!/usr/bin/env python3

import argparse
import json
import sqlite3
from pathlib import Path

DB_PATH = Path("data/episodes.db")


def inspect_traces(limit: int = 10, workspace_id: str | None = None) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    base_query = """
        SELECT
            t.id,
            t.workspace_id,
            t.status,
            t.created_at,
            t.completed_at,
            json_extract(t.metadata_json, '$.trace_id') as meta_trace_id,
            tt.status as trace_status,
            tt.trace_id as trace_trace_id,
            tt.cost_estimate_usd,
            tt.started_at,
            tt.finished_at,
            tt.duration_ms
        FROM tasks t
        LEFT JOIN task_traces tt ON tt.task_id = t.id
    """

    params: list[object] = []
    where_clauses: list[str] = []

    if workspace_id:
        where_clauses.append("t.workspace_id = ?")
        params.append(workspace_id)

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    base_query += " ORDER BY datetime(t.created_at) DESC LIMIT ?"
    params.append(limit)

    cur.execute(base_query, params)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No tasks found")
        return

    for row in rows:
        (
            task_id,
            ws_id,
            status,
            created_at,
            completed_at,
            meta_trace_id,
            trace_status,
            trace_trace_id,
            cost_estimate_usd,
            started_at,
            finished_at,
            duration_ms,
        ) = row

        print("-" * 60)
        print(f"task_id       : {task_id}")
        print(f"workspace_id  : {ws_id}")
        print(f"task.status   : {status}")
        print(f"trace.status  : {trace_status}")
        print(f"meta.trace_id : {meta_trace_id}")
        print(f"trace.trace_id: {trace_trace_id}")
        print(f"cost_usd      : {cost_estimate_usd}")
        print(f"created_at    : {created_at}")
        print(f"completed_at  : {completed_at}")
        print(f"started_at    : {started_at}")
        print(f"finished_at   : {finished_at}")
        print(f"duration_ms   : {duration_ms}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect recent tasks and traces from episodes.db"
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=10,
        help="Number of tasks to show (default: 10)",
    )
    parser.add_argument(
        "-w",
        "--workspace",
        type=str,
        default=None,
        help="Filter by workspace_id",
    )
    args = parser.parse_args()

    inspect_traces(limit=args.limit, workspace_id=args.workspace)


if __name__ == "__main__":
    main()