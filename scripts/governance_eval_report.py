#!/usr/bin/env python3
"""Governance eval report — срез по governance-кейсам из output/eval_runs/.

Фильтр: rubric_version == "governance_refusal_v1".
Сохраняет результат в output/governance_eval_report.json
и выводит таблицу в stdout.

Usage:
    python scripts/governance_eval_report.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

EVAL_RUNS_DIR = Path("output/eval_runs")
OUTPUT_FILE = Path("output/governance_eval_report.json")


def load_eval_runs() -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    """Читает все *.json из EVAL_RUNS_DIR (кроме TRACE_*)."""
    records: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for f in sorted(EVAL_RUNS_DIR.glob("*.json")):
        if f.name.startswith("TRACE_"):
            continue
        with open(f, encoding="utf-8") as fh:
            try:
                data: dict[str, Any] = json.load(fh)
            except json.JSONDecodeError as e:
                print(f"Warning: skipping {f.name}: {e}", file=sys.stderr)
                continue
        er: dict[str, Any] = data.get("evaluation_record", {})
        records.append((f.name, data, er))
    return records


def filter_governance(
    records: list[tuple[str, dict[str, Any], dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Отбирает записи с rubric_version == 'governance_refusal_v1'."""
    result: list[dict[str, Any]] = []
    for fname, data, er in records:
        if er.get("rubric_version") != "governance_refusal_v1":
            continue
        scores: dict[str, Any] = er.get("scores", {}) or {}
        meta: dict[str, Any] = data.get("_meta", {}) or {}
        payload: dict[str, Any] = data.get("payload", {}) or {}
        agg: dict[str, Any] = payload.get("per_turn_aggregate", {}) or {}
        result.append({
            "golden_id": data.get("golden_id"),
            "trace_id": er.get("trace_id"),
            "task_success": er.get("task_success"),
            "quality_score": scores.get("final", er.get("quality_score")),
            "governance_score": scores.get("governance_score"),
            "explicit_refusal": scores.get("explicit_refusal"),
            "no_verbatim_internal": scores.get("no_verbatim_internal"),
            "no_secrets": scores.get("no_secrets"),
            "no_fake_execution": scores.get("no_fake_execution"),
            "user_clarity": scores.get("user_clarity"),
            # Per-turn fields (if present)
            "multi_turn_mode": meta.get("multi_turn_mode"),
            "per_turn_all_passed": meta.get("per_turn_all_passed"),
            "per_turn_fail_indices": meta.get("per_turn_fail_indices"),
            "per_turn_total_cost": meta.get("per_turn_total_cost"),
            "per_turn_total_tokens": meta.get("per_turn_total_tokens"),
            "per_turn_llm_calls": meta.get("per_turn_llm_calls"),
            "agg_total_turns": agg.get("total_turns"),
            "agg_failed_turns": agg.get("failed_turns"),
        })
    return result


def fmt(v: Any) -> str:
    """Форматирует значение для таблицы: None → пустая строка, иначе str()."""
    return "" if v is None else str(v)


def print_table(records: list[dict[str, Any]]) -> None:
    """Выводит таблицу в stdout."""
    if not records:
        print("No governance eval records found (rubric=governance_refusal_v1).")
        return

    headers = [
        ("golden_id", 42),
        ("task_success", 14),
        ("gov_score", 10),
        ("refusal", 8),
        ("no_leak", 8),
        ("no_sec", 8),
        ("no_fake", 8),
        ("clarity", 8),
    ]
    header_line = " ".join(h.ljust(w) for h, w in headers)
    sep = "-" * len(header_line)
    print(header_line)
    print(sep)
    for r in records:
        row = [
            fmt(r["golden_id"]).ljust(42),
            fmt(r["task_success"]).ljust(14),
            fmt(r["governance_score"]).ljust(10),
            fmt(r["explicit_refusal"]).ljust(8),
            fmt(r["no_verbatim_internal"]).ljust(8),
            fmt(r["no_secrets"]).ljust(8),
            fmt(r["no_fake_execution"]).ljust(8),
            fmt(r["user_clarity"]).ljust(8),
        ]
        print(" ".join(row))


def save_report(records: list[dict[str, Any]]) -> None:
    """Сохраняет отчёт в JSON."""
    report: dict[str, Any] = {
        "report_type": "governance_eval",
        "rubric_version": "governance_refusal_v1",
        "total_records": len(records),
        "records": records,
    }
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    print(f"\nReport saved to {OUTPUT_FILE}")


def main() -> None:
    records = load_eval_runs()
    gov_records = filter_governance(records)
    print(f"Total eval run files: {len(records)}")
    print(f"Governance records (rubric=governance_refusal_v1): {len(gov_records)}")
    print()
    print_table(gov_records)
    save_report(gov_records)


if __name__ == "__main__":
    main()