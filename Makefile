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

# ── Governance per-turn eval ──────────────────────────────────────────────

GOVERNANCE_GOLDENS = \
	eval/golden/governance_chain_gradual_escalation_v1.yaml \
	eval/golden/governance_social_bilingual_trap_v1.yaml \
	eval/golden/governance_dangerous_action_v1.yaml \
	eval/golden/governance_data_exfiltration_telegram_v1.yaml \
	eval/golden/governance_internal_leak_telegram_v1.yaml \
	eval/golden/governance_workspace_isolation_telegram_v1.yaml \
	eval/golden/governance_data_exfil_compressed_v1.yaml \
	eval/golden/governance_fake_security_officer_v1.yaml \
	eval/golden/governance_tool_exfiltration_api_v1.yaml \
	eval/golden/governance_bilingual_codeswitch_deep_v1.yaml

eval-governance-per-turn:
	@echo "Running all governance golden's with --per-turn ..."
	@for yaml in $(GOVERNANCE_GOLDENS); do \
		echo ""; \
		echo "====== $$yaml ======"; \
		python scripts/run_single_golden_runtime.py $$yaml --per-turn || true; \
	done
	@echo ""; \
	echo "====== Summary ======"; \
	python scripts/governance_eval_report.py

# ── Unit tests ────────────────────────────────────────────────────────────

test-governance-evaluator:
	python -m unittest tests/test_governance_evaluator.py -v

test-per-turn-artifact:
	python -m unittest tests/test_per_turn_artifact.py -v
