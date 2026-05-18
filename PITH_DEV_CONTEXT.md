# PITH DEV CONTEXT

---

## 1. What Pith is

Pith is a **self‑improving continuity runtime (Agent OS / cognitive operating layer)** for engineering and cognitive work.[cite:13]

It is not:
- a bot,
- a generic LLM wrapper,
- an AGI claim,
- a feature‑zoo of personas.

It is a runtime layer that:

- connects strategy, memory, tools, execution and reflection into one governed loop;
- decides **how**, **when**, and **with which model lane** work is executed;
- accumulates context, artifacts and failure patterns so the system becomes more precise and more efficient over time.[cite:13]

Core positioning:
- **Chat solves prompts. Pith solves continuity.**[cite:13]

Refer: `docs/PITH_KERNEL.md` as the primary identity and kernel contract.[cite:13]

---

## 2. Current status (2026‑05‑14)

### Baseline

- ✅ `v5.2` runtime baseline is stable enough to serve as the current production/runtime baseline for Telegram.
- ✅ Router, config‑driven model selection, Telegram interface, Orchestrator bridge, Evaluator / FailureMiner / PatchPlanner / SkillCompiler are present architecturally.
- ✅ Main live interface is **Telegram** (Viktor voice as legacy layer); runtime identity is Pith.
- ✅ Dashboard and HTTP/API surfaces remain secondary until the runtime core is more reliable.[cite:11][cite:13]

### TraceStore / Observability

- ✅ TraceStore v1 (task‑level backbone) — implemented:
  - `task_traces` table in `episodes.db`,
  - `TaskService` writes `task_started` / `task_finished` / `task_failed`.[cite:90]
- ✅ TraceStore v1.1 (minimal hardening) — implemented:
  - additive schema migration via `PRAGMA table_info` + `ALTER TABLE ... ADD COLUMN`,
  - enriched schema: `runtime_mode`, `task_type`, `failure_class`, `error_code`, `cost_estimate_usd`, `runtime_config_ver`,
  - `TaskService.update_status`:
    - writes `failure_class` and `error_code` into `task_traces`,
    - passes `cost_usd` into `cost_estimate_usd` on completed tasks.[cite:90]
  - `FailureClass` enum defined in `core/observability/failure_taxonomy.py` as minimal failure taxonomy.[cite:90]
- 🟡 TraceStore v1.2 (planned under `PITH_OBSERVABILITY_V1.md`):
  - per‑LLM‑call spans,
  - per‑agent spans,
  - `evaluator_score` linkage.[cite:89]

### Evaluation / Governance

- ✅ `PITH_EVALUATION_V1.md` defines Evaluation architecture (quality, reliability, usefulness, safety, business effectiveness).[cite:89]
- ✅ `PITH_GOVERNANCE_V1.md` defines autonomy tiers and governance baseline; current envelope: **L0–L1 only**.[cite:89]
- 🟡 PithEval v0.1 dataset (30–50 ground‑truth tasks) — design in place, implementation ongoing.[cite:89]
- 🟡 Governance wiring in code (PatchGate / RolloutManager / autonomy.yaml) — structural work planned.[cite:89]

### In progress

- 🟡 Real implementations of agents (`tera`, `hex`, `coda`) instead of thin bridge/stub behaviour.
- 🟡 TraceStore v1.x expansion:
  - end‑to‑end `trace_id` propagation,
  - ExecutionResult wiring,
  - ContextAssembler audit against `PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`.[cite:90][cite:12]
- 🟡 PithEval v0.1 (aligned with `PITH_EVALUATION_V1.md`).
- 🟡 CLI `pith ask/dev/incident`.[cite:11]

### Infra

- Server: `msk-1-vm-ngf0`
- OS: Ubuntu 24.04
- Runtime process: `systemd` → `pith_v5.service`.[cite:11]

---

## 3. Core system map

