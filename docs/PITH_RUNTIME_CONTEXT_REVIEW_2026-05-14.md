# PITH RUNTIME CONTEXT REVIEW — 2026-05-14

## Purpose

This document captures the first structured runtime-context review for Pith v5.2 and converts the current architecture understanding into a scoped runtime-hardening execution baseline.

It is intended to serve as a repository-level source of truth for the current hardening phase, rather than leaving the analysis only inside chat history.

***

## Initial context review

### Review prompt

```text
Review the currently loaded Pith project context.
1. Identify the canonical architecture layers you infer.
2. Name any likely documentation conflicts or missing contracts.
3. Propose the best review order for runtime hardening work.
Do not expand beyond the current phase.
```

### Response summary

#### 1. Canonical architecture layers

The project context suggests two orthogonal dimensions.

##### Vertical planes

| Plane | Status in docs |
|---|---|
| Runtime Plane (Operating Loop) | Fully described in KERNEL §6 and RUNTIME_CONTEXT_PROTOCOL §4–5 |
| Model Plane | Described in KERNEL §3.1 and MASTER_PLAN §4 |
| Tool Plane | Described in KERNEL §3.2 and referenced in DEV_CONTEXT |
| State Plane | Core entities are defined in KERNEL §4, but service contracts are not yet explicit |
| Governance Plane | Defined in GOVERNANCE_V1 and partially implemented |
| Agent Company Plane | Described conceptually, implementation absent |
| Evolution Plane | Described in MASTER_PLAN §7 and partially scaffolded |

##### Horizontal implementation layers

- Interface Layer → `telegram_bot.py`, CLI (partial), FastAPI (prototype)
- Cognition Layer → `router.py`, `planner.py`, `orchestrator.py`, policy engine absent
- Agent Company Layer → department registry absent, workflows absent
- Execution Layer → tool calls without formal contracts, MCP not described in code
- Memory Layer → `manager.py`, `episodes.db`, `skills/index.json`
- Evolution Layer → `evaluator.py`, `miner.py`, `patch_planner.py`, `skill_compiler.py`

#### 2. Likely documentation conflicts and missing contracts

##### Conflict A — Router vs RuntimePlanner boundary

- `MASTER_PLAN §3.2` frames Router as responsible for LLM routing, fallback, and budget.
- `IMPLEMENTATION_EPIC §4.1` narrows Router to lane/model-path selection and excludes execution topology ownership.
- `DEV_CONTEXT §8` aligns Router with model lane selection, fallback, budget enforcement, and provider switching.

**Gap:** `RuntimePlanner` responsibility is described in docs but not yet locked as an explicit code-level contract or schema. `ACTIVE_CONTEXT` still reflects unfinished audit work around `TaskService` and `Evaluator`.

##### Conflict B — ContextAssembler described but not confirmed in code

- `RUNTIME_CONTEXT_PROTOCOL_V1 §11` defines a Python-like `context_assembler.build(...)` contract and expected output shape.
- `IMPLEMENTATION_EPIC §6.1` states that normal runtime execution should not bypass `ContextAssembler`.

**Gap:** current runtime may still assemble prompt/context outside a verifiable `ContextAssembler` contract. This is not yet explicitly logged as confirmed debt in the changelog.

##### Conflict C — TraceStore v1 scope mismatch

- `CHANGELOG` for 2026-05-12 records `task_traces` as implemented and smoke-tested.
- `ACTIVE_CONTEXT §4` still lists TraceStore alignment with `PITH_OBSERVABILITY_V1.md` as TODO.
- `OBSERVABILITY_V1 §5` requires fields such as `runtime_mode`, `task_type`, `failure_class`, `error_code`, `cost_estimate_usd`, and related observability metadata.

**Gap:** the implemented trace schema does not yet cover the minimal observability contract needed for evaluation linkage.

##### Critical missing contracts for the current phase

