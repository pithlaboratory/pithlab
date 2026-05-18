# PITH_EVAL_OPS_V1

> Operational evaluation framework for Pith v5: how evaluation runs are scheduled, executed, reviewed, and used to gate runtime changes, releases, and autonomy expansion.

---

## 1. Purpose

PITH_EVAL_OPS_V1 defines the operational layer that sits on top of `PITH_EVALUATION_V1.md`.

If `PITH_EVALUATION_V1.md` defines **what** Pith evaluates, this document defines **how evaluation is run in practice** across releases, regressions, incidents, and department autonomy changes.

The purpose of Eval Ops is to ensure that evaluation is not informal or optional.
It must function as a repeatable operating discipline for runtime quality control.

---

## 2. Why Eval Ops Exists

A stable evaluation contract is not sufficient on its own.

Pith also needs an operational system that determines:

- which workflows are evaluated,
- when evaluations run,
- which metrics block releases,
- how failures are converted into future regression cases,
- how autonomy tier changes are approved or rejected,
- how department-level quality drift is detected early.

Without Eval Ops, evaluation remains descriptive rather than operational.

---

## 3. Eval Ops Principles

### 3.1 Runtime-native

Eval Ops must operate on the same runtime objects used by the system itself:

- `trace_id`
- `task_id`
- `workspace_id`
- runtime envelope snapshots
- trace events from `TraceStore`

Eval Ops must not depend on disconnected benchmark-only abstractions.

### 3.2 Trace-linked

Every evaluation run must be traceable back to the runtime evidence that produced it.

This means:

- every evaluated case must resolve to one or more traces,
- every run summary must be reproducible from stored records,
- all blocking decisions must be explainable from trace-linked evidence.

### 3.3 Regression-driven

Real failures are the most valuable source of future evaluation cases.

Incidents, rejected outputs, costly failures, autonomy overreach, policy misses, and memory mistakes should be converted into future regression assets.

### 3.4 Gate-oriented

Evaluation is not only for dashboards.
It must also control decisions.

Eval Ops should be used to gate:

- planner/orchestrator changes,
- prompt and model changes,
- policy changes,
- memory policy changes,
- tool integration changes,
- department autonomy expansion.

### 3.5 Tier-aware

Eval Ops must explicitly account for autonomy tier (`Tier 0–4`).

A workflow that is acceptable at a lower tier may be unacceptable at a higher one if it increases risk, policy surface, or business exposure.

---

## 4. Evaluation Run Types

Pith Eval Ops v1 should support four primary run types.

### 4.1 Smoke Runs

Smoke runs are small, fast evaluation runs over a stable set of high-signal workflows.

Their purpose is to detect obvious regressions quickly after changes to:

- prompts,
- routing,
- planner behavior,
- orchestrator behavior,
- tool integrations,
- memory behavior.

Smoke runs should complete quickly and run frequently.

### 4.2 Regression Runs

Regression runs are broader and deeper than smoke runs.

They should include:

- golden workflows,
- past incident cases,
- historically fragile cases,
- edge cases,
- governance-sensitive tasks,
- high-cost workflows,
- department-critical business tasks.

Regression runs are the default validation layer before significant runtime changes are accepted.

### 4.3 Canary Evaluation Runs

Canary runs operate on a sampled subset of real production workflows.

Their purpose is to detect real-world drift that may not appear in curated datasets.

Canary evaluation may include:

- sampled human review,
- model-based quality scoring,
- business outcome validation,
- policy adherence checks,
- cost drift monitoring.

### 4.4 Incident Review Runs

Every meaningful production incident should trigger a dedicated evaluation run.

This run should:

- reconstruct the trace and envelope context,
- classify the failure,
- determine whether the issue was planning, tooling, memory, policy, cost, or business-outcome related,
- create one or more future regression cases,
- update the relevant evaluation datasets.

---

## 5. Evaluation Assets

Eval Ops should operate on explicit evaluation assets.

### 5.1 Golden Workflows

Golden workflows are stable, representative, high-value workflows used as canaries.

They should be:

- small enough to run frequently,
- important enough to matter,
- stable enough to compare over time,
- broad enough to cover major runtime surfaces.

Golden workflows should exist across core departments and critical workflow types.

