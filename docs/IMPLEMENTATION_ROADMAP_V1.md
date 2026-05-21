# Pith Implementation Roadmap

**Status:** ACTIVE  
**Scope:** Pith v5.4 implementation roadmap aligned with `docs/PITH_MASTER_PLAN.md`  
**Focus:** runtime-first core + Support/Ops Desk wedge + governance baseline  
**Last updated:** 2026-05-21

---

## 1. Purpose

Этот документ фиксирует **практический implementation roadmap** для Pith v5.x.

Он отвечает на вопрос: **что именно строить в ближайшие 30–120 дней**, чтобы:
- стабилизировать runtime;
- довести observability / evaluation / governance до рабочего baseline;
- поддержать первый продуктовый wedge: **Support/Ops Desk для B2B-команд**.

Это не заменяет `PITH_MASTER_PLAN.md`, а конкретизирует его на инженерном уровне. [file:14]

---

## 2. Guiding Principle

Приоритеты implementation roadmap подчиняются иерархии:

1. **Primary wedge:** Support/Ops Desk  
2. **Internal platform capability:** governed runtime, traces, eval, approvals, memory, routing  
3. **Deferred platform narrative:** broad “Agent Company OS” / multi-department platform позже, после подтверждения wedge [file:14]

---

## 3. Phase 1 — Runtime stabilization (0–30 days)

### Goal
Сделать runtime предсказуемым, трассируемым и пригодным для пилотных workflows.

### Deliverables

- **Model plane hardening**
  - registry-first routing через `core/model_registry.json`;
  - budget-aware lane selection;
  - fallback handling и routing diagnostics. [file:14]

- **Runtime core boundaries**
  - чётко закрепить границы `Router` / `RuntimePlanner` / `ContextAssembler` / `MemoryManager` / `Evaluator`;
  - убрать размытые ответственности и скрытые side effects. [file:14]

- **TraceStore baseline**
  - task-level traces (`task_traces`);
  - trace linkage: `trace_id`, `task_id`, `workspace_id`, `runtime_mode`;
  - failure taxonomy (`failure_class`, `error_code`). [file:14]

- **Evaluation baseline**
  - `EvaluationRecord v1`;
  - запись eval в episodes/task traces;
  - связь eval ↔ runtime path ↔ task outcome. [file:14]

- **Config / secrets hygiene**
  - чистый `config.yaml`;
  - единый env lookup для секретов;
  - versioned runtime config footprint в traces. [file:14]

### Exit criteria

- smoke tests проходят стабильно;
- direct vs orchestrated execution различимы в traces;
- cost и failures атрибутируются хотя бы на task/workspace уровне. [file:14]

---

## 4. Phase 2 — Workspace substrate (30–60 days)

### Goal
Сделать `Workspace` и `Task` реальной operational substrate, а не формальностью.

### Deliverables

- **WorkspaceService**
  - canonical CRUD / lookup;
  - жёсткая привязка контекста, памяти, артефактов и traces к workspace. [file:14]

- **TaskService hardening**
  - канонический lifecycle задач;
  - transitions, cancellation/failure states;
  - связка task ↔ workflow ↔ trace. [file:14]

- **ArtifactStore**
  - schema + API;
  - lineage: кто создал, из чего получено, к какому workflow относится. [file:14]

- **Context substrate**
  - ContextAssembler по `PITH_RUNTIME_CONTEXT_PROTOCOL_V1`;
  - relevance floor для memory;
  - token budget и секционные приоритеты. [file:14]

- **Interface unification**
  - Telegram и HTTP/CLI используют один runtime substrate;
  - интерфейсы не содержат отдельной бизнес-логики. [file:14]

### Exit criteria

- любой task имеет workspace binding;
- artifacts и traces можно восстановить по workspace/task;
- memory retrieval не ломает identity и не floods prompt. [file:14]

---

## 5. Phase 3 — Governance baseline (30–90 days)

### Goal
Сделать Pith управляемым для реальных pilot workflows.

### Deliverables

