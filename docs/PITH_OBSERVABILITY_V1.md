# Pith Observability v1

> Observability architecture for Pith v5 as a runtime-native, multi-agent, continuity-aware system.

---

## 1. Purpose

Pith Observability v1 defines how Pith should be observed, traced, debugged, measured, and audited in production.

Pith observability is not limited to logs and infra metrics.
It must provide visibility into:

- runtime flow,
- planner/orchestrator behavior,
- tool execution,
- memory operations,
- agent handoffs,
- cost formation,
- workflow outcomes,
- policy and approval boundaries.

This document exists because traditional logging is not enough for modern agent systems.
A successful HTTP response does not prove that the runtime made correct decisions.

Observability is also the primary data source for **evaluation** and **self‑evolution**:
production traces must be reusable as evaluation cases and learning signals.

---

## 2. Why This Matters

Pith is evolving toward:

- a workspace-native AGI runtime,
- a continuity engine,
- an Agent Company OS,
- a governed execution system.

As a result, failure can happen in many layers:

- wrong planner choice,
- silent tool misuse,
- failed department handoff,
- broken memory retrieval,
- inflated model/tool costs,
- low-quality output that still appears "successful,"
- autonomy beyond intended policy,
- incomplete or misleading traces.

Without strong observability, Pith cannot be debugged, trusted, evaluated, or safely monetized.

---

## 3. Observability Principles

### 3.1 Runtime-native

Observability must be built into runtime contracts, not bolted on later.
Core Runtime components (Planner, Orchestrator, TaskService, Tool/Model Plane, Memory) emit structured events by design.

### 3.2 Trace-first

Every meaningful workflow should be reconstructible as a trace, not just as scattered logs.

Trace is the main reconstruction and debugging unit for:

- planner/orchestrator behavior,
- department/agent handoffs,
- tool calls,
- memory operations,
- billable events and cost,
- policy decisions and approvals.

### 3.3 Multi-layer visibility

Pith must expose visibility across:

- request entry,
- planner decisions,
- orchestrator execution,
- subtask transitions,
- memory operations,
- tool calls,
- agent/department outcomes,
- user-facing completion state.

### 3.4 Workspace-aware

Observability must preserve tenant/workspace boundaries and avoid leaking cross-workspace state.
Every trace and event is scoped at least by `tenant_id` and `workspace_id`.

### 3.5 Cost-aware

Every expensive action must be attributable:

- by workspace,
- by task,
- by trace,
- by department,
- by agent role,
- by tool/model.

### 3.6 Governance-compatible

Observability must support:

- audits,
- approvals,
- policy enforcement review,
- postmortems,
- rollback analysis.

> **Role boundary**: Observability does not decide policy or quality; it exposes stable signals that `PITH_EVALUATION_V1` and `PITH_GOVERNANCE_V1` consume to make those decisions.

### 3.7 Evaluation-ready

Observability data should be directly reusable by the evaluation pipeline:

- traces can be sampled into evaluation suites,
- metrics and failure taxonomy feed evaluation dashboards,
- production regressions can be replayed and compared against previous model/prompt versions.

> Observability provides the raw trace/event data; evaluation defines sampling strategies, metrics, and regression tests on top of that data.

---

## 4. Observability Surfaces

Pith observability should expose five core surfaces.

### 4.1 Execution Traces

A trace is the main reconstruction unit for runtime behavior.

A trace should show:

- entrypoint,
- request goal,
- tenant_id,
- workspace_id,
- task_id,
- workflow_id (if applicable),
- trace_id,
- planner mode selection,
- orchestrator branches,
- agent handoffs,
- tool calls,
- memory reads/writes,
- retries,
- final result.

Traces should be compatible with standard tracing patterns (span/parent_span semantics) to integrate with external tooling (e.g. OTel‑style backends).

> **Canonical store for v1**: `TraceStore v1` is the canonical runtime trace store for Pith v5. Any core runtime component (Planner, Orchestrator, TaskService, Tool/Model Plane, Memory) must emit its minimum trace events via `TraceStore`. Additional logging/metrics are allowed but do not replace the TraceStore contract.

### 4.2 Structured Event Stream

Every major runtime transition should emit structured events.

Examples:

- `request_received`
- `task_created`
- `planner_started`
- `planner_completed`
- `orchestrator_started`
- `subtask_dispatched`
- `tool_invoked`
- `tool_completed`
- `memory_read`
- `memory_write`
- `approval_required`
- `approval_granted`
- `approval_rejected`
- `billable_event_recorded`
- `workflow_completed`
- `workflow_failed`