### 5.2 Regression Cases

Regression cases are individual failure-informed or risk-informed tasks.

Sources include:

- production incidents,
- human rejections,
- policy failures,
- memory-induced failures,
- excessive-cost workflows,
- broken artifacts,
- route/path failures.

### 5.3 Evaluation Datasets

An evaluation dataset is a managed collection of cases used for a run.

A dataset may be defined by:

- explicit case IDs,
- trace filters,
- department + workflow type filters,
- incident-derived bundles,
- tier-specific governance cases.

Each dataset should be versioned.

### 5.4 Rubrics

Rubrics define how quality is scored.

Each rubric must be versioned and linked to:

- workflow type,
- department context,
- evaluation prompt or scoring logic,
- allowed score range,
- interpretation guide.

---

## 6. EvaluationRun v1

Every Eval Ops execution should produce an `EvaluationRun` record.

### 6.1 Minimum fields

- `run_id`
- `run_type` (`smoke` / `regression` / `canary` / `incident`)
- `run_status` (`started` / `completed` / `failed` / `blocked`)
- `started_at`
- `completed_at`
- `eval_version`
- `dataset_id` or `trace_selection_rule`
- `trigger_type` (`scheduled` / `release_candidate` / `manual` / `incident`)
- `trigger_ref` (commit SHA, incident ID, release ID, policy change ID, etc.)
- `scope` (`global` / `department` / `workflow_type` / `tier`)
- `summary_metrics`
- `decision` (`approved` / `rejected` / `needs_investigation`)
- `decision_reason`

### 6.2 Traceability rule

Every `EvaluationRun` must be reproducible from:

- the dataset or trace selection rule,
- the evaluation version,
- the rubric version(s),
- the underlying trace-linked `EvaluationRecord` set.

An Eval Ops run is invalid if its decision cannot be reconstructed from stored evidence.

---

## 7. Data Flow

Eval Ops v1 should follow a simple, repeatable pipeline.

### 7.1 Select cases

Cases are selected from one of the following:

- a fixed golden dataset,
- a regression dataset,
- a production canary sampling rule,
- an incident-derived trace set.

### 7.2 Resolve runtime evidence

For each case, the system resolves:

- trace events from `TraceStore`,
- the relevant runtime envelope snapshot,
- governance context,
- artifact context,
- billing context,
- task/workflow metadata.

### 7.3 Execute evaluation

Evaluation may combine:

- deterministic checks,
- model-based scoring,
- human review,
- business outcome checks.

### 7.4 Write EvaluationRecord v1

Each evaluated task/workflow writes or updates a structured `EvaluationRecord` linked to:

- `trace_id`
- `task_id`
- `workspace_id`

### 7.5 Aggregate and decide

The run produces aggregate metrics, compares them to baseline, and emits a final decision.

---

## 8. Metrics in Eval Ops

Eval Ops should center around a small set of decision-grade metrics.

### 8.1 Core health metrics

The primary metrics are:

- `task_completion_rate`
- `human_override_rate`

All run summaries should report these first.

### 8.2 Quality and reliability metrics

Additional metrics should include:

- sampled quality score,
- failure rate by taxonomy,
- retry rate,
- incident-linked failure recurrence,
- output rejection rate,
- approval pass rate.

### 8.3 Cost metrics

Eval Ops should also track:

- cost per workflow,
- cost per successful workflow,
- p95 cost for important workflow types,
- cost drift versus baseline,
- high-cost anomaly rate.

### 8.4 Governance metrics

Governance-sensitive runs should track:

- policy violation rate,
- missing approval rate,
- approval escalation rate,
- autonomy overreach rate,
- approval rejection rate.

### 8.5 Artifact and business metrics

Where applicable, runs should also measure:

- artifact creation success,
- artifact completeness,
- business outcome success rate,
- department-specific outcome value,
- downstream artifact usage.

---

## 9. Quality Gates

Eval Ops must define explicit gates for operational decisions.

### 9.1 Release gates

A release candidate should be rejected if any of the following occur:

- significant degradation in `task_completion_rate`,
- significant increase in `human_override_rate`,
- material increase in policy violations,
- material regression in high-priority golden workflows,
- unacceptable increase in cost per successful workflow.

Thresholds may vary by workflow type, but they must be declared in advance.

### 9.2 Autonomy tier gates

A department or workflow should not move to a higher autonomy tier unless evaluation evidence shows:

- stable completion behavior,
- low human override rate,
- low policy violation rate,
- acceptable cost efficiency,
- no unresolved critical failure classes,
- acceptable performance on governance-sensitive cases.

### 9.3 Incident gates

After a serious incident, the affected workflow class should not be considered healthy again until:

- the incident is classified,
- one or more regression cases are created,
- the new regression cases pass,
- the underlying change is validated in a dedicated run.

---

## 10. Operational Cadence

Eval Ops v1 should run on a predictable cadence.

### 10.1 Daily

- smoke runs on golden workflows,
- dashboard refresh for core health metrics,
- review of policy and failure-rate anomalies.

### 10.2 Per change

Run smoke and targeted regression checks for:

- planner changes,
- orchestrator changes,
- prompt/model changes,
- memory policy changes,
- critical tool changes,
- governance policy changes.

### 10.3 Weekly

- broader regression suite,
- department-level metric review,
- review of high-cost traces,
- review of human override clusters,
- review of canary outcomes.

### 10.4 Per incident

- incident reconstruction,
- incident-linked evaluation run,
- regression case creation,
- rubric or policy updates where necessary.

---

## 11. Human Roles

Eval Ops requires explicit ownership.

### 11.1 Runtime owners

Responsible for:

- planner/orchestrator quality,
- workflow stability,
- regression resolution,
- release readiness.

### 11.2 Governance owners

Responsible for:

- approval correctness,
- policy adherence,
- autonomy tier review,
- governance-sensitive regression coverage.

### 11.3 Department owners

Responsible for:

- business outcome quality,
- department-specific rubric calibration,
- review of outcome usefulness,
- approval of autonomy expansion in their domain.

### 11.4 Operators and reviewers

Responsible for:

- sampled human scoring,
- rejection tagging,
- correction labeling,
- incident annotation,
- identifying false positives and false negatives in automated evals.

---

## 12. Incident-to-Regression Loop

Eval Ops must formalize the incident learning loop.

### 12.1 Required conversion

Every meaningful incident should be evaluated for conversion into:

- a regression case,
- a golden workflow candidate,
- a rubric example,
- a policy test,
- a memory evaluation case.

### 12.2 Required metadata

Incident-derived cases should retain:

- `incident_id`
- `failure_class`
- affected department
- workflow type
- autonomy tier
- policy context
- cost impact
- business impact

### 12.3 Goal

The goal is simple:
Pith should become harder to break because its real failures become part of its permanent evaluation surface.

---

## 13. Minimum v1 Implementation Pattern

Eval Ops v1 does not require a fully mature platform on day one.

A valid first implementation may consist of:

1. versioned golden workflow lists,
2. regression datasets built from real failures,
3. an `EvaluationRun` object stored in metadata or a dedicated table,
4. `EvaluationRecord v1` linked by `trace_id` and `task_id`,
5. simple pass/fail release gates,
6. a documented incident-to-regression loop.

This is enough to make evaluation operational before the system becomes more automated.

---

## 14. Out of Scope for v1

Not required immediately:

- fully automated autonomy promotion,
- universal rubric coverage for every workflow,
- perfect causal attribution for all regressions,
- zero-human-review evaluation,
- complete simulation of all departments,
- sophisticated adaptive gate tuning.

The v1 goal is operational discipline, not platform perfection.

---

## 15. Integration Points

This document should align with:

- `docs/PITH_EVALUATION_V1.md`
- `docs/PITH_OBSERVABILITY_V1.md`
- `docs/PITH_GOVERNANCE_V1.md`
- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
- `docs/EVOLUTION.md`
- planner/orchestrator release procedures
- operator review flows
- incident review procedures
- future regression tooling

Eval Ops is the layer that turns evaluation from a design principle into a management system for runtime quality.

---

<div style="text-align: center; margin-top: 40px; color: #666;">

**Pith Lab · Москва · 2026**

*Версия v1.0 · Май 2026 · CONFIDENTIAL / INTERNAL*

</div>