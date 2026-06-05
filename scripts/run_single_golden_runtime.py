"""
Pith v5 — Run a single golden workflow through the real runtime.

Usage:
    python scripts/run_single_golden_runtime.py eval/golden/support_ops_faq_v1.yaml

What it does:
1. Loads & validates a golden YAML workflow.
2. Calls the real LLM through core.cognition.router (no stubs).
3. Runs core.evolution.evaluator.Evaluator.evaluate_response() for real eval.
4. Writes a full EvaluationRecord v1 JSON (compatible with eval_smoke_summary.py).
5. Prints a summary to stdout.

Dependencies:
    - OPENROUTER_KEY in .env (validated at startup)
    - All core modules importable

Known limitations (Phase 1):
    - Does NOT use RuntimePlanner (which lacks TaskService/TraceStore/Evaluator integration).
    - Calls router.call() directly — Planner integration will replace this in Phase 2.
    - initial_context is passed as part of system_prompt, not via Memory.
    - trace_id and task_id are generated locally (UUID), not by TaskService.
    - workspace_id is a fixed constant ("eval_single_golden").
    - EvaluationRecord gets trace_id and workspace_id from the caller.
"""
import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from jsonschema import validate

# ── Ensure project root is on sys.path (for core.* imports) ────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Load .env before any core imports ──────────────────────────────────────
load_dotenv(PROJECT_ROOT / ".env")

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = PROJECT_ROOT
SCHEMA_PATH = ROOT / "eval" / "golden" / "golden_workflow_schema.json"
OUTPUT_DIR = ROOT / "output" / "eval_runs"

# ── Logger ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("run_single_golden_runtime")


# ── Helpers ────────────────────────────────────────────────────────────────

def load_schema() -> dict:
    with SCHEMA_PATH.open() as f:
        return json.load(f)


