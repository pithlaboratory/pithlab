# PITH v5

PITH is an operational AI runtime built to move real work forward across dialogue, tasks, memory, agents, repositories, external tools, and observability. [file:278]

The system is evolving from a Telegram-first runtime into a multi-surface product with shared runtime semantics across chat, API, web, and future voice interfaces. [file:278][file:361]

## What PITH includes

- Telegram runtime interface with task creation, loading UX, governance guards, feedback handling, memory writes, and trace-aware execution. [file:278]
- Task and planning layer that correlates requests with `task_id`, `trace_id`, `workspace_id`, runtime mode, and execution metadata. [file:278]
- Agent and API layer for creating agents, launching work, and polling task state over structured endpoints. [file:361]
- Product shell direction through web surfaces such as landing pages and API explorer experiences. [file:361]

## Repo structure

- `core/` — runtime, memory, task services, governance, observability, planner, and tools. [file:278]
- `agents/` — agent definitions and role-oriented logic. [file:278]
- `scripts/` — inspection, debug, eval, and operational helper scripts. [file:278]
- `docs/` — system, operating, and operational documentation. [file:278]
- `dashboard/` and `dashboard.py` — current visual and control surfaces. [file:278]
- `config.yaml` — primary runtime configuration. [file:278]

## Current state

- Telegram runtime is the primary production entrypoint for PITH today. [file:278]
- Observability, evaluation, and cost tracking are live through traces, tasks, and evaluator records. [file:278]
- Governance guards are wired into the runtime for dangerous deletes, prompt leakage, data exfiltration, and workspace isolation. [file:278]
- Agent/API and web surfaces exist as the emerging product shell for non-Telegram access. [file:278][file:361]

## Core docs

PITH uses a four-document core stack:

- `docs/PITH_SYSTEM_VISION.md` — defines the product and system identity, interface direction, autonomy boundaries, and long-horizon evolution.
- `docs/PITH_CAPABILITIES_MODEL.md` — defines the capability map, capability layers, and contracts between system abilities.
- `docs/PITH_OPERATING_STANDARD.md` — defines how PITH is operated, measured, governed, and released.
- `docs/PITH_MASTER_PLAN.md` — defines execution order, strategic priorities, milestones, and implementation sequencing. [file:278]

Recommended reading order:

1. `docs/PITH_SYSTEM_VISION.md`
2. `docs/PITH_CAPABILITIES_MODEL.md`
3. `docs/PITH_OPERATING_STANDARD.md`
4. `docs/PITH_MASTER_PLAN.md`

Rule of thumb:

- Vision answers **what PITH becomes**.
- Capabilities answer **what PITH can do and how abilities are structured**.
- Operating standard answers **how PITH is run safely and consistently**.
- Master plan answers **what gets built next and in what order**. [file:278]

## Runtime principles

- Every meaningful action should be traceable through task and trace correlation. [file:278]
- Memory, tasks, and observability should stay aligned across all interfaces. [file:278]
- New capabilities should not be treated as production-ready without smoke coverage, observability hooks, and ownership. [file:278]
- Governance is part of the runtime, not an afterthought; dangerous delete, prompt leakage, data exfiltration, and workspace isolation are first-class refusal paths. [file:278]

## Operations quick start

1. Activate the environment.
2. Validate configuration.
3. Restart the required service.
4. Check service health and logs.
5. Verify a smoke path through Telegram or another active interface. [file:278]

Example:

```bash
cd /root/pith_v5
source /root/pith_v5/venv/bin/activate
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
systemctl restart pith_v5.service
systemctl status pith_v5.service --no-pager
journalctl -u pith_v5.service -n 50 --no-pager
```

## Related docs

- `README-env.md` — environment and service notes for the current VM and deployment shape. [file:278]
- `docs/observability-smoke-checklist.md` — deploy and smoke validation checklist. [file:278]
- `PITH_CHANGELOG.md` — record of major changes. [file:278]
- `TODO_ENGINEERING.md` — active engineering follow-ups. [file:278]