#!/usr/bin/env python3
"""Ночной цикл эволюции Pith — генерирует патч-кандидаты и сохраняет в БД."""
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from core.evolution.failure_miner import get_failed_episodes, cluster_by_pattern
from core.evolution.patch_planner import generate_hypothesis
from core.governance.patch_gate import patch_gate

DB_PATH = Path(__file__).parent.parent / "data" / "episodes.db"

def main():
    print(f"🌙 Pith Nightly Evolution started at {datetime.utcnow().isoformat()}")

    fails = get_failed_episodes(100)
    if not fails:
        print("No failures found. Exiting.")
        return

    patterns = cluster_by_pattern(fails)
    conn = sqlite3.connect(DB_PATH)
    candidates_saved = 0

    for name, examples in patterns.items():
        if len(examples) < 3:
            continue

        print(f"Analyzing pattern: {name} ({len(examples)} occurrences)")
        hypothesis = generate_hypothesis(name, examples)

        if not hypothesis or not isinstance(hypothesis, dict):
            print(f"  ⚠️ Failed to generate valid hypothesis")
            continue

        component = hypothesis.get("component", "unknown")
        confidence = hypothesis.get("confidence", 0.0)
        patch_type = hypothesis.get("patch_type", "unknown")

        candidate = {
            "component": component,
            "confidence": confidence,
            "patch_type": patch_type,
            "summary": hypothesis.get("summary", "")
        }
        gate_decision = patch_gate.evaluate(candidate)

        cur = conn.execute(
            """INSERT INTO patch_candidates
               (failure_cluster_id, summary, root_cause, component, patch_type,
                patch_content, confidence, test_plan, status, evaluated_by, metadata_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'proposed', ?, ?)""",
            (
                name,
                hypothesis.get("summary", ""),
                hypothesis.get("root_cause", ""),
                component,
                patch_type,
                hypothesis.get("patch", ""),
                confidence,
                hypothesis.get("test_plan", ""),
                f"PatchGate: {gate_decision.decision} ({gate_decision.reason})",
                f'{{"gate_decision": "{gate_decision.decision}", "ring": "{gate_decision.rollout_ring}"}}'
            )
        )
        patch_id = cur.lastrowid
        candidates_saved += 1
        print(f"  ✅ Patch #{patch_id} saved ({gate_decision.decision})")

    conn.commit()
    conn.close()
    print(f"🌙 Evolution cycle completed. {candidates_saved} candidates saved.")

if __name__ == "__main__":
    main()
