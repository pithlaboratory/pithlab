import json
from pathlib import Path

import yaml
from jsonschema import validate


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "eval" / "golden" / "golden_workflow_schema.json"
GOLDEN_PATH = ROOT / "eval" / "golden" / "research_competitor_brief_v1.yaml"


def load_and_validate():
    with SCHEMA_PATH.open() as f:
        schema = json.load(f)
    with GOLDEN_PATH.open() as f:
        data = yaml.safe_load(f)
    validate(instance=data, schema=schema)
    return data


def clean_multiline_text(value: str) -> str:
    if not isinstance(value, str):
        return value
    return value.strip().strip('"').replace("\\n", "\n").strip()


def build_payload(golden: dict) -> dict:
    entry = golden["entrypoint"]
    inputs = golden["inputs"]

    trace_id = "TRACE_PLACEHOLDER"
    task_id = "TASK_PLACEHOLDER"
    workspace_id = "WORKSPACE_PLACEHOLDER"

    initial_context = []
    for item in inputs.get("initial_context", []):
        initial_context.append({
            "type": item["type"],
            "role": item["role"],
            "content": clean_multiline_text(item["content"]),
        })

    payload = {
        "trace_id": trace_id,
        "task_id": task_id,
        "workspace_id": workspace_id,
        "runtime_mode": entry["runtime_mode"],
        "task_type": entry["task_type"],
        "user_query": clean_multiline_text(inputs["user_query"]),
        "initial_context": initial_context,
    }
    return payload


def fake_evaluation_record(golden: dict) -> dict:
    expected = golden["expected_eval_outcome"]
    record = {
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
    return record


def main():
    golden = load_and_validate()
    print("Golden workflow loaded and validated.")

    payload = build_payload(golden)
    print("\n=== Runtime payload (stub) ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    eval_record = fake_evaluation_record(golden)
    print("\n=== EvaluationRecord v1 (stub) ===")
    print(json.dumps(eval_record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
