# PITH v5

PITH is a workspace-native continuity runtime for long-running cognitive and operational work.

It is built to move real work forward across dialogue, tasks, memory, agents, repositories, external tools, and observability.

PITH is runtime-first:
- continuity across sessions and workflows,
- traceable execution,
- governed task flow,
- workspace-aware memory,
- evaluation and observability by design.

Current practical focus:
- runtime stabilization,
- observability and evaluation v1,
- governance baseline,
- Support/Ops Desk as the first product wedge.

---

## What PITH includes

- Telegram runtime interface with task creation, loading UX, governance guards, feedback handling, memory writes, and trace-aware execution.
- Task and planning layer that correlates requests with `task_id`, `trace_id`, `workspace_id`, runtime mode, and execution metadata.
- Runtime services for planning, orchestration, memory, observability, evaluation, and governance.
- Emerging product shell through API, dashboard, and future web/voice surfaces.

---

## Current state

- Telegram runtime is the main live production entrypoint today.
- Observability, evaluation, and cost tracking are active through tasks, traces, and evaluator records.
- Governance guards are part of the runtime path.
- API and web surfaces are secondary until runtime reliability is stronger.
- Current phase: Runtime stabilization + Observability/Eval v1 + Support/Ops Desk wedge.

---

## Repo structure

- `core/` — runtime, planner, routing, memory, governance, observability, services, tools
- `agents/` — agent definitions and role-oriented logic
- `scripts/` — debug, eval, inspection, and operational helper scripts
- `docs/` — system, architecture, governance, and roadmap documentation
- `dashboard/` and `dashboard.py` — visual/operator surfaces
- `config.yaml` — primary runtime configuration
- `interfaces/` — Telegram and other interface layers

---

## Documentation map

Start here:

1. `docs/PITH_DOCS_INDEX.md`
2. `PITH_ACTIVE_CONTEXT.md`
3. `PITH_DEV_CONTEXT.md`

Canonical core docs:

- `docs/PITH_MASTER_PLAN.md`
- `docs/PITH_KERNEL.md`
- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
- `docs/PITH_OBSERVABILITY_V1.md`
- `docs/PITH_EVALUATION_V1.md`
- `docs/PITH_GOVERNANCE_V1.md`

Product and direction docs:

- `docs/PITH_SYSTEM_VISION.md`
- `docs/PITH_CAPABILITIES_MODEL.md`
- `docs/PITH_OPERATING_STANDARD.md`

---

## Quick start

```bash
cd /root/pith_v5
source /root/pith_v5/venv/bin/activate
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

For environment-specific operations, service control, restart flow, and smoke checks, see:

- `README-env.md`
- `docs/observability-smoke-checklist.md`

---

## Runtime principles

- Every meaningful action should be traceable.
- Memory, tasks, and observability should stay aligned across interfaces.
- New capabilities are not production-ready without smoke coverage, observability hooks, and clear ownership.
- Governance is part of the runtime, not an afterthought.

---

## Related docs

- `README-env.md` — active VM environment and service operations note
- `docs/PITH_DOCS_INDEX.md` — canonical document map
- `PITH_CHANGELOG.md` — meaningful change history
- engineering TODO/backlog — short-term execution work