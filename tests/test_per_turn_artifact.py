"""Tests for per-turn evaluation artifact contract in run_single_golden_runtime.py.

Verifies that the --per-turn mode produces correct _meta and payload fields.
No LLM calls — patches call_llm to return a controlled stub response.
"""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Any, Dict

# ── Ensure project root is on sys.path ────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_single_golden_runtime import run_golden_multi_turn_per_turn


def make_mock_golden(
    golden_id: str = "test_per_turn_mock_v1",
    turn_count: int = 3,
) -> Dict[str, Any]:
    """Build a minimal golden dict with conversation for per-turn testing."""
    conversation = []
    for i in range(turn_count):
        conversation.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"User message {i}" if i % 2 == 0 else f"Assistant reply {i}",
        })
    return {
        "golden_id": golden_id,
        "version": 1,
        "department": "governance",
        "workflow_type": "governance_refusal_test",
        "autonomy_tier": "Tier 0-1",
        "entrypoint": {
            "runtime_mode": "telegram_chat",
            "task_type": "governance_refusal",
        },
        "inputs": {
            "description": "Mock multi-turn golden for per-turn artifact test.",
            "user_query": "Final dangerous request.",
            "conversation": conversation,
            "initial_context": [
                {
                    "type": "note",
                    "role": "system",
                    "content": "Test context: workspace isolation policy.",
                },
            ],
        },
        "expected_properties": {
            "high_level_goal": "Test per-turn artifact contract.",
        },
        "rubric": {
            "rubric_version": "governance_refusal_v1",
            "dimensions": [
                {"name": "explicit_refusal", "scale": "pass/fail", "description": "..."},
            ],
        },
        "expected_eval_outcome": {
            "task_success": "success",
            "human_override": "none",
            "min_quality_score": 0.6,
            "policy_violation": False,
        },
        "owner": {
            "name": "Test",
            "contact": "test@pith.lab",
        },
    }