Events should follow a stable schema so they can be shipped to log/metric systems and reused by evaluation tools.

### 4.3 Metrics Layer

Pith should aggregate operational metrics such as:

- workflow success rate,
- planner routing distribution,
- average task duration,
- tool latency,
- model latency,
- retry counts,
- failure rates by step,
- cost per workflow,
- cost per department,
- cost per client/workspace,
- memory retrieval hit usefulness,
- human approval frequency.

### 4.4 Audit Layer

Pith should support audit-oriented inspection for:

- who triggered a workflow,
- which agent/department acted,
- what tools were used,
- what approvals were required,
- what artifacts were created,
- what the final business outcome was,
- what billable events were emitted.

### 4.5 Replay / Debug Layer

For important failures and regressions, Pith should support replay-style debugging:

- inspect the exact trace path,
- compare planned vs actual execution,
- compare outputs across prompt/model versions,
- isolate where a workflow degraded.

Replay does not mean recreating full hidden chain-of-thought.
It means reconstructing runtime decisions and externally visible behavior.

---

## 5. Core Trace Model

The minimum runtime trace model should include the following fields. Fields are categorized by v1 requirement level.

### 5.1 Required in v1 (non‑nullable for runtime events)

| Field | Description | Scope |
|-------|-------------|-------|
| `trace_id` | Unique correlation ID for the trace | Global |
| `workspace_id` | Workspace boundary (tenant may be empty in dev) | Workspace |
| `task_id` | Task identifier (for task‑scoped events) | Task |
| `event_type` | Type of event (e.g. `planner_started`, `tool_invoked`) | Event |
| `status` | Outcome status (`ok`, `failed`, `cancelled`) | Event |
| `timestamp` | ISO‑8601 timestamp of the event | Event |
| `duration_ms` | Duration for completed steps (nullable for in‑progress) | Event |
| `runtime_mode` | Planner mode (`normal`, `diagnostics`, `vision`) | Planner |
| `task_type` | Classified task type (`general`, `coding`, `research`, …) | Task |
| `cost_estimate_usd` | Estimated cost for the step (0 if not applicable) | Cost |
| `failure_class` | Failure taxonomy label (for failed/errored events) | Failure |

### 5.2 Optional in v1 / Future

| Field | Description | Planned for |
|-------|-------------|-------------|
| `tenant_id` | Multi‑tenant boundary | Agent Company v1 |
| `workflow_id` | Parent workflow identifier | Orchestrator v2 |
| `session_id` | User session correlation | UX v2 |
| `department`, `department_role`, `agent` | Agent Company hierarchy | Agent Company v1 |
| `token_usage_in`, `token_usage_out` | Token accounting | Billing v2 |
| `cost_actual_usd` | Final billed cost | Billing v2 |
| `artifact_refs`, `billable_event_refs` | Links to artifacts / billing | Agent Company v1 |
| `error_code`, `error_summary` | Structured error details | Failure taxonomy v2 |

> This is the minimum viable trace vocabulary. It may be extended later, but the system should converge around a stable trace contract early.

### 5.3 Envelope Linkage

Начиная с `PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`, каждый runtime‑шаг должен быть восстанавливаем из комбинации:

- envelope‑снимка (или его части),
- одного или нескольких trace events.

Для этого trace‑события v1 должны:

- ссылаться на `trace_id`, `task_id`, `workspace_id` из envelope,
- иметь ссылку на `envelope_version`,
- для ключевых событий (planner, orchestrator, approvals, billing, artifact) включать **сжатый snapshot** соответствующих блоков envelope:
  - для governance‑связанных событий — выжимку из `governance` блока,
  - для artifact‑событий — выжимку из `artifacts` блока,
  - для billing‑событий — выжимку из `billing` блока.

Цель: Governance/Evaluation/Billing должны уметь восстановить необходимый контекст **без обращения к сторонним системам**, опираясь только на TraceStore + envelope.

---

## 6. What Must Be Observable

### 6.1 Planner Behavior

For RuntimePlanner, Pith should record:

- inputs used for decision (safe summary),
- chosen mode/path,
- declared rationale summary,
- route outcome,
- fallback path if used.

Planner traces are critical for understanding misrouting and cost/performance trade‑offs.

### 6.2 Orchestrator Behavior

For orchestrated workflows, Pith should record:

- execution graph,
- subtasks created,
- departments involved,
- agent roles involved,
- handoff order,
- completion or failure per subtask,
- aggregated final result summary.

### 6.3 Memory Operations

Memory observability should include:

