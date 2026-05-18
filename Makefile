.PHONY: eval-smoke

eval-smoke:
	python scripts/run_golden.py eval/golden/research_competitor_brief_v1.yaml
	python scripts/run_golden.py eval/golden/delivery_specification_draft_v1.yaml