| Missing contract | Mentioned in | Risk |
|---|---|---|
| `ExecutionResult` schema (Orchestrator → TaskService) | `ACTIVE_CONTEXT §4` | Orchestrator writes trace/output state through arbitrary dicts |
| `ContextAssembler` output schema (code-level) | `RUNTIME_CONTEXT_PROTOCOL §11` | Planner may assemble context without a verifiable contract |
| `RuntimeConfig` versioning contract | `KERNEL §7.5`, `ACTIVE_CONTEXT §4` | Runtime config behaves like a magic global and cannot be sliced reliably |
| Tool contract schema (JSON Schema per tool) | `MASTER_PLAN ADR #5`, `DEV_CONTEXT §8` | Tool plane is invoked without typed interface discipline |
| `PolicyDecision` record schema | `GOVERNANCE_V1 §11` | Governance decisions are not persisted in trace form |
| `BillableEvent` schema | `MASTER_PLAN §5.3`, `EPIC §6.5` | Agent Company workflows cannot be cost-attributed cleanly |
| `failure_class` enum (code-level) | `OBSERVABILITY_V1 §8`, `EPIC §4.3` | Errors are written to traces without stable classification |

#### 3. Recommended review order for runtime hardening

The review order should move from runtime invariants toward higher-level capabilities.

1. **TraceStore v1 — schema gap audit**
   - Compare `task_traces` against the minimum observability dictionary from `OBSERVABILITY_V1 §5`
   - Convert missing fields into a concrete migration list
   - Prioritize `failure_class`, `runtime_mode`, and `cost_estimate_usd`

2. **RuntimePlanner contract audit**
   - Inspect signatures in `planner.py`
   - Verify whether planner writes `runtime_mode`, `task_type`, and `autonomy_level` into trace context
   - Verify whether planner routes context assembly through `ContextAssembler`

3. **ContextAssembler — existence check**
   - Confirm whether a real module exists with the contract described in `RUNTIME_CONTEXT_PROTOCOL §11`
   - If not, classify the gap explicitly as code-level debt

4. **`failure_class` enum introduction**
   - Implement the minimum enum set from `OBSERVABILITY_V1 §8`
   - Integrate it on task failure paths

5. **ExecutionResult schema**
   - Define a `dataclass` or `TypedDict`
   - Require Orchestrator to return a typed execution result instead of arbitrary dicts

6. **RuntimeConfig versioning check**
   - Verify that `runtime_config_version` is written into `task_traces`
   - If absent, treat this as a blocker for evaluation slicing

7. **Evaluator linkage audit**
   - Verify evaluator reads `trace_id` / `task_id`
   - Verify evaluation results persist with trace linkage
   - If not, record it as Phase C work rather than expanding current scope

##### Out of scope for the current phase

- Agent Company department workflows
- `BillableEvent` schema implementation
- `ContextRetriever` / `RepoIndexer`
- Operator console

### Initial verdict

Documentation is aligned at a conceptual level. The immediate gap is not strategy but missing verifiable code-level contracts around `ContextAssembler`, `ExecutionResult`, and `failure_class`. TraceStore v1 exists, but its schema does not yet meet the minimum fields needed for evaluation linkage.

Priority: **1 → 3 → 4**, with **2 and 5** possible in parallel where safe.

***

## Architecture analysis — runtime hardening

### 1. Verdict

Documentation is aligned. Implementation is behind on three critical contracts: TraceStore schema is incomplete, `ContextAssembler` existence is not yet confirmed, and `failure_class` is absent from the codebase. Evaluation and Governance remain blocked until these gaps are addressed.

### 2. Core problem

TraceStore v1 exists at the task level, but `task_traces` does not yet contain the fields required for evaluation linkage: `runtime_mode`, `task_type`, `failure_class`, `cost_estimate_usd`, and `runtime_config_version`.