- memory read attempts,
- source of memory hit,
- retrieval scope,
- workspace filter applied,
- retrieval score / confidence,
- writes to long-term memory,
- temporary vs durable memory distinction.

This is required both for debugging continuity issues and for evaluating retrieval quality.

### 6.4 Tool Calls

Every tool invocation should expose:

- tool name,
- arguments hash or safe summary,
- start/end time,
- latency,
- result summary,
- retry count,
- failure reason if any.

Raw secrets or unsafe payloads must not be exposed in traces.

### 6.5 Agent Company Operations

For department workflows, observability should include:

- department label,
- agent role,
- autonomy level (Tier 0–4),
- billable event references,
- business outcome category,
- human approval checkpoints,
- artifact production.

This allows cost and quality analysis per department and per vertical.

### 6.6 Governance / Approvals

Для Governance/HITL observability должна фиксировать:

- какие действия требовали approval,
- каким policy‑решением это было определено,
- кто и когда дал/отклонил approval,
- на каком уровне автономии работал агент (Tier 0–4),
- каким был итоговый approval state для трассы/задачи.

Минимальный набор событий:

- `approval_required` — система определила, что шаг требует review,
- `approval_requested` — запрос отправлен reviewer’у,
- `approval_granted` — approval дан,
- `approval_rejected` — отказ,
- `approval_escalated` — эскалация (роль/департамент),
- `approval_expired` — просрочен SLT/TTL.

Каждое approval‑событие должно включать:

- `trace_id`, `task_id`, `workspace_id`,
- `policy_id`, `autonomy_tier`, `requested_autonomy_tier`,
- `action_class`,
- `approval_state` до/после,
- `subject` (кто запросил) и `reviewer` (кто принял решение, если применимо),
- ссылку на соответствующий approval‑checkpoint из runtime‑envelope.

### 6.7 Artifacts

Артефакты — отдельный first‑class слой, и observability должна позволять:

- понять, какие артефакты были созданы/обновлены в рамках трассы,
- проследить lineage артефактов (из каких задач/артефактов они происходят),
- оценить качество и использование артефактов в последующих workflows.

Минимальный набор событий:

- `artifact_created`
- `artifact_updated`
- `artifact_deleted` (если поддерживается)
- `artifact_published` (доступен за пределами исходного workspace/department)
- `artifact_used_as_input` (артефакт включён в контекст другого task/workflow)

Каждое artifact‑событие должно включать:

- `trace_id`, `task_id`, `workspace_id`,
- `artifact_id`, `artifact_type`, `artifact_role` (draft, reference, published),
- `lineage` ссылки: `created_from_task_ids`, `derived_from_artifact_ids`,
- high‑level summary (без больших payload’ов).

События должны быть согласованы с `artifacts` блоком из `PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md` и `PITH_ARTIFACT_SYSTEM_V1` (когда он появится).

### 6.8 Billing

Для cost/monetization observability должна отражать:

- где и почему возникли billable events,
- как cost накапливается по трассе,
- какие guardrails/лимиты сработали.

Минимальный набор событий:

- `billing_event_recorded` — зафиксирован billable event (tokens, tool, model, workflow),
- `billing_limit_hit` — достигнут лимит (task/workspace/tenant),
- `billing_projection_updated` — обновлён прогнозируемый cost по трассе/задаче,
- `billing_anomaly_detected` (future) — подозрительная аномалия cost.

Каждое billing‑событие должно включать:

- `trace_id`, `task_id`, `workspace_id`, `tenant_id` (если есть),
- `billing_unit` (`task|workflow|artifact|outcome`),
- `billing_context` (department, workflow, plan, tags),
- `runtime_cost_estimate` (tokens, usd),
- для `billing_limit_hit` — какое именно ограничение сработало (`task_usd_limit`, `workspace_monthly_usd_limit`, `premium_hops_limit`).

Эти события должны быть консистентны с billing‑блоком из runtime‑envelope и будущим `PITH_BILLING_V1`.

---

## 7. Observability and Cost

Pith should treat cost as a first-class observability signal.

Cost must be attributable by:

- trace,
- workflow,
- workspace,
- tenant,
- department,
- agent,
- tool,
- model.

This is required not only for infrastructure control, but also for monetization and product design:

- which department is expensive,
- which workflow is profitable,
- which tool path is too costly,
- which client/workspace exceeds expected usage.

Cost telemetry should be consistent with billing events in `PITH_AGENT_COMPANY_V1.md` and the billing model.

---

## 8. Failure Taxonomy

Pith should classify failures instead of collapsing everything into generic "error."

Suggested failure classes:

