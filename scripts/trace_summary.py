#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


TRACE_DIR = Path("output/traces")


def parse_ts(value: Optional[str]) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return datetime.min


def first_non_null(values: List[Any]) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def load_trace_events(trace_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if not trace_dir.exists():
        return grouped

    for path in sorted(trace_dir.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                raw = event.get("raw") or {}
                trace_id = raw.get("trace_id") or "no-trace-id"
                grouped[trace_id].append(event)

    return grouped


def build_summary(trace_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    events = sorted(events, key=lambda e: parse_ts(e.get("timestamp")))
    last_event = events[-1] if events else {}
    workspace_id = first_non_null([e.get("workspace_id") for e in events])
    task_id = first_non_null([e.get("task_id") for e in events])

    raw_blobs = [(e.get("raw") or {}) for e in events]

    workflow_type = first_non_null([raw.get("workflow_type") for raw in raw_blobs])
    task_type = first_non_null([raw.get("task_type") for raw in raw_blobs])
    autonomy_tier = first_non_null([raw.get("autonomy_tier") for raw in raw_blobs])
    policy_violation = first_non_null([raw.get("policy_violation") for raw in raw_blobs])
    quality_score = first_non_null([raw.get("quality_score") for raw in raw_blobs])
    cost_usd = first_non_null([raw.get("cost_usd") for raw in reversed(raw_blobs)])
    if cost_usd is None:
        cost_usd = first_non_null([raw.get("cost") for raw in reversed(raw_blobs)])

    event_types = [e.get("event_type") for e in events if e.get("event_type")]

    return {
        "trace_id": trace_id,
        "workspace_id": workspace_id,
        "task_id": task_id,
        "event_count": len(events),
        "event_types": event_types,
        "workflow_type": workflow_type,
        "task_type": task_type,
        "autonomy_tier": autonomy_tier,
        "policy_violation": policy_violation,
        "quality_score": quality_score,
        "cost_usd": cost_usd,
        "final_event_type": last_event.get("event_type"),
        "last_timestamp": last_event.get("timestamp"),
    }


def print_summary(summaries: List[Dict[str, Any]]) -> None:
    print("=== Trace Summary ===")
    if not summaries:
        print("(no trace events found)")
        return

    for item in summaries:
        print(
            f"- trace_id={item['trace_id']} | "
            f"task_id={item['task_id']} | "
            f"ws={item['workspace_id']} | "
            f"events={item['event_count']} | "
            f"final={item['final_event_type']} | "
            f"workflow={item['workflow_type']} | "
            f"task_type={item['task_type']} | "
            f"tier={item['autonomy_tier']} | "
            f"policy_violation={item['policy_violation']} | "
            f"quality_score={item['quality_score']} | "
            f"cost_usd={item['cost_usd']}"
        )


def main() -> None:
    grouped = load_trace_events(TRACE_DIR)
    summaries = [
        build_summary(trace_id, events)
        for trace_id, events in grouped.items()
    ]
    summaries.sort(key=lambda x: parse_ts(x.get("last_timestamp")), reverse=True)
    print_summary(summaries)


if __name__ == "__main__":
    main()