- **Policy / approval baseline**
  - risk classes;
  - approval checkpoints;
  - HITL states: pending / approved / rejected / escalated. [file:14]

- **Budget & risk controls**
  - лимиты по workspace / task / day;
  - premium quotas;
  - fallback policy и kill-switch alerts. [file:14]

- **Runtime versioning / rollout primitives**
  - `runtime_versions`;
  - `patch_candidates`;
  - `patch_rollouts`;
  - rollback hooks и canary semantics. [file:14]

- **Operator visibility**
  - dashboard/operator console v1:
    - tasks,
    - traces,
    - costs,
    - failures,
    - approvals,
    - runtime version view. [file:14]

- **Safe tool runtime policy**
  - deny-by-default;
  - sandbox classes;
  - scoped permissions;
  - traceability всех tool calls. [file:14]

### Exit criteria

- high-impact workflows не идут без approval/policy;
- routing, tool use и cost видны оператору;
- rollback path существует хотя бы на baseline уровне. [file:14]

---

## 6. Phase 4 — Support/Ops Desk enablement (60–120 days)

### Goal
Поддержать первый внешний wedge: **Digital Support/Ops Desk**.

### Deliverables

- **Workflow contracts**
  - 5–10 production-like workflows;
  - explicit acceptance criteria;
  - risk class + approval policy + escalation rules. [file:14]

- **Knowledge/admin flow**
  - загрузка customer docs / SOP / FAQ;
  - document ingest baseline;
  - привязка knowledge к workspace. [file:14]

- **Support/Ops execution loop**
  - intake → classify → answer / escalate → artifact/report → trace/eval;
  - HITL‑friendly escalation;
  - weekly reporting baseline. [file:14]

- **Business usefulness scorecard**
  - response time,
  - deflection,
  - escalation quality,
  - operator edits,
  - time saved. [file:14]

### Exit criteria

- есть 1–3 пилотных сценария, где desk даёт измеримую пользу;
- traces/eval/business metrics связаны между собой;
- можно объяснить, почему workflow окупается или нет. [file:14]

---

## 7. Phase 5 — Capability accumulation (parallel / after baseline)

### Goal
Сделать успешные execution patterns reusable и эволюционирующими.

### Deliverables

- `SkillRegistry`
- candidate mining из traces / evaluations / artifacts
- review pipeline: approve / reject / rollout
- binding skills to workflow types / workspaces / desks [file:14]

### Exit criteria

- повторяемые паттерны извлекаются из runtime;
- skill changes проходят через governance и rollback path;
- evolution не ломает stable workflows silently. [file:14]

---

## 8. Phase 6 — Intelligence expansion (later)

### Goal
Расширить глубину контекста без потери управляемости.

### Deliverables

- `RepoIndexer`
- `ContextRetriever`
- `DocumentIngestor`
- `WebResearch` / `WebMonitor`
- richer context graph and multimodal intake [file:14]

### Exit criteria

- контекст расширяется управляемо;
- новые источники не ломают budget / traceability / policy boundaries. [file:14]

---

## 9. Out of scope for current cycle

Сознательно **не делаем сейчас**:

- broad self-serve “platform for everyone”;
- неконтролируемый multi-agent zoo;
- persona-layer как продуктовую идентичность;
- глубокий auto-patching ядра без human gate;
- high-autonomy L3–L4 workflows без сильного eval/governance. [file:14]

---

## 10. Practical priority order

Если ресурсов мало, строить в таком порядке:

1. Trace / Eval / Task lifecycle
2. Workspace / Artifact substrate
3. Governance / approvals / budget guards
4. Support/Ops Desk workflows
5. Skill lifecycle
6. Repo/web/document intelligence [file:14]

---

## 11. Success condition

Roadmap считается успешным, если Pith v5.x становится:

- достаточно стабильным для pilot workflows;
- достаточно наблюдаемым для расследования ошибок и cost spikes;
- достаточно управляемым для low-risk semi-automation;
- достаточно полезным, чтобы Support/Ops Desk давал измеримый operational outcome. [file:14]