- `routing_failure`
- `planner_failure`
- `orchestrator_failure`
- `tool_failure`
- `memory_failure`
- `policy_failure`
- `approval_timeout`
- `artifact_failure`
- `quality_failure`
- `cost_guardrail_violation`
- `unknown_failure`

Each failure should be attached to a trace event with `failure_class`, `error_code`, and `error_summary`.
A stable failure taxonomy is necessary for postmortems, evaluation, and operational learning.

### 8.1 Event Families

Чтобы упростить анализ и эволюцию observability‑схемы, события v1 группируются в семейства:

- **Core Runtime Events**  
  `request_received`, `task_created`, `task_started`, `task_finished`, `task_failed`, `workflow_started`, `workflow_completed`, `workflow_failed`.

- **Planner / Orchestrator Events**  
  `planner_started`, `planner_routed`, `planner_fallback_used`,  
  `orchestrator_started`, `subtask_dispatched`, `subtask_completed`, `subtask_failed`.

- **Tool / Memory Events**  
  `tool_invoked`, `tool_completed`, `tool_failed`,  
  `memory_read`, `memory_write`, `memory_hit`, `memory_miss`.

- **Governance / Approval Events**  
  `approval_required`, `approval_requested`, `approval_granted`, `approval_rejected`, `approval_escalated`, `approval_expired`,  
  `policy_decision_applied`, `policy_guardrail_triggered`.

- **Artifact Events**  
  `artifact_created`, `artifact_updated`, `artifact_deleted`, `artifact_published`, `artifact_used_as_input`.

- **Billing / Cost Events**  
  `billing_event_recorded`, `billing_limit_hit`, `billing_projection_updated`, `billing_anomaly_detected` (future).

Каждый event family должен использовать общий поднабор полей (envelope linkage + специфические поля), чтобы упростить:

- агрегацию и дашборды,
- отбор трасс для evaluation,
- построение регрессий по конкретным классам проблем (например, approvals vs artifacts vs billing).

---

## 9. v1 Dashboards / Views

Pith should eventually expose at least these operator-facing views:

1. **Trace Explorer**  
   Search by `trace_id`, `task_id`, `workspace_id`, `tenant_id`.

2. **Workflow View**  
   See department flow, outcomes, approvals, artifacts, billable events.

3. **Cost View**  
   Cost by workflow, department, model, tool, workspace, tenant.

4. **Failure View**  
   Group failures by taxonomy and recurrence.

5. **Memory View**  
   Inspect memory usage and retrieval behavior.

These do not need to exist as polished UI in v1, but the data model should be designed for them.

---

## 10. v1 Implementation Priorities

Observability v1 should focus on:

1. Stable `trace_id` propagation (from interface → runtime → tools/models → result).
2. Structured runtime events (planner, orchestrator, tools, memory, billing).
3. Minimum trace schema (section 5) implemented as a real store (e.g. `TraceStore v1`).
4. Workflow/tool/model cost attribution via trace events and billable events.
5. Failure taxonomy adoption in all critical components.
6. Operator-readable logs and debugability for priority paths.

Do not overbuild full analytics before the trace contract is stable.

> **Concrete v1 store**: `TraceStore v1` stores at minimum:
> - `task_traces` (aggregate per task, as currently implemented),
> - optional `trace_events` (fine‑grained step log, deferred to v2).
>
> For v1, `task_traces` is the aggregate trace table for task‑level observability. Future versions may add `trace_events` as a fine‑grained event log; v1 does not require this yet.
>
> Core components must ensure that all **Required v1** fields (section 5.1) are populated for `task_started`, `task_finished`, and `task_failed` events.

---

## 11. Out of Scope for v1

Not required immediately:

- perfect replay across all model/tool versions,
- full distributed tracing infrastructure,
- polished observability UI,
- advanced anomaly detection,
- deep autonomous remediation.

These can be layered later.
The goal of v1 is reliable visibility and evaluation‑readiness, not observability perfection.

---

## 12. Next Integration Points

This document should influence:

- `PITH_ACTIVE_CONTEXT.md`
- `docs/PITH_AGENT_COMPANY_V1.md`
- `docs/PITH_EVALUATION_V1.md`
- `docs/PITH_GOVERNANCE_V1.md`
- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
- planner/orchestrator contracts
- TaskService and execution result schemas
- future operator console work

Pith should not expand autonomy or monetized agent workflows without observability that is good enough to support trust, debugging, evaluation, and cost control.

---

<div style="text-align: center; margin-top: 40px; color: #666;">

**Pith Lab · Москва · 2026**

*Версия v1.2.1 · Май 2026 · CONFIDENTIAL / INTERNAL*

</div>
