.PHONY: eval-smoke eval-smoke-summary eval-smoke-gate \
        trace-summary \
        eval-runtime-golden eval-runtime-summary eval-runtime-gate

eval-smoke:
	python scripts/run_golden.py eval/golden/research_competitor_brief_v1.yaml
	python scripts/run_golden.py eval/golden/delivery_specification_draft_v1.yaml
	python scripts/run_golden.py eval/golden/governance_dangerous_action_v1.yaml
	python scripts/run_golden.py eval/golden/governance_internal_leak_telegram_v1.yaml
	python scripts/run_golden.py eval/golden/governance_data_exfiltration_telegram_v1.yaml
	python scripts/run_golden.py eval/golden/governance_workspace_isolation_telegram_v1.yaml
	python scripts/run_golden.py eval/golden/support_ops_faq_v1.yaml
	python scripts/run_golden.py eval/golden/support_ops_escalation_v1.yaml

eval-smoke-summary:
	python scripts/eval_smoke_summary.py

eval-smoke-gate:
	$(MAKE) eval-smoke
	$(MAKE) eval-smoke-summary

trace-summary:
	python scripts/trace_summary.py

# Новый таргет: прогон всех golden'ов через RuntimePlanner
eval-runtime-golden:
	@echo "Running all golden evals via Planner..."
	@python scripts/run_all_golden_via_planner.py

# Сводка по runtime-eval'ам (как и раньше)
eval-runtime-summary:
	python scripts/eval_runtime_summary.py

# Гейт: сначала прогон через Planner, затем сводка + gate-логика
eval-runtime-gate:
	$(MAKE) eval-runtime-golden
	$(MAKE) eval-runtime-summary
	python scripts/eval_runtime_gate.py