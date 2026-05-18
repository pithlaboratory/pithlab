import json
import sys
from pathlib import Path

import yaml
from jsonschema import validate


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "eval" / "golden" / "golden_workflow_schema.json"
OUTPUT_DIR = ROOT / "output" / "eval_runs"


def load_schema() -> dict:
    with SCHEMA_PATH.open() as f:
        return json.load(f)


def load_golden(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def validate_golden(schema: dict, data: dict) -> None:
    validate(instance=data, schema=schema)


def clean_multiline_text(value):
    if not isinstance(value, str):
        return value
    return value.strip().strip('"').replace("\\n", "\n").strip()


def build_payload(golden: dict) -> dict:
    entry = golden["entrypoint"]
    inputs = golden["inputs"]

    initial_context = []
    for item in inputs.get("initial_context", []):
        initial_context.append({
            "type": item["type"],
            "role": item["role"],
            "content": clean_multiline_text(item["content"]),
        })

    payload = {
        "trace_id": "TRACE_PLACEHOLDER",
        "task_id": "TASK_PLACEHOLDER",
        "workspace_id": "WORKSPACE_PLACEHOLDER",
        "runtime_mode": entry["runtime_mode"],
        "task_type": entry["task_type"],
        "user_query": clean_multiline_text(inputs["user_query"]),
        "initial_context": initial_context,
    }

    if "route" in entry:
        payload["route"] = entry["route"]

    return payload


def fake_evaluation_record(golden: dict) -> dict:
    expected = golden["expected_eval_outcome"]

    return {
        "trace_id": "TRACE_PLACEHOLDER",
        "task_id": "TASK_PLACEHOLDER",
        "workspace_id": "WORKSPACE_PLACEHOLDER",
        "workflow_type": golden["workflow_type"],
        "task_type": golden["entrypoint"]["task_type"],
        "task_success": expected["task_success"],
        "human_override": expected["human_override"],
        "quality_score": expected.get("min_quality_score", 0.0),
        "cost_per_workflow": 0.0,
        "policy_violation": expected.get("policy_violation", False),
        "failure_class": None,
        "eval_source": "stub",
        "eval_version": golden["rubric"]["rubric_version"],
    }


def save_run_artifacts(golden: dict, payload: dict, eval_record: dict, output_path: Path) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    run_artifact = {
        "golden_id": golden["golden_id"],
        "department": golden["department"],
        "workflow_type": golden["workflow_type"],
        "autonomy_tier": golden["autonomy_tier"],
        "payload": payload,
        "evaluation_record": eval_record,
    }
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(run_artifact, f, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/run_golden.py <path-to-golden-yaml>")
        sys.exit(1)

    golden_path = Path(sys.argv[1]).resolve()
    if not golden_path.exists():
        print(f"Golden file not found: {golden_path}")
        sys.exit(2)

    schema = load_schema()
    golden = load_golden(golden_path)
    validate_golden(schema, golden)

    print(f"Golden workflow loaded and validated: {golden_path}")

    payload = build_payload(golden)
    print("\n=== Runtime payload (stub) ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    eval_record = fake_evaluation_record(golden)
    print("\n=== EvaluationRecord v1 (stub) ===")
    print(json.dumps(eval_record, ensure_ascii=False, indent=2))

    # save artifacts
    output_file = OUTPUT_DIR / f"{golden['golden_id']}.json"
    save_run_artifacts(golden, payload, eval_record, output_file)
    print(f"\nArtifacts written to: {output_file}")


if __name__ == "__main__":
    main()
