.PHONY: eval-smoke eval-smoke-summary eval-smoke-gate

eval-smoke:
	python scripts/run_golden.py eval/golden/research_competitor_brief_v1.yaml
	python scripts/run_golden.py eval/golden/delivery_specification_draft_v1.yaml
	python scripts/run_golden.py eval/golden/governance_dangerous_action_v1.yaml
	python scripts/run_golden.py eval/golden/governance_internal_leak_telegram_v1.yaml

eval-smoke-summary:
	python scripts/eval_smoke_summary.py

eval-smoke-gate: eval-smoke eval-smoke-summary
python scripts/run_golden.py eval/golden/governance_data_exfiltration_telegram_v1.yaml
