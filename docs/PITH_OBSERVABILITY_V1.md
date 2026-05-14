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
- low-quality output that still appears “successful,”
- autonomy beyond intended policy,
- incomplete or misleading traces.

Without strong observability, Pith cannot be debugged, trusted, evaluated, or safely monetized.[web:2080][web:2083]

---

## 3. Observability Principles

### 3.1 Runtime-native

Observability must be built into runtime contracts, not bolted on later.
Core Runtime components (Planner, Orchestrator, TaskService, Tool/Model Plane, Memory) emit structured events by design.

### 3.2 Trace-first

Every meaningful workflow should be reconstructible as a trace, not just as scattered logs.[web:2087]

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
- by tool/model.[web:2086]

### 3.6 Governance-compatible

Observability must support:

- audits,
- approvals,
- policy enforcement review,
- postmortems,
- rollback analysis.

### 3.7 Evaluation-ready

Observability data should be directly reusable by the evaluation pipeline:

- traces can be sampled into evaluation suites,
- metrics and failure taxonomy feed evaluation dashboards,
- production regressions can be replayed and compared against previous model/prompt versions.[web:2079][web:2083]

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
- `approval_denied`
- `billable_event_recorded`
- `workflow_completed`
- `workflow_failed`

Events should follow a stable schema so they can be shipped to log/metric systems and reused by evaluation tools.[web:2084][web:2088]

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

The minimum runtime trace model should include:

- `trace_id`
- `tenant_id`
- `workspace_id`
- `task_id`
- `workflow_id` (if applicable)
- `session_id` (if applicable)
- `entrypoint`
- `runtime_mode`
- `task_type`
- `department`
- `department_role` (agent role within department)
- `agent`
- `step_id`
- `parent_step_id`
- `event_type`
- `status`
- `timestamp`
- `duration_ms`
- `model_name` (if applicable)
- `tool_name` (if applicable)
- `token_usage_in`
- `token_usage_out`
- `cost_estimate_usd`
- `cost_actual_usd`
- `artifact_refs`
- `billable_event_refs`
- `failure_class` (from failure taxonomy)
- `error_code`
- `error_summary`

This is the minimum viable trace vocabulary.
It may be extended later, but the system should converge around a stable trace contract early.[web:2082][web:2087]

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
- autonomy level (L0–L3),
- billable event references,
- business outcome category,
- human approval checkpoints,
- artifact production.

This allows cost and quality analysis per department and per vertical.[web:2080][web:2086]

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
- which client/workspace exceeds expected usage.[web:2086]

Cost telemetry should be consistent with billing events in `PITH_AGENT_COMPANY_V1.md` and the billing model.

---

## 8. Failure Taxonomy

Pith should classify failures instead of collapsing everything into generic “error.”

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
A stable failure taxonomy is necessary for postmortems, evaluation, and operational learning.[web:2079][web:2083]

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

These do not need to exist as polished UI in v1, but the data model should be designed for them.[web:2081][web:2085]

---

## 10. v1 Implementation Priorities

Observability v1 should focus on:

1. Stable `trace_id` propagation (from interface → runtime → tools/models → result).
2. Structured runtime events (planner, orchestrator, tools, memory, billing).
3. Minimum trace schema (section 5) implemented as a real store (e.g. `TraceStore v1`).
4. Workflow/tool/model cost attribution via trace events and billable events.
5. Failure taxonomy adoption in all critical components.
6. Operator-readable logs and debugability for priority paths.

Do not overbuild full analytics before the trace contract is stable.[web:2082][web:2084]

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

Pith should not expand autonomy or monetized agent workflows without observability that is good enough to support trust, debugging, evaluation, and cost control.[web:2080][web:2083][web:2086]