In parallel, it is still unclear whether `ContextAssembler` exists as a real module matching the contract in `RUNTIME_CONTEXT_PROTOCOL_V1 §11`, or whether `RuntimePlanner` still assembles prompt/context manually.

### 3. Recommended design

Three minimum changes, in order of importance:

1. **TraceStore schema migration**
   - Add `runtime_mode`, `task_type`, `failure_class`, `error_code`, `cost_estimate_usd`, and `runtime_config_version` to `task_traces`
   - Use ALTER-based migration with backfill-safe defaults rather than rewrite

2. **`failure_class` enum**
   - Introduce it under `core/observability/`
   - Integrate it into `TaskService.update_status()` on failure paths

3. **ExecutionResult schema**
   - Define it as `dataclass` or `TypedDict`
   - Make Orchestrator return it instead of arbitrary dict output

4. **ContextAssembler existence check**
   - Treat this as a binary verification item whose result defines the next contract-hardening step

### 4. Risks

- `task_traces` schema migration can break existing reads if migration guards are missing.
- `failure_class` rollout without exception-path audit produces partial coverage and weakens downstream failure analysis.
- If `ContextAssembler` is absent, planner context assembly remains hidden coupling outside a traceable contract boundary.

### 5. Next step

Audit two files first:

- `core/observability/trace_store.py` — current `task_traces` schema
- `core/runtime/planner.py` — whether `ContextAssembler` is actually called

The outcome of those audits should drive the first code-level patch plan.

***

## Patch / execution plan — runtime hardening

### 1. Verdict

The patch is feasible without architectural rewrite. All proposed changes are local, reversibly compatible, and within the current hardening phase. The blocker for evaluation linkage is removed after P1–P3; the rest is sequential closure of contract gaps.

### 2. What is broken

| ID | What is broken | Where | Severity |
|---|---|---|---|
| B1 | `task_traces` lacks `runtime_mode`, `task_type`, `failure_class`, `error_code`, `cost_estimate_usd`, `runtime_config_version` | `trace_store.py` | Critical — blocks evaluation linkage |
| B2 | `failure_class` does not exist as a typed enum in the codebase | new module needed | High — FailureMiner operates on raw strings |
| B3 | `ExecutionResult` is not fixed as a schema; Orchestrator returns arbitrary dicts | `orchestrator.py` | High — trace/output state remains incomplete |
| B4 | `RuntimeConfig` version is not verifiably written into `task_traces` | `task_service.py` | High — evaluation cannot be sliced by version |
| B5 | `ContextAssembler` existence and contract are not confirmed | `planner.py` | Medium — hidden coupling remains outside trace visibility |

### 3. Minimal patch set

#### P1 — TraceStore schema migration (`core/observability/trace_store.py`)

Add to `CREATE TABLE task_traces`:

```python
runtime_mode        TEXT,
task_type           TEXT,
failure_class       TEXT,
error_code          TEXT,
cost_estimate_usd   REAL,
runtime_config_ver  TEXT
```

Implementation rules:

- migration guard through `PRAGMA table_info`
- `ALTER TABLE` only for missing columns
- backfill-safe default as `NULL`
- no rewrite of existing trace rows

API changes:

- `TraceStore.task_started()` accepts optional `runtime_mode`, `task_type`, `runtime_config_ver`
- `TraceStore.task_failed()` accepts `failure_class`, `error_code`
- `TraceStore.task_finished()` accepts `cost_estimate_usd`

#### P2 — `failure_class` enum (`core/observability/failure_taxonomy.py`)

```python
from enum import Enum

class FailureClass(str, Enum):
    ROUTING_FAILURE       = "routing_failure"
    PLANNER_FAILURE       = "planner_failure"
    ORCHESTRATOR_FAILURE  = "orchestrator_failure"
    TOOL_FAILURE          = "tool_failure"
    MEMORY_FAILURE        = "memory_failure"
    POLICY_FAILURE        = "policy_failure"
    APPROVAL_TIMEOUT      = "approval_timeout"
    ARTIFACT_FAILURE      = "artifact_failure"
    QUALITY_FAILURE       = "quality_failure"
    COST_GUARDRAIL        = "cost_guardrail_violation"
    UNKNOWN_FAILURE       = "unknown_failure"
```

Integration rules:

- `TaskService.update_status()` accepts `failure_class: FailureClass` on failure paths
- forward value into `TraceStore.task_failed()`
- default to `UNKNOWN_FAILURE` for backward compatibility where explicit class is not yet passed

#### P3 — RuntimeConfig version in TaskService (`core/services/task_service.py`)

- `create_task()` reads `runtime_config_version` from current runtime config
- forwards it into `TraceStore.task_started()`
- if config is not versioned, write explicit string `"unversioned"` rather than `NULL`

#### P4 — ExecutionResult schema (`core/runtime/execution_result.py`)

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ExecutionResult:
    task_id:           str
    status:            str
    output:            Optional[str] = None
    artifact_refs:     list[str] = field(default_factory=list)
    failure_class:     Optional[str] = None
    error_summary:     Optional[str] = None
    cost_estimate_usd: Optional[float] = None
    runtime_mode:      Optional[str] = None
```

Integration rules:

- Orchestrator must return `ExecutionResult`
- `TaskService.attach_execution_result()` must accept `ExecutionResult` and write relevant fields into `task_traces`

#### P5 — ContextAssembler audit (`core/runtime/planner.py`)

Binary check:

- If `ContextAssembler` exists, verify planner calls `context_assembler.build(...)` and writes `context_profile` trace signal
- If absent, log explicit debt in `PITH_CHANGELOG.md` and create a stub module matching `RUNTIME_CONTEXT_PROTOCOL_V1 §11` without full implementation

This step does not block P1–P4 but must be recorded before the epic is considered closed.

### 4. What stays deferred

- Per-LLM-call spans / per-agent spans (`TraceStore v1.1+`)
- Evaluator linkage to trace records (unblocked after P1–P3, but not in this cycle)
- Full `ContextAssembler` implementation after audit
- `PolicyDecision` record schema
- `BillableEvent` schema
- Tool contract JSON Schema
- Operator console
- Agent Company workflows and department registry

### 5. Rollout order

1. **P2 — `failure_class` enum**
   - isolated new file, no storage migration dependency
2. **P1 — TraceStore schema migration**
   - depends on stable `failure_class` vocabulary for task failure writes
3. **P3 — RuntimeConfig version write path**
   - depends on new trace schema fields
4. **P4 — ExecutionResult schema**
   - depends on updated trace write path
5. **P5 — ContextAssembler audit**
   - independent, but result must be logged in changelog before epic closure

Rule: each step should be a separate commit with explicit scope.

### 6. Verification

| Patch | Verification |
|---|---|
| P1 | `PRAGMA table_info(task_traces)` shows new columns; smoke test creates a task, fails/completes it, and reads back expected fields |
| P2 | `FailureClass("unknown_failure")` is valid; `TaskService` accepts `FailureClass.TOOL_FAILURE` without type/runtime issues |
| P3 | After `create_task()`, `runtime_config_ver` is non-null in `task_traces` |
| P4 | Orchestrator returns `ExecutionResult`; `isinstance(result, ExecutionResult)` is true on every execution path |
| P5 | `PITH_CHANGELOG.md` records either `ContextAssembler verified, contract matched` or `ContextAssembler absent, stub created, debt logged` |

***

## Proposed changelog entry

```text
2026-05-14 — Added PITH_RUNTIME_CONTEXT_REVIEW_2026-05-14.md and initial runtime hardening Patch / Execution Plan (TraceStore schema, FailureClass enum, ExecutionResult, RuntimeConfig versioning, ContextAssembler audit).
```
EOF && wc -l output/PITH_RUNTIME_CONTEXT_REVIEW_2026-05-14.md