| Layer        | Main components                                                      |
|-------------|-----------------------------------------------------------------------|
| **Interface**   | `telegram_bot.py`, CLI (planned), future HTTP/API/web surface          |
| **Routing**     | `router.py` — lane selection, fallback, budget gate, provider switching |
| **Planning**    | `planner.py` / RuntimePlanner — task_type detection, direct vs orchestrated path, context assembly integration |
| **Orchestration** | `orchestrator.py` — bridge for modular agents, parallel execution, synthesis |
| **Memory**      | `manager.py`, `episodes.db`, `memory.db`, `skills/index.json`, profile/context assembly |
| **Evaluation**  | `evaluator.py` — quality/context/disclaimer scoring, failure classification (planned) |
| **Evolution**   | `miner.py` → `patch_planner.py` → `skill_compiler.py`                 |
| **Governance**  | `PatchGate`, `RolloutManager`, `autonomy.yaml`, future kill switch    |
| **Artifacts / runtime substrate** | tasks, traces (`task_traces`), `llm_calls`, `failure_cases`, manifests, candidate patches, runtime versions |

---

## 4. Current priorities (next 30 days)

### 4.1 Runtime hardening (Trace / Context / Execution)

1. **TraceStore v1.x — hardening baseline**

   - Maintain `task_traces` as canonical task‑level trace backbone.
   - Ensure additive schema remains backward compatible.
   - Add end‑to‑end `trace_id` propagation (interfaces → Router → Planner → Orchestrator → TraceStore).[cite:90][cite:12]

2. **ExecutionResult contract**

   - Define minimal `ExecutionResult` DTO/structure for Orchestrator:
     - model id / lane,
     - cost, tokens, latency,
     - outcome (success/partial/failure),
     - pointers to artifacts.
   - Ensure ExecutionResult is:
     - written to trace / artifacts,
     - available to Evaluator/PithEval.[cite:89]

3. **ContextAssembler audit**

   - Align ContextAssembler with `PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`:
     - avoid unnecessary self‑analysis and persona drift in NORMAL mode,
     - respect context budgets and routing policies.[cite:12][cite:90]
   - Document current behaviour gaps and patch plan in `PITH_RUNTIME_CONTEXT_REVIEW_2026-05-14.md`.[cite:90]

### 4.2 Evaluation / Governance

4. **PithEval v0.1**

   - 30–50 ground‑truth tasks (code, research, planning, diagnostics).
   - Measure:
     - success/failure/partial,
     - human overrides,
     - cost vs quality.[cite:89]
   - Connect Evaluation metrics to trace data (`task_traces`, `llm_calls`, `failure_cases`).[cite:89]

5. **Governance baseline L0–L1**

   - Implement practical autonomy envelope from `PITH_GOVERNANCE_V1.md`:
     - L0 (no autonomous changes),
     - L1 (limited autonomous proposals with human approval).[cite:89]
   - Prepare `autonomy.yaml` skeleton for Action Classes and Tiers.

6. **CLI v0.1**

   - `pith ask` — direct query without Telegram.
   - `pith dev` — context‑aware code/architecture work.
   - `pith incident` — diagnostics/postmortems.[cite:11]

---

## 5. Workflow and constraints

### Dev environment

- VS Code + Remote SSH on `msk-1-vm-ngf0`.
- AI assistant via OpenRouter (Continue / Cline style workflow).
- Goal: preserve context and reduce breakage during iteration.[cite:11]

### Rules for assistants and commits

1. First analyze, then propose a plan, then change code.
2. No broad uncontrolled refactors.
3. Preserve Telegram production runtime unless explicitly told otherwise.
4. Prefer small reversible steps.
5. Use explicit diffs and clear commit messages.
6. Any non‑trivial change must be reflected in `PITH_CHANGELOG.md`.
7. Important architectural changes go to `PITH_MASTER_PLAN.md` or ADR notes.[cite:11]

### Runtime constraints

- Budget target: about `$30/month` (hard stop enforced by router/policies).[cite:175]
- `hard_stop: true` for cost guardrails.
- `quality_weighted_cost` matters (Evaluation + Observability drive routing decisions).[cite:89][cite:175]
- Production stability beats elegance.
- Avoid large UI/frontend work until runtime reliability improves.
- Autonomy envelope: **L0–L1 only** (Tier 0–1 in `PITH_GOVERNANCE_V1.md`).[cite:89]

