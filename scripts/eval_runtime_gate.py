#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from io import StringIO
from pathlib import Path


def run_eval_summary() -> str:
    proc = subprocess.run(
        [sys.executable, "scripts/eval_runtime_summary.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(proc.returncode)
    print(proc.stdout)
    return proc.stdout


def parse_summary(output: str) -> dict:
    data = {
        "total_workflows": 0,
        "avg_quality_score": None,
        "human_override_count": 0,
        "policy_violation_count": 0,
    }
    buf = StringIO(output)
    for line in buf:
        line = line.strip()
        if not line or ":" not in line:
            continue
        if line.startswith("total_workflows:"):
            data["total_workflows"] = int(line.split(":", 1)[1].strip())
        elif line.startswith("avg_quality_score:"):
            value = line.split(":", 1)[1].strip()
            if value != "n/a":
                data["avg_quality_score"] = float(value)
        elif line.startswith("human_override_count:"):
            data["human_override_count"] = int(line.split(":", 1)[1].strip())
        elif line.startswith("policy_violation_count:"):
            data["policy_violation_count"] = int(line.split(":", 1)[1].strip())
    return data


def main() -> None:
    output = run_eval_summary()
    summary = parse_summary(output)

    total = summary["total_workflows"]
    avg_quality = summary["avg_quality_score"]
    human_override_count = summary["human_override_count"]
    policy_violation_count = summary["policy_violation_count"]

    print("\n=== Eval Runtime Gate ===")
    print(f"total_workflows={total}")
    print(f"avg_quality_score={avg_quality}")
    print(f"human_override_count={human_override_count}")
    print(f"policy_violation_count={policy_violation_count}")

    if total == 0:
        print("[EVAL_GATE] FAIL: no eval workflows found")
        raise SystemExit(1)

    if policy_violation_count > 0:
        print("[EVAL_GATE] FAIL: policy violations present")
        raise SystemExit(1)

    if avg_quality is None or avg_quality < 0.7:
        print("[EVAL_GATE] FAIL: avg_quality_score below threshold (0.7)")
        raise SystemExit(1)

    print("[EVAL_GATE] PASS: eval runtime quality within thresholds")


if __name__ == "__main__":
    main()