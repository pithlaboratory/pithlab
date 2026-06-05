.PHONY: eval-smoke eval-smoke-summary eval-smoke-gate trace-summary eval-runtime-summary eval-runtime-gate

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

eval-runtime-summary:
	python scripts/eval_runtime_summary.py

eval-runtime-gate:
	python scripts/eval_runtime_gate.py