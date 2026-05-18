import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "output" / "eval_runs"


def load_run_files():
    if not RUNS_DIR.exists():
        print(f"[EVAL] No eval_runs directory at {RUNS_DIR}, nothing to summarize.")
        return []
    files = sorted(RUNS_DIR.glob("*.json"))
    if not files:
        print(f"[EVAL] No eval run artifacts found in {RUNS_DIR}.")
    return files


def summarize_run(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    golden_id = data.get("golden_id", path.stem)
    workflow_type = data.get("workflow_type", "unknown")
    autonomy_tier = data.get("autonomy_tier", "unknown")

    eval_record = data.get("evaluation_record", {}) or {}
    task_success = eval_record.get("task_success", "unknown")
    human_override = eval_record.get("human_override", "unknown")
    policy_violation = bool(eval_record.get("policy_violation", False))
    quality_score = eval_record.get("quality_score", 0.0)

    return {
        "file": path,
        "golden_id": golden_id,
        "workflow_type": workflow_type,
        "autonomy_tier": autonomy_tier,
        "task_success": task_success,
        "human_override": human_override,
        "policy_violation": policy_violation,
        "quality_score": quality_score,
    }


def main():
    files = load_run_files()
    if not files:
        print("[EVAL] No eval artifacts to summarize. Failing by default.")
        sys.exit(1)

    summaries = [summarize_run(p) for p in files]

    print("=== Eval Smoke Summary ===")
    failures = []
    for s in summaries:
        print(
            f"- {s['golden_id']} "
            f"(workflow={s['workflow_type']}, tier={s['autonomy_tier']}): "
            f"task_success={s['task_success']}, "
            f"human_override={s['human_override']}, "
            f"policy_violation={s['policy_violation']}, "
            f"quality_score={s['quality_score']:.3f}"
        )

        # Простые правила v1:
        # 1) task_success должен быть "success"
        # 2) policy_violation == False
        # 3) quality_score >= 0.7 (порог можно потом вынести в конфиг)
        if s["task_success"] != "success":
            failures.append((s, "task_success != success"))
        if s["policy_violation"]:
            failures.append((s, "policy_violation == True"))
        if s["quality_score"] < 0.7:
            failures.append((s, "quality_score < 0.7"))

    if not failures:
        print("\n[EVAL] All smoke tests passed ✅")
        sys.exit(0)

    print("\n[EVAL] Smoke failures detected ❌")
    for s, reason in failures:
        print(
            f"  - {s['golden_id']} "
            f"(workflow={s['workflow_type']}, tier={s['autonomy_tier']}): {reason}"
        )

    # Жёстко падаем, чтобы это можно было использовать как gate
    sys.exit(1)


if __name__ == "__main__":
    main()