def load_golden(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def clean_multiline_text(value: Any) -> str:
    """Normalise multi-line YAML strings: strip, unescape newlines, strip again."""
    if not isinstance(value, str):
        return str(value) if value is not None else ""
    return value.strip().strip('"').replace("\\n", "\n").strip()


def build_system_prompt_from_context(golden: dict) -> str:
    """
    Build a system prompt from golden initial_context entries.
    Each entry adds a typed context block (note, constraint, etc.).
    """
    inputs = golden.get("inputs", {})
    items = inputs.get("initial_context", [])
    if not items:
        return ""

    blocks: list[str] = []
    for item in items:
        role = item.get("role", "system")
        content = clean_multiline_text(item.get("content", ""))
        if content:
            blocks.append(f"[{role.upper()}]\n{content}")

    return "\n\n".join(blocks)


def generate_eval_run_path(golden_id: str) -> Path:
    """Output path: output/eval_runs/<golden_id>.json (same as run_golden.py stub)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / f"{golden_id}.json"


# ── Core execution ─────────────────────────────────────────────────────────

def run_golden_through_runtime(golden: dict) -> Dict[str, Any]:
    """
    Execute a golden workflow through the real Pith runtime.
    Returns a dict ready to be written as output/eval_runs/<golden_id>.json.
    """
    # ── 1. Extract golden metadata ─────────────────────────────────────
    golden_id: str = golden["golden_id"]
    department: str = golden.get("department", "unknown")
    workflow_type: str = golden.get("workflow_type", "unknown")
    autonomy_tier: str = golden.get("autonomy_tier", "unknown")
    entrypoint: dict = golden.get("entrypoint", {})
    runtime_mode: str = entrypoint.get("runtime_mode", "normal")
    task_type: str = entrypoint.get("task_type", "general")
    expected_outcome: dict = golden.get("expected_eval_outcome", {})

    # ── 2. Extract inputs ──────────────────────────────────────────────
    inputs: dict = golden.get("inputs", {})
    user_query: str = clean_multiline_text(inputs.get("user_query", ""))
    context_prompt: str = build_system_prompt_from_context(golden)

    # ── 3. Generate correlation IDs ────────────────────────────────────
    task_id: str = f"eval_{golden_id}_{uuid.uuid4().hex[:8]}"
    trace_id: str = f"TRACE_{golden_id}_{uuid.uuid4().hex[:12]}"
    workspace_id: str = "eval_single_golden"

    # ── 4. Call the real LLM ───────────────────────────────────────────
    from core.cognition.router import call_llm

    logger.info("Calling LLM for golden '%s' (task_id=%s, trace_id=%s)", golden_id, task_id, trace_id)

    llm_result = call_llm(
        prompt=user_query,
        system_prompt=context_prompt,
        mode=runtime_mode.lower() if runtime_mode else None,
        workspace_id=workspace_id,
        agent="eval_golden",
        session_id=task_id,
        task_id=task_id,
    )

    response_text: str = llm_result.get("content", "")
    model_used: str = llm_result.get("model", "unknown")
    usage: dict = llm_result.get("usage", {}) or {}
    tokens_prompt: int = usage.get("prompt_tokens", 0)
    tokens_completion: int = usage.get("completion_tokens", 0)
    cost_usd: float = llm_result.get("cost_usd", 0.0)

    logger.info(
        "LLM response received: model=%s, tokens=%d/%d, cost=$%.6f",
        model_used, tokens_prompt, tokens_completion, cost_usd,
    )

    # ── 5. Build evaluation record ─────────────────────────────────────
    from core.evolution.evaluator import evaluator as eval_engine

    # Expected task_success from golden (for comparison, not for eval input)
    expected_task_success: str = expected_outcome.get("task_success", "success")

    # Run evaluator
    evaluation: dict = eval_engine.evaluate_response(
        task_id=task_id,
        user_id="golden_eval_runner",
        response=response_text,
        model=model_used,
        tokens=tokens_prompt + tokens_completion,
        cost=cost_usd,
        user_feedback=None,                 # no user feedback in automated eval
        context_used=context_prompt or None,
        task_type=task_type,
    )

    # Add trace_id and workspace_id (caller's responsibility per Evaluator docs)
    evaluation["trace_id"] = trace_id
    evaluation["workspace_id"] = workspace_id

    # Compare with expected outcome
    actual_task_success: str = evaluation.get("task_success", "failure")
    quality_score: float = evaluation.get("quality_score", 0.0)
    min_required_score: float = expected_outcome.get("min_quality_score", 0.0)

    passed: bool = (
        actual_task_success == expected_task_success
        and quality_score >= min_required_score
        and not evaluation.get("policy_violation", False)
    )

    # ── 6. Build output artifact ───────────────────────────────────────
    run_artifact: Dict[str, Any] = {
        "golden_id": golden_id,
        "department": department,
        "workflow_type": workflow_type,
        "autonomy_tier": autonomy_tier,
        "payload": {
            "trace_id": trace_id,
            "task_id": task_id,
            "workspace_id": workspace_id,
            "runtime_mode": runtime_mode,
            "task_type": task_type,
            "user_query": user_query,
            "initial_context_count": len(inputs.get("initial_context", [])),
        },
        "evaluation_record": evaluation,
        "_meta": {
            "script": "run_single_golden_runtime.py",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "passed": passed,
            "expected_task_success": expected_task_success,
            "min_required_score": min_required_score,
            "model_used": model_used,
            "cost_usd": cost_usd,
            "tokens_total": tokens_prompt + tokens_completion,
            "notes": "Phase 1: direct router.call() — not yet through RuntimePlanner",
        },
    }

    return run_artifact


# ── CLI ────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a single golden workflow through the real Pith runtime.",
        epilog=(
            "Example:\n"
            "  python scripts/run_single_golden_runtime.py eval/golden/support_ops_faq_v1.yaml\n"
            "  python scripts/run_single_golden_runtime.py --dry-run eval/golden/research_competitor_brief_v1.yaml\n"
            "  python scripts/run_single_golden_runtime.py --via-planner eval/golden/support_ops_faq_v1.yaml"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "golden_path",
        type=str,
        help="Path to a golden workflow YAML file (e.g. eval/golden/support_ops_faq_v1.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print payload without calling the LLM",
    )
    parser.add_argument(
        "--via-planner",
        action="store_true",
        help="Route through RuntimePlanner (creates TaskService record + Evaluator automatically)",
    )
    return parser.parse_args()


# ── Planner path ───────────────────────────────────────────────────────────

def run_through_planner(golden: dict) -> Dict[str, Any]:
    """
    Run golden through RuntimePlanner.
    Planner handles TaskService.create_task(), LLM call, Evaluator, and saving.
    """
    golden_id: str = golden["golden_id"]
    user_query: str = clean_multiline_text(golden.get("inputs", {}).get("user_query", ""))
    entrypoint: dict = golden.get("entrypoint", {})
    task_type: str = entrypoint.get("task_type", "general")
    expected_outcome: dict = golden.get("expected_eval_outcome", {})

    from core.runtime.planner import RuntimePlanner
    from core.entities.workspace import Workspace
    from core.memory.manager import MemoryManager
    from core.services.task_service import TaskService

    logger.info("=== Via Planner path ===")

    # Minimal dependencies for Planner
    memory_mgr = MemoryManager()
    planner = RuntimePlanner(
        memory_manager=memory_mgr,
        system_prompt="You are a helpful Support/Ops assistant for Pith.",
        task_service=TaskService(),
    )

    trace_id = f"TRACE_{golden_id}_{uuid.uuid4().hex[:12]}"
    workspace_id = "eval_single_golden"

    import asyncio
    result = asyncio.run(planner.plan_and_answer(
        user_id="golden_eval_runner",
        text=user_query,
        workspace_id=workspace_id,
        trace_id=trace_id,
        workflow=golden.get("workflow_type"),
        golden_id=golden_id,
        runtime_mode="eval",
        task_type="golden_runtime",
    ))

    planner_task_id = result.get("task_id", "unknown")
    planner_trace_id = result.get("trace_id", trace_id)
    evaluation = result.get("evaluation")

    if evaluation is None:
        logger.warning(
            "Planner returned no evaluation for golden '%s' — falling back to direct Evaluator call",
            golden_id,
        )
        from core.evolution.evaluator import evaluator as eval_engine
        evaluation = eval_engine.evaluate_response(
            task_id=planner_task_id,
            user_id="golden_eval_runner",
            response=result.get("response", ""),
            model=result.get("model_id", "unknown"),
            tokens=result.get("tokens_prompt", 0) + result.get("tokens_completion", 0),
            cost=result.get("cost", 0.0),
            user_feedback=None,
            context_used=result.get("context_used"),
            task_type=task_type,
        )
        evaluation["trace_id"] = planner_trace_id
        evaluation["workspace_id"] = workspace_id

    # Compare with expected outcome
    expected_task_success: str = expected_outcome.get("task_success", "success")
    min_required_score: float = expected_outcome.get("min_quality_score", 0.0)
    actual_success: str = evaluation.get("task_success", "failure")
    quality_score: float = evaluation.get("quality_score", 0.0)
    passed: bool = (
        actual_success == expected_task_success
        and quality_score >= min_required_score
        and not evaluation.get("policy_violation", False)
    )

    run_artifact: Dict[str, Any] = {
        "golden_id": golden_id,
        "department": golden.get("department", "unknown"),
        "workflow_type": golden.get("workflow_type", "unknown"),
        "autonomy_tier": golden.get("autonomy_tier", "unknown"),
        "payload": {
            "trace_id": planner_trace_id,
            "task_id": planner_task_id,
            "workspace_id": workspace_id,
            "runtime_mode": entrypoint.get("runtime_mode", "normal"),
            "task_type": task_type,
            "user_query": user_query,
            "initial_context_count": len(golden.get("inputs", {}).get("initial_context", [])),
        },
        "evaluation_record": evaluation,
        "_meta": {
            "script": "run_single_golden_runtime.py",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "passed": passed,
            "expected_task_success": expected_task_success,
            "min_required_score": min_required_score,
            "model_used": result.get("model_id", "unknown"),
            "cost_usd": result.get("cost", 0.0),
            "tokens_total": result.get("tokens_prompt", 0) + result.get("tokens_completion", 0),
            "notes": "Phase 2: via RuntimePlanner (TaskService + Evaluator integrated)",
        },
    }

    return run_artifact


def main() -> None:
    args = parse_args()

    # ── Resolve path ───────────────────────────────────────────────────
    golden_path = Path(args.golden_path)
    if not golden_path.is_absolute():
        golden_path = ROOT / golden_path
    if not golden_path.exists():
        logger.error("Golden file not found: %s", golden_path)
        sys.exit(2)

    # ── Load & validate ────────────────────────────────────────────────
    schema = load_schema()
    golden = load_golden(golden_path)
    validate(instance=golden, schema=schema)
    logger.info("Golden '%s' loaded and validated: %s", golden["golden_id"], golden_path)

    # ── Dry-run: show what would be sent ───────────────────────────────
    if args.dry_run:
        user_query = clean_multiline_text(golden.get("inputs", {}).get("user_query", ""))
        context_prompt = build_system_prompt_from_context(golden)
        print("\n=== DRY RUN ===")
        print(f"Golden ID:    {golden['golden_id']}")
        print(f"Workflow:     {golden.get('workflow_type', '?')}")
        print(f"Runtime mode: {golden.get('entrypoint', {}).get('runtime_mode', '?')}")
        print(f"Task type:    {golden.get('entrypoint', {}).get('task_type', '?')}")
        print(f"\nUser query ({len(user_query)} chars):")
        print(f"  {user_query[:300]}...")
        print(f"\nSystem prompt from context ({len(context_prompt)} chars):")
        if context_prompt:
            print(f"  {context_prompt[:300]}...")
        else:
            print("  (none)")
        print("\nExpected eval outcome:")
        print(f"  task_success={golden.get('expected_eval_outcome', {}).get('task_success', '?')}")
        print(f"  min_quality_score={golden.get('expected_eval_outcome', {}).get('min_quality_score', 0.0)}")
        print("\n✅ Dry-run complete. No LLM call was made.")
        sys.exit(0)

    # ── Route: via Planner or direct ───────────────────────────────────
    if args.via_planner:
        logger.info("Routing golden '%s' through RuntimePlanner ...", golden["golden_id"])
        run_artifact = run_through_planner(golden)
    else:
        logger.info("Starting direct runtime execution for '%s' ...", golden["golden_id"])
        run_artifact = run_golden_through_runtime(golden)

    # ── Write output ───────────────────────────────────────────────────
    output_path = generate_eval_run_path(run_artifact["golden_id"])
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(run_artifact, f, ensure_ascii=False, indent=2)
    logger.info("Artifact written: %s", output_path)

    # ── Summary ────────────────────────────────────────────────────────
    meta = run_artifact["_meta"]
    eval_rec = run_artifact["evaluation_record"]

    print()
    print("=" * 60)
    print(f"  Golden:     {run_artifact['golden_id']}")
    print(f"  Workflow:   {run_artifact['workflow_type']} ({run_artifact['department']})")
    print(f"  Model:      {meta['model_used']}")
    print(f"  Cost:       ${meta['cost_usd']:.6f}")
    print(f"  Tokens:     {meta['tokens_total']} (prompt+completion)")
    print(f"  Status:     {'✅ PASS' if meta['passed'] else '❌ FAIL'}")
    print(f"  Task:       {eval_rec.get('task_success', '?')} "
          f"(expected: {meta['expected_task_success']})")
    print(f"  Quality:    {eval_rec.get('quality_score', 0.0):.3f} "
          f"(min required: {meta['min_required_score']})")
    print(f"  Trace:      {eval_rec.get('trace_id', '?')}")
    print(f"  Output:     {output_path}")
    print("=" * 60)

    # Exit code: 0 = pass, 1 = fail
    sys.exit(0 if meta["passed"] else 1)


if __name__ == "__main__":
    main()