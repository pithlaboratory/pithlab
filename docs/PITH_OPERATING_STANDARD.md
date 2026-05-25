# PITH Operating Standard

> PITH is an operational AI runtime. This document defines how it must behave in production: what to observe, how to evaluate, how to control cost, and which checks are mandatory before and after changes.[1][2]

## 1. Purpose

This operating standard sets the minimum bar for running PITH as a long-lived system rather than a one-off bot.[1]

It focuses on four aspects:
- **Observability** — everything important must be traceable and explainable.[1]
- **Evaluation** — behaviour must be testable, not just subjectively “good”.[1]
- **Operational discipline** — predictable deploys, smoke checks, incident handling.[1]
- **Cost control** — LLM usage must be measurable and bounded.[1][2]

This document is intended to be used together with `PITH_SYSTEM_VISION.md`, `PITH_CAPABILITIES_MODEL.md`, and `PITH_MASTER_PLAN.md` so that product evolution, capability growth, and runtime quality stay aligned.[1][3]

## 2. Core operating principles

1. **No invisible work**
   - Every significant operation (task, tool call, agent run, governance guard, eval) must leave a trace.[1]

2. **No unmeasured quality**
   - Critical flows must have eval or smoke coverage; subjective “it seems fine” is not sufficient.[1]

3. **No unbounded LLM usage**
   - Every interface and capability must expose token and cost metrics.[1][2]

4. **No ungoverned autonomy**
   - Dangerous actions, cross-workspace access, and data exfiltration must be mediated by governance guards and refusals.[1]

5. **No feature without ownership**
   - Any meaningful subsystem must have a code owner, an operational owner, and a place in the master plan.[1][3]

6. **No production surface without runtime parity**
   - Telegram, API, web UI, and future voice interfaces must map into the same task, memory, and observability model rather than inventing separate local logic.[1][2][3]

## 3. Observability model

### 3.1 Core identifiers

Every meaningful event in PITH must be identifiable and correlatable.[1]

Required identifiers:
- `task_id` — unique per logical task.[1]
- `trace_id` — unique per end-to-end execution.[1]
- `workspace_id` — context isolation for memory and tasks.[1]
- `user_id` — origin of the request.[1]
- `channel` — e.g. `telegram`, `api`, `web`.[1][3]
- `session_id` — optional but recommended for multi-turn interface reconstruction.[1]
- `tool_call_id` — recommended for non-trivial tool chains and agent workflows.[1]

These IDs must be:
- present in TaskService records and metadata;[1]
- attached to episodes in memory;[1]
- propagated to trace service and observability integrations;[1]
- recoverable from scripts and dashboards used by operators.[1]

### 3.2 Event types

At minimum, the following events must be captured:[1]

- `task_created`
- `task_started`
- `task_completed`
- `task_failed`
- `tool_called`
- `tool_failed`
- `governance_refusal`
- `eval_recorded`
- `telegram_message_received` / `api_request_received` / `web_request_received`
- `memory_written` / `memory_read`
- `budget_warning_triggered`

Each event should carry:
- identifiers (task, trace, workspace, user, channel);
- timestamps;
- model information (where applicable);
- cost and token usage (where applicable);
- failure class or refusal reason where applicable.[1][2]

### 3.3 Episodes and memory

Episodes (dialogue turns and responses) must be stored with:
- role (`user` / `assistant` / `system`);
- content;
- workspace and channel;
- task and trace identifiers;
- model and cost metadata (for assistant messages);
- eval / feedback metadata where available.[1]

Episodes DB is the ground truth for reconstructing what happened for a given task or user.[1]

### 3.4 Interface parity

Each user-facing surface must preserve the same minimum metadata quality.[1][2][3]

| Surface | Required guarantees |
|---|---|
| Telegram | Message receipt event, task creation, episode persistence, response metadata, governance refusal logging.[1] |
| API | Request traceability, task lifecycle status, latency visibility, structured error reporting, health visibility.[2] |
| Web | Request/session tracing, action telemetry, artifact/task linkage, parity with API-backed operations.[3] |
| Voice | Transcription event, task linkage, response event, cost and latency visibility, same workspace isolation rules. |

## 4. Evaluation and smoke tests

### 4.1 Eval levels

Evaluation is defined at three levels:[1]

1. **Unit-level** (functions, components)
   - Traditional tests in `tests/` and related modules.

2. **Integration-level** (runtime flows)
   - Tests that exercise planner + task service + memory + tools.[1]

3. **End-to-end** (user-visible flows)
   - Tests that mimic real interactions, e.g. via Telegram or API, validating outcomes and observability.[1][2]

### 4.2 Minimum eval coverage

A capability is not considered production-ready unless:
- it has at least one end-to-end scenario in an eval or smoke suite;[1]
- its events and episodes carry enough metadata to debug failures;[1]
- it can be inspected via existing scripts (e.g. `inspect_eval`, `inspect_task`, `list_bad_tasks`);[1]
- negative-path behaviour is defined for at least one failure mode or refusal path.[1]

### 4.3 Capability readiness gate

