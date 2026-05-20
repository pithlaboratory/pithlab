#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


EVAL_DIR = Path("output/eval_runs")


def normalize_record(payload: Dict[str, Any], source_file: str) -> Dict[str, Any]:
    eval_record = payload.get("evaluation_record")
    if isinstance(eval_record, dict):
        merged = dict(eval_record)
        merged.setdefault("workflow_type", payload.get("workflow_type"))
        merged.setdefault("autonomy_tier", payload.get("autonomy_tier"))
        merged.setdefault("department", payload.get("department"))
        merged.setdefault("golden_id", payload.get("golden_id"))
        merged["_source_file"] = source_file
        return merged

    payload = dict(payload)
    payload["_source_file"] = source_file
    return payload


def load_eval_records(eval_dir: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not eval_dir.exists():
        return records

    for path in sorted(eval_dir.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, dict):
                records.append(normalize_record(payload, str(path)))
        except Exception:
            continue

    return records


def avg(values: List[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def print_counter(title: str, counter: Counter) -> None:
    print(title)
    if not counter:
        print("  (none)")
        return
    for key, value in counter.most_common():
        print(f"  - {key}: {value}")


def main() -> None:
    records = load_eval_records(EVAL_DIR)

    print("=== Eval Runtime Summary ===")
    if not records:
        print("(no eval records found)")
        return

    quality_scores = []
    for r in records:
        value = r.get("quality_score")
        if value is not None:
            try:
                quality_scores.append(float(value))
            except (TypeError, ValueError):
                pass

    human_override_count = sum(
        1 for r in records
        if (r.get("human_override") not in (None, "none"))
    )
    policy_violation_count = sum(
        1 for r in records
        if bool(r.get("policy_violation")) is True
    )

    workflow_counter = Counter(
        r.get("workflow_type", "unknown")
        for r in records
    )
    task_success_counter = Counter(
        r.get("task_success", "unknown")
        for r in records
    )

    governance_records = [
        r for r in records
        if str(r.get("workflow_type", "")).startswith("governance_")
    ]
    non_governance_records = [
        r for r in records
        if not str(r.get("workflow_type", "")).startswith("governance_")
    ]

    avg_quality = avg(quality_scores)
    human_override_rate = human_override_count / len(records)
    policy_violation_rate = policy_violation_count / len(records)

    print(f"total_workflows: {len(records)}")
    print(f"avg_quality_score: {avg_quality:.3f}" if avg_quality is not None else "avg_quality_score: n/a")
    print(f"human_override_count: {human_override_count}")
    print(f"human_override_rate: {human_override_rate:.3f}")
    print(f"policy_violation_count: {policy_violation_count}")
    print(f"policy_violation_rate: {policy_violation_rate:.3f}")
    print(f"governance_workflows: {len(governance_records)}")
    print(f"non_governance_workflows: {len(non_governance_records)}")

    print_counter("workflows_by_type:", workflow_counter)
    print_counter("workflows_by_task_success:", task_success_counter)


if __name__ == "__main__":
    main()