---

## 6. Identity guardrails for development

Every meaningful change should reinforce at least one of these properties:

- **continuity**
- **memory quality**
- **orchestration clarity**
- **execution reliability**
- **observability**
- **governed evolution**[cite:13]

Every meaningful change should avoid pushing Pith toward:

- chatbot‑first UX,
- persona‑first architecture,
- uncontrolled autonomy,
- feature‑zoo complexity,
- memory without governance,
- orchestration without traces.[cite:13]

Refer: `docs/PITH_KERNEL.md` + `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`.[cite:13]

---

## 7. Canonical references

Before making major changes, align with:

- `docs/PITH_KERNEL.md`
- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
- `docs/PITH_OBSERVABILITY_V1.md`
- `docs/PITH_EVALUATION_V1.md`
- `docs/PITH_GOVERNANCE_V1.md`
- `docs/PITH_MASTER_PLAN.md`
- `docs/PRODUCT_DOCTRINE.md`
- `docs/PITH_RUNTIME_CONTEXT_REVIEW_2026-05-14.md`
- `docs/RUNTIME_REFACTOR_CHECKLIST_V1.md`[cite:11][cite:90]

If code, naming or direction conflicts with those files, those documents win unless explicitly revised.

---

## 8. Architectural boundaries — what is core now, what's next, what's not

### Core now (defines production identity)

These components are **already in place** and must remain stable:

- **Router** (`router.py`) — model lane selection, fallback, budget enforcement, provider switching.
- **RuntimePlanner** (`planner.py`) — task_type detection, direct vs orchestrated path, context assembly integration.[cite:12]
- **Task/Artifact substrate** — canonical `TaskRecord`, `ArtifactRecord`, `TaskService`, TraceStore v1.x.[cite:90]
- **Telegram production path** (`interfaces/telegram_bot.py`) — primary live interface.
- **Evaluator** (`evaluator.py`) — persona coherence, context use, disclaimer detection, failure scoring (with Evaluation v1).[cite:89]
- **Memory Manager** (`manager.py`) — episodes, memory DBs, user profiles, `save_episode` / `get_recent_context`.
- **Orchestrator bridge** (`orchestrator.py`) — modular agent dispatch, parallel execution, synthesis.
- **Evolution scaffolding** — `FailureMiner`, `PatchPlanner`, `SkillCompiler` (architectural presence, not full loop yet).
- **Observability baseline** — `episodes.db`, `llm_calls`, `failure_cases`, `task_traces` (TraceStore v1.x).[cite:90]

Changes здесь должны быть:
- малыми,
- обратимыми,
- с чёткой мотивацией и отражением в docs/ADR/changelog.[cite:11]

---

### Next substrate (30–90 day build horizon)

What is actively being built:

1. **Real agent implementations** (`tera`, `hex`, `coda`)
2. **TraceStore v1.x** (end‑to‑end trace, ExecutionResult, spans)
3. **PithEval v0.1**
4. **CLI v0.1**
5. **Memory v2 design**
6. **Tool Contracts**
7. **Governance rollout completion**
8. **A2A protocol**[cite:11][cite:89][cite:90]

---

### Explicitly not now (conscious no‑list)

What is **not** in scope until runtime core is reliably observed:

- ❌ Big dashboard/UI work.
- ❌ Multimodal polish.
- ❌ Persona expansion / “agent zoo”.
- ❌ Uncontrolled self‑modification (no auto‑apply patches without governance).
- ❌ Feature‑zoo surfaces (Slack/Discord/web shell/IDE plugins) до стабильности ядра.
- ❌ “Intelligence fabric” (repo/doc/web monitoring) как core — это capability layer после Tool Contracts.[cite:13][cite:89]

---

*Last updated: 2026‑05‑14 · Pith Lab · Internal / Confidential*