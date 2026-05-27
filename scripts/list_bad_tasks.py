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
        description="List suspicious/bad tasks from episodes.db"
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
        help="Max tasks to show",
    )
    parser.add_argument(
        "--workspace",
        help="Filter by workspace_id prefix",
    )
    parser.add_argument(
        "--user",
        help="Filter by user_id",
    )
    parser.add_argument(
        "--governance-only",
        action="store_true",
        help="Only tasks with governance/policy refusals",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Show full assistant content (not truncated)",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 1

    conn = connect(db_path)

    # Базовый фильтр по workspace/user, если заданы
    where_clauses = []
    params: list[Any] = []

    if args.workspace:
        where_clauses.append("workspace_id LIKE ?")
        params.append(f"{args.workspace}%")

    if args.user:
        where_clauses.append("user_id = ?")
        params.append(args.user)

    where_sql = " AND ".join(where_clauses)
    if where_sql:
        where_sql = "WHERE " + where_sql

    # Подготовим CTE с эпизодами + task_id/trace_id, чтобы было проще группировать
    # json_extract(metadata_json, '$.task_id') – стандартный способ вытащить значение из JSON. [web:421][web:469]
    sql = f"""
        WITH episodes_with_ids AS (
            SELECT
                id,
                ts,
                user_id,
                workspace_id,
                role,
                content,
                metadata_json,
                json_extract(metadata_json, '$.task_id') AS task_id,
                json_extract(metadata_json, '$.trace_id') AS trace_id
            FROM episodes
            {where_sql}
        ),
        bad_episodes AS (
            SELECT *
            FROM episodes_with_ids
            WHERE
                role = 'assistant'
                AND task_id IS NOT NULL
                AND (
                    -- governance / policy style
                    LOWER(content) LIKE '%governance%'
                    OR LOWER(content) LIKE '%policy%'
                    OR LOWER(content) LIKE '%safety%'
                    OR LOWER(content) LIKE '%not allowed%'
                    OR LOWER(content) LIKE '%refuse%'
                    OR LOWER(content) LIKE '%refusal%'
                    OR LOWER(content) LIKE '%cannot comply%'
                    OR LOWER(content) LIKE '%blocked%'
                    OR LOWER(content) LIKE '%violat%'  -- violation / violate / etc.
                    -- orchestrator SKIP / routing artefacts
                    OR content LIKE 'SKIP:%'
                    -- generic error-ish markers
                    OR LOWER(content) LIKE '%exception%'
                    OR LOWER(content) LIKE '%traceback%'
                    OR LOWER(content) LIKE '%error%'
                    OR LOWER(content) LIKE '%failed%'
                    OR LOWER(content) LIKE '%failure%'
                )
        )
        SELECT
            task_id,
            trace_id,
            MIN(ts) AS first_ts,
            MAX(ts) AS last_ts,
            COUNT(*) AS assistant_episodes,
            GROUP_CONCAT(id) AS assistant_episode_ids
        FROM bad_episodes
        GROUP BY task_id, trace_id
        ORDER BY last_ts DESC, task_id DESC
        LIMIT ?
    """
    all_params = list(params)
    all_params.append(args.limit)

    bad_tasks = conn.execute(sql, all_params).fetchall()

    if not bad_tasks:
        print("No suspicious tasks found")
        return 0

    print(f"Suspicious tasks shown: {len(bad_tasks)}\n")

    # Для каждого плохого таска вытащим полный контекст (user+assistant) и распечатаем
    for trow in bad_tasks:
        task_id = trow["task_id"]
        trace_id = trow["trace_id"]
        print(
            f"- task_id={task_id} trace_id={trace_id} "
            f"first_ts={trow['first_ts']} last_ts={trow['last_ts']} "
            f"assistant_episodes={trow['assistant_episodes']}"
        )

        # Вторая выборка: все эпизоды по этому task_id (и trace_id, если есть)
        where_task = ["json_extract(metadata_json, '$.task_id') = ?"]
        ep_params: list[Any] = [task_id]

        if trace_id is not None:
            where_task.append("json_extract(metadata_json, '$.trace_id') = ?")
            ep_params.append(trace_id)

        if args.workspace:
            where_task.append("workspace_id LIKE ?")
            ep_params.append(f"{args.workspace}%")

        if args.user:
            where_task.append("user_id = ?")
            ep_params.append(args.user)

        where_task_sql = " AND ".join(where_task)

        ep_sql = f"""
            SELECT
                id,
                ts,
                user_id,
                workspace_id,
                role,
                content,
                metadata_json
            FROM episodes
            WHERE {where_task_sql}
            ORDER BY id ASC
        """
        episodes = conn.execute(ep_sql, ep_params).fetchall()

        # При governance-only – ещё раз фильтруем на уровне вывода (без выкидывания таска)
        for row in episodes:
            if args.governance_only and row["role"] == "assistant":
                lc = (row["content"] or "").lower()
                if not any(
                    key in lc
                    for key in (
                        "governance",
                        "policy",
                        "safety",
                        "not allowed",
                        "refuse",
                        "refusal",
                        "cannot comply",
                        "blocked",
                        "violat",
                    )
                ):
                    # это не governance-эпизод – скипаем строку, но сам task остаётся
                    continue

            print(
                f"  [id={row['id']}] ts={row['ts']} "
                f"user_id={row['user_id']} workspace={row['workspace_id'] or '-'} "
                f"role={row['role']}"
            )
            content = row["content"] if args.full else shorten(row["content"])
            print(f"  content: {content}")
            print(f"  metadata: {shorten_json(row['metadata_json'])}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
