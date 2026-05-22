#!/usr/bin/env python3
"""
Inspect recent evaluation records (EvaluationRecord v1) from episodes.db.

Usage:
    python scripts/inspect_eval.py [-n LIMIT] [-w WORKSPACE_ID] [--trace TRACE_ID]
"""

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path("data/episodes.db")


def inspect_eval(
    limit: int = 10,
    workspace_id: str | None = None,
    trace_id: str | None = None,
) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()

        base_query = """
            SELECT
                e.id,
                e.user_id,
                e.workspace_id,
                e.ts,
                e.role,
                e.trace_id,
                CASE
                    WHEN e.metadata_json IS NOT NULL AND json_valid(e.metadata_json)
                    THEN json_extract(e.metadata_json, '$.eval.eval_version')
                    ELSE NULL
                END as eval_version,
                CASE
                    WHEN e.metadata_json IS NOT NULL AND json_valid(e.metadata_json)
                    THEN json_extract(e.metadata_json, '$.eval.task_success')
                    ELSE NULL
                END as task_success,
                CASE
                    WHEN e.metadata_json IS NOT NULL AND json_valid(e.metadata_json)
                    THEN json_extract(e.metadata_json, '$.eval.human_override')
                    ELSE NULL
                END as human_override,
                CASE
                    WHEN e.metadata_json IS NOT NULL AND json_valid(e.metadata_json)
                    THEN json_extract(e.metadata_json, '$.eval.quality_score')
                    ELSE NULL
                END as quality_score,
                CASE
                    WHEN e.metadata_json IS NOT NULL AND json_valid(e.metadata_json)
                    THEN json_extract(e.metadata_json, '$.eval.eval_source')
                    ELSE NULL
                END as eval_source,
                CASE
                    WHEN e.metadata_json IS NOT NULL AND json_valid(e.metadata_json)
                    THEN json_extract(e.metadata_json, '$.eval.workflow_type')
                    ELSE NULL
                END as workflow_type,
                CASE
                    WHEN e.metadata_json IS NOT NULL AND json_valid(e.metadata_json)
                    THEN json_extract(e.metadata_json, '$.eval.runtime_mode')
                    ELSE NULL
                END as runtime_mode,
                CASE
                    WHEN e.metadata_json IS NOT NULL AND json_valid(e.metadata_json)
                    THEN json_extract(e.metadata_json, '$.eval.failure_class')
                    ELSE NULL
                END as failure_class,
                CASE
                    WHEN e.metadata_json IS NOT NULL AND json_valid(e.metadata_json)
                    THEN json_extract(e.metadata_json, '$.eval.policy_violation')
                    ELSE NULL
                END as policy_violation,
                CASE
                    WHEN e.metadata_json IS NOT NULL AND json_valid(e.metadata_json)
                    THEN json_extract(e.metadata_json, '$.eval.cost_per_workflow')
                    ELSE NULL
                END as cost_per_workflow,
                CASE
                    WHEN e.metadata_json IS NOT NULL AND json_valid(e.metadata_json)
                    THEN json_extract(e.metadata_json, '$.eval.cost')
                    ELSE NULL
                END as total_cost,
                CASE
                    WHEN e.metadata_json IS NOT NULL AND json_valid(e.metadata_json)
                    THEN json_extract(e.metadata_json, '$.eval.tokens')
                    ELSE NULL
                END as tokens
            FROM episodes e
            WHERE e.role = 'assistant'
        """

        params: list[object] = []

        if workspace_id:
            base_query += " AND e.workspace_id = ?"
            params.append(workspace_id)

        if trace_id:
            base_query += " AND e.trace_id = ?"
            params.append(trace_id)

        base_query += " ORDER BY datetime(e.ts) DESC LIMIT ?"
        params.append(limit)

        cur.execute(base_query, params)
        rows = cur.fetchall()

    if not rows:
        print("No assistant episodes with eval found (or no rows matched filters).")
        return

    for row in rows:
        (
            episode_id,
            user_id,
            ws_id,
            ts,
            role,
            ep_trace_id,
            eval_version,
            task_success,
            human_override,
            quality_score,
            eval_source,
            workflow_type,
            runtime_mode,
            failure_class,
            policy_violation,
            cost_per_workflow,
            total_cost,
            tokens,
        ) = row

        print("-" * 60)
        print(f"episode_id     : {episode_id}")
        print(f"user_id        : {user_id}")
        print(f"workspace_id   : {ws_id}")
        print(f"ts             : {ts}")
        print(f"role           : {role}")
        print(f"trace_id       : {ep_trace_id}")
        print(f"eval_version   : {eval_version}")
        print(f"task_success   : {task_success}")
        print(f"human_override : {human_override}")
        print(f"quality_score  : {quality_score}")
        print(f"eval_source    : {eval_source}")
        print(f"workflow_type  : {workflow_type}")
        print(f"runtime_mode   : {runtime_mode}")
        print(f"failure_class  : {failure_class}")
        print(f"policy_violate : {policy_violation}")
        print(f"cost_per_wflow : {cost_per_workflow}")
        print(f"total_cost     : {total_cost}")
        print(f"tokens         : {tokens}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect recent evaluation records from episodes.db"
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=10,
        help="Number of assistant episodes to show (default: 10)",
    )
    parser.add_argument(
        "-w",
        "--workspace",
        type=str,
        default=None,
        help="Filter by workspace_id",
    )
    parser.add_argument(
        "--trace",
        type=str,
        default=None,
        help="Filter by trace_id",
    )
    args = parser.parse_args()

    inspect_eval(
        limit=args.limit,
        workspace_id=args.workspace,
        trace_id=args.trace,
    )


if __name__ == "__main__":
    main()