class TestPerTurnArtifactContract(unittest.TestCase):
    """Verify that run_golden_multi_turn_per_turn() produces correct output."""

    def setUp(self):
        self.maxDiff = None  # show full diff on failure

    def _stub_call_llm(self, **kwargs) -> Dict[str, Any]:
        """Return a controlled LLM response stub."""
        return {
            "content": "Я не могу выполнить это действие. Доступ ограничен.",
            "model": "test-model/gpt-4o-mini",
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 10,
            },
            "cost_usd": 0.0001,
        }

    @patch("core.cognition.router.call_llm")
    def test_meta_fields_present_and_correct_types(self, mock_call_llm):
        """_meta contains all required per-turn fields with correct types."""
        mock_call_llm.side_effect = self._stub_call_llm

        golden = make_mock_golden(turn_count=4)
        artifact = run_golden_multi_turn_per_turn(golden)

        meta = artifact.get("_meta", {})
        # ── General fields ──
        self.assertIn("multi_turn", meta)
        self.assertIs(meta["multi_turn"], True)

        self.assertIn("multi_turn_mode", meta)
        self.assertEqual(meta["multi_turn_mode"], "per_turn")

        # ── per-turn count fields ──
        self.assertIn("per_turn_count", meta)
        self.assertIsInstance(meta["per_turn_count"], int)
        self.assertGreaterEqual(meta["per_turn_count"], 1)

        self.assertIn("per_turn_all_passed", meta)
        self.assertIsInstance(meta["per_turn_all_passed"], bool)

        self.assertIn("per_turn_fail_indices", meta)
        self.assertIsInstance(meta["per_turn_fail_indices"], list)

        self.assertIn("per_turn_llm_calls", meta)
        self.assertIsInstance(meta["per_turn_llm_calls"], int)
        self.assertGreaterEqual(meta["per_turn_llm_calls"], 1)

        self.assertIn("per_turn_total_cost", meta)
        self.assertIsInstance(meta["per_turn_total_cost"], float)
        self.assertGreaterEqual(meta["per_turn_total_cost"], 0.0)

        self.assertIn("per_turn_total_tokens", meta)
        self.assertIsInstance(meta["per_turn_total_tokens"], int)
        self.assertGreaterEqual(meta["per_turn_total_tokens"], 0)

        self.assertIn("per_turn_eval_version", meta)
        self.assertIsInstance(meta["per_turn_eval_version"], str)
        self.assertEqual(meta["per_turn_eval_version"], "governance_refusal_v1")

        self.assertIn("notes", meta)
        self.assertIsInstance(meta["notes"], str)
        self.assertIn("Per-turn", meta["notes"])

    @patch("core.cognition.router.call_llm")
    def test_payload_fields_present_and_correct_types(self, mock_call_llm):
        """Payload contains per_turn_evaluations and per_turn_aggregate with correct structure."""
        mock_call_llm.side_effect = self._stub_call_llm

        golden = make_mock_golden(turn_count=4)
        artifact = run_golden_multi_turn_per_turn(golden)

        payload = artifact.get("payload", {})

        # ── per_turn_evaluations ──
        self.assertIn("per_turn_evaluations", payload)
        self.assertIsInstance(payload["per_turn_evaluations"], list)

        # ── per_turn_aggregate ──
        self.assertIn("per_turn_aggregate", payload)
        agg = payload["per_turn_aggregate"]
        self.assertIsInstance(agg, dict)
        self.assertIn("total_turns", agg)
        self.assertIsInstance(agg["total_turns"], int)
        self.assertIn("failed_turns", agg)
        self.assertIsInstance(agg["failed_turns"], int)
        self.assertIn("all_success", agg)
        self.assertIsInstance(agg["all_success"], bool)
        self.assertIn("worst_turn_index", agg)
        self.assertIsInstance(agg["worst_turn_index"], int)

        # ── Existing standard fields still present ──
        self.assertIn("trace_id", payload)
        self.assertIn("task_id", payload)
        self.assertIn("workspace_id", payload)
        self.assertIn("runtime_mode", payload)
        self.assertIn("task_type", payload)
        self.assertIn("user_query", payload)
        self.assertIn("conversation_turn_count", payload)
        self.assertIn("conversation_roles", payload)

    @patch("core.cognition.router.call_llm")
    def test_per_turn_evaluation_entries(self, mock_call_llm):
        """Each entry in per_turn_evaluations has the required sub-fields."""
        mock_call_llm.side_effect = self._stub_call_llm

        golden = make_mock_golden(turn_count=4)
        artifact = run_golden_multi_turn_per_turn(golden)

        evaluations = artifact.get("payload", {}).get("per_turn_evaluations", [])

        for entry in evaluations:
            self.assertIn("turn_index", entry)
            self.assertIsInstance(entry["turn_index"], int)
            self.assertIn("role", entry)
            self.assertEqual(entry["role"], "assistant")
            self.assertIn("user_query", entry)
            self.assertIsInstance(entry["user_query"], str)
            self.assertIn("assistant_response", entry)
            self.assertIsInstance(entry["assistant_response"], str)
            self.assertIn("evaluation", entry)
            ev = entry["evaluation"]
            self.assertIn("explicit_refusal", ev)
            self.assertIn("no_verbatim_internal", ev)
            self.assertIn("no_secrets", ev)
            self.assertIn("no_fake_execution", ev)
            self.assertIn("user_clarity", ev)
            self.assertIn("governance_score", ev)
            self.assertIn("task_success", ev)
            self.assertIn("rubric_version", ev)
            self.assertEqual(ev["rubric_version"], "governance_refusal_v1")

    @patch("core.cognition.router.call_llm")
    def test_per_turn_count_vs_conversation(self, mock_call_llm):
        """per_turn_count matches conversation length, llm_calls ≤ turn_count for user turns."""
        mock_call_llm.side_effect = self._stub_call_llm

        for turn_count in [2, 4, 6]:
            golden = make_mock_golden(turn_count=turn_count)
            artifact = run_golden_multi_turn_per_turn(golden)
            meta = artifact["_meta"]
            payload = artifact["payload"]

            cc = len(golden["inputs"]["conversation"])
            self.assertEqual(
                meta["per_turn_count"],
                cc,
                f"per_turn_count ({meta['per_turn_count']}) != conversation length ({cc})",
            )
            self.assertEqual(
                payload["conversation_turn_count"],
                cc,
                f"conversation_turn_count ({payload['conversation_turn_count']}) != {cc})",
            )
            # llm_calls <= turn_count (only user turns trigger LLM)
            self.assertLessEqual(
                meta["per_turn_llm_calls"],
                meta["per_turn_count"],
                f"llm_calls ({meta['per_turn_llm_calls']}) > turn_count ({meta['per_turn_count']})",
            )

    @patch("core.cognition.router.call_llm")
    def test_artifact_serializable_to_json(self, mock_call_llm):
        """Full artifact must be JSON-serializable (no non-serializable types)."""
        mock_call_llm.side_effect = self._stub_call_llm

        golden = make_mock_golden(turn_count=4)
        artifact = run_golden_multi_turn_per_turn(golden)

        try:
            json.dumps(artifact, indent=2, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            self.fail(f"Artifact is not JSON-serializable: {e}")


if __name__ == "__main__":
    unittest.main()