A capability may be called **experimental**, **beta**, or **production-ready** only by the following rules:

| Readiness | Minimum requirements |
|---|---|
| Experimental | Basic implementation exists; traces may be incomplete; no deploy dependency is allowed. |
| Beta | Observability exists, at least one smoke path exists, failure modes are partially understood. |
| Production-ready | Full task/trace/workspace correlation, smoke coverage, eval path, incident playbook, cost visibility, and code ownership are all in place.[1] |

This gate is especially important for internet access, repo ingestion, agent execution, and skill acquisition because those capabilities increase both leverage and operational risk.[1][2]

### 4.4 Smoke checklist

For each deploy, a minimal smoke run must validate:[1]

- **Core runtime**
  - A simple user request produces a task, gets a response, and logs a trace.

- **Memory**
  - User and assistant episodes are written with correct workspace and IDs.

- **Observability**
  - `task_completed` and `task_failed` events appear with correct metadata.

- **Governance**
  - Dangerous delete, leak, and data exfiltration patterns trigger refusals and events.[1]

- **Eval path**
  - At least one eval scenario runs and records a result via the evaluator.[1]

- **Budget path**
  - Budget warning logic can be observed and does not break user-facing execution.[1]

Existing `docs/observability-smoke-checklist.md` can be treated as a detailed appendix to this section.[1]

## 5. Cost and budget control

### 5.1 Metrics

PITH must track, at minimum:[1][2]

- tokens per request (prompt and completion);
- cost per request and per workflow;
- aggregate cost per workspace and per channel;
- latency per task and per interface;
- model distribution by workflow type;
- failure rate by model and by capability.[1]

### 5.2 Budget policies

Budget policies should include:

- **Warning thresholds**
  - When daily or monthly usage approaches a configured limit, the system should surface budget warnings to users or operators.[1]

- **Degradation strategies**
  - Use cheaper models or modes for low-priority tasks.
  - Reduce context length where safe.
  - Disable non-essential tools when budgets are exceeded.
  - Prefer cached, local, or previously retrieved context when quality risk is low.

- **Monitoring and alerts**
  - Alerts when cost or token usage spikes unexpectedly.
  - Alerts when latency or failure rates exceed thresholds.[1][2]

### 5.3 Cost review cadence

The system should have a recurring review loop:
- daily review for obvious spikes or failures in active development periods;
- weekly review of cost by interface, capability, and workspace;
- monthly review of model policy, retries, context sizes, and heavy workflows.

## 6. Operational discipline

### 6.1 Deploy process

A deploy to any user-facing environment must include:[1]

- passing unit and integration tests;
- passing smoke checks for core capabilities;
- verification that new or changed capabilities have observability and eval hooks;
- clear rollback path for interface-facing changes;
- release note or changelog entry when user-visible behaviour changes.

### 6.2 Incident handling

For incidents (errors, regressions, runaway cost):[1]

- reproduce via trace IDs and episodes;
- identify which capability failed (task orchestration, memory, tools, governance, etc.);
- classify the failure (`runtime`, `tool`, `governance`, `cost`, `memory`, `interface`, `model`);
- add or update eval cases to cover this scenario in the future.

### 6.3 Postmortem minimum

A postmortem is required for severe incidents and should include:
- what happened;
- affected interfaces and workspaces;
- relevant task IDs and trace IDs;
- root cause;
- missing signal that should have caught it earlier;
- concrete follow-up in code, eval, or observability.

### 6.4 Capability lifecycle

Every capability in `PITH_CAPABILITIES_MODEL.md` should have:
- a clear owner in the codebase;
- documented observability points;
- documented eval scenarios;
- an entry in the master plan when major changes are planned;[1][2][3]
- a defined readiness state (`experimental`, `beta`, `production-ready`).

## 7. Ownership and change governance

Every meaningful subsystem should answer four questions before it is expanded:

1. Who owns the code?
2. Who operates it in production?
3. How is it observed?
4. How is it evaluated?

If one of these questions is unanswered, the subsystem should not be treated as production-ready.

For larger changes, pull requests or planning docs should explicitly state:
- affected capabilities;
- affected interfaces;
- expected new events/metrics;
- expected eval additions;
- cost impact assumptions.

## 8. Relationship to other documents

This operating standard sits beside the system vision and capability model:[1][3]

- `PITH_SYSTEM_VISION.md` defines what PITH is becoming as a system and product.
- `PITH_CAPABILITIES_MODEL.md` defines the capability inventory and contracts.
- `PITH_OPERATING_STANDARD.md` defines how those capabilities must behave in production.
- `PITH_MASTER_PLAN.md` should reference this standard when planning work that affects observability, eval, or cost.
- `docs/observability-smoke-checklist.md` should act as the concrete deploy checklist derived from this document.[1]

## 9. Immediate repo alignment

The most useful next repo steps are:
- link this document from `README.md` and `PITH_MASTER_PLAN.md`;
- align smoke scripts and inspect scripts to the sections above;[1]
- tag current capabilities by readiness state;
- attach ownership and observability requirements to every major new subsystem.