# Pith Evaluation v1

> Evaluation architecture for Pith v5 as a runtime-native, continuity-aware, multi-agent operating system.

---

## 1. Purpose

Pith Evaluation v1 defines how Pith should measure quality, reliability, usefulness, safety, and business effectiveness across runtime workflows.

Evaluation in Pith is not limited to model output scoring.
It must cover:

- end-to-end workflow success,
- planner and orchestrator behavior,
- memory usefulness,
- tool correctness,
- human review outcomes,
- cost-quality tradeoffs,
- regression over time,
- department-level business outcomes.

This document exists because a system that "runs" is not necessarily a system that works well.

Evaluation is a **first‑class runtime concern** and is built on top of observability traces and events, not as a separate analytics afterthought.

---

## 2. Why Evaluation Is Required

Pith is designed for:

- long-running cognitive work,
- continuity across sessions and tasks,
- governed evolution,
- multi-agent workflows,
- department-oriented execution,
- monetizable outcomes.

In such a system, failure may appear even when nothing crashes.

Examples:

- the planner chooses the wrong mode,
- the orchestrator finishes but the workflow is low-quality,
- the tool call succeeds but the business outcome is wrong,
- memory retrieval happens but is irrelevant or harmful,
- the agent completes the task but at unacceptable cost,
- the department appears productive but requires too much human correction.

Therefore, evaluation must be treated as part of architecture, not as an optional analytics layer.

---

## 3. Evaluation Principles

### 3.1 Workflow-first

Pith must evaluate complete workflows, not only single responses or isolated tool calls.

### 3.2 Multi-layer scoring

Evaluation must cover:

- output quality,
- trajectory quality,
- operational quality,
- business usefulness,
- safety and governance compliance.

### 3.3 Continuous, not one-time

Evaluation must happen:

- before release,
- during runtime operation (online signals),
- after workflow completion (post-review),
- after incidents and regressions (regression tests).

### 3.4 Human-calibrated

Automated scoring is necessary but insufficient.
Critical workflows must include human feedback and correction signals.

### 3.5 Runtime-grounded

Evaluation should use real runtime traces and events from Observability v1, not abstract benchmark-only assumptions.

### 3.6 Improvement-oriented

Evaluation exists not only to score, but to drive:

- patching,
- policy tuning,
- prompt/tool revisions,
- routing updates,
- memory adjustments,
- evolution decisions.

### 3.7 Two primary health indicators

Across all workflows, the **two primary health indicators** are:

- `task_completion_rate` (success vs partial vs failure),
- `human_override_rate` (how often humans must correct or redo work).

All other metrics should be interpretable in the context of these two.

---

## 4. Core Evaluation Surfaces

Pith Evaluation v1 should operate across five main surfaces.

### 4.1 Outcome Evaluation

Did the workflow produce a usable result?

Examples:

- was the task completed,
- was the output accepted,
- did the user or operator approve it,
- did the workflow create the expected artifact or business outcome.

### 4.2 Trajectory Evaluation

Did the system behave correctly while producing the result?

Examples:

- was the plan coherent,
- were handoffs reasonable,
- did the workflow follow the intended route,
- was the chosen tool path appropriate,
- were retries excessive.

### 4.3 Operational Evaluation

Was the workflow operationally healthy?

Examples:

- latency,
- token usage,
- tool latency,
- retries,
- error rate,
- cost per completion.

### 4.4 Memory Evaluation

Did memory actually help?

Examples:

- was retrieved memory relevant,
- did it improve output quality,
- did it cause contradiction or stale behavior,
- was workspace scope respected,
- was memory write quality acceptable.

### 4.5 Governance Evaluation

Did the workflow remain within policy?

Examples:

- were approval gates triggered when required,
- were forbidden actions blocked,
- was autonomy level (Tier 0–4) respected,
- were risk thresholds exceeded.

---

## 5. Core Evaluation Dimensions

Pith should converge on a stable set of evaluation dimensions.

### 5.1 Task Success

The most important question:
Did the system complete the task in a usable way?

Suggested values:

- `success`
- `partial_success`
- `failure`
- `rejected_after_review`

Task success labels should be attached to workflows/tasks in the trace store for later analysis and regression.

### 5.2 Human Override Rate

How often does a human need to intervene, correct, or replace the result?

This is one of the strongest indicators that the system is not yet trustworthy or cost-effective.

### 5.3 Quality Score

A structured quality score should measure:

- accuracy,
- completeness,
- groundedness,
- coherence,
- usefulness.

The exact rubric may vary by workflow type.
Quality scores can be produced by models and/or humans, but must be explainable.

### 5.4 Cost Efficiency

A workflow is not healthy if it succeeds at unreasonable cost.

Evaluation should compare:

- value delivered,
- tokens consumed,
- tools used,
- time spent,
- final business outcome.

Cost efficiency metrics should be computed using the same cost telemetry as Observability v1.

### 5.5 Reliability

Reliability includes:

- repeatability,
- low failure rates,
- low variance on similar tasks,
- acceptable recovery behavior.

### 5.6 Safety / Policy Adherence

Evaluation should capture whether the workflow stayed within declared boundaries:

- policy violations,
- autonomy overreach,
- missing approvals,
- risky tool usage.

### 5.7 EvaluationRecord v1 Contract

For v1, every evaluated task/workflow must produce a structured `EvaluationRecord`. It may be stored as a dedicated table or as a structured JSON blob attached to tasks/workflows (e.g., in `task_traces` or `memory episodes`).

**Identity:**
- `trace_id` (must resolve to a single trace in TraceStore)
- `task_id`
- `workspace_id`
- `workflow_type` / `task_type`

**Core Dimensions:**
- `task_success` (`success` / `partial_success` / `failure` / `rejected_after_review`)
- `human_override` (`none` / `minor_correction` / `major_rework`)
- `quality_score` (0.0–1.0 or 1–5, linked to `rubric_version`)
- `cost_per_workflow` (pulled from Observability)
- `policy_violation` (bool) + `failure_class` (if applicable)
- `autonomy_tier` (current execution tier, e.g. `Tier 2`)
- `requested_autonomy_tier` (tier requested by agent/task)

**Metadata:**
- `eval_source` (`human` / `model` / `mixed`)
- `eval_version` (rubric/prompt/model ID)
- `created_at`

> **Traceability Rule:** Any `EvaluationRecord` must be resolvable to a single trace in `TraceStore` via `trace_id` and `task_id`. Evaluation must not introduce independent primary keys without linking them back to the runtime trace.

> **Envelope Linkage:**
> EvaluationRecord v1 должен быть восстановим из комбинации:
> - trace events из `TraceStore`,
> - snapshot'а runtime‑envelope для задачи (`PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`).
>
> Минимальные связи:
> - governance‑сигналы (`policy_id`, `autonomy_tier`, `approval_state`) → из `governance` блока envelope,
> - artifact‑ссылки и business outcomes → из `artifacts` и department‑level контекстов,
> - billing‑поля (`billing_unit`, `billing_context`, `runtime_cost_estimate`) → из `billing` блока.
>
> EvaluationRecord не дублирует весь envelope, но содержит достаточно ссылок, чтобы по `trace_id` и `task_id` можно было поднять соответствующий envelope‑snapshot и воспроизвести контекст решения.

---

## 6. Evaluation Layers

Pith should use three evaluation layers.

### 6.1 Offline Evaluation

Used before release and for known scenarios.

Includes:

- curated benchmark tasks,
- regression suites,
- edge-case tests,
- prompt/model comparison,
- route comparison.

Use this layer when validating:

- planner changes,
- orchestrator changes,
- memory policy changes,
- critical tool integrations.

Offline evaluation can run against recorded traces (replay) or synthetic tasks, but should reuse the same evaluation dimensions and metrics.

### 6.2 Online Production Signals

Used during real operation.

Includes signals derived from runtime traces:

- task completion rate (success/partial/failure),
- human override / rejection rate,
- latency,
- cost per workflow,
- retry count,
- approval frequency,
- failure taxonomy rates,
- incident rate,
- operator review outcomes.

> **Observability Linkage:** All evaluation metrics in v1 must be derivable from `TraceStore` fields and event families defined in `PITH_OBSERVABILITY_V1.md` (Core Runtime, Planner/Orchestrator, Tool/Memory, Governance, Artifact, Billing). Any `EvaluationRecord` must reference at minimum: `trace_id`, `task_id`, `workspace_id`, `runtime_mode`, `task_type`, `failure_class`, and `cost_estimate_usd`.

### 6.3 Post-Workflow Review

Used after important workflow completion.

Includes:

- artifact review,
- business outcome validation,
- sampled human scoring,
- incident-linked evaluation,
- regression creation from real failures.

Real failures should become future evaluation cases and regression tests.

---

## 7. Evaluation Objects

Pith should evaluate multiple object types, not only final answers.

### 7.1 Final Outputs

Examples:

- report,
- campaign pack,
- lead list,
- research brief,
- code artifact,
- response to user.

### 7.2 Workflow Trajectories

Examples:

- plan quality,
- route quality,
- handoff logic,
- retry discipline,
- escalation correctness.

### 7.3 Tool Actions

Examples:

- correct tool chosen,
- correct arguments passed,
- result handled properly,
- no policy violation.

### 7.4 Memory Events

Examples:

- correct retrieval scope,
- relevant memory returned,
- write quality,
- contradiction risk,
- stale memory risk.

### 7.5 Department Outcomes

Examples:

- qualified leads produced,
- campaign package delivered,
- competitor matrix generated,
- support case resolved.

Department-level evaluation should align with billable outcomes from `PITH_AGENT_COMPANY_V1.md`.

---

## 8. Department-Level Evaluation

Because Pith is becoming an Agent Company OS, evaluation must also work at department level. All department evaluations share a common core schema, with vertical-specific signals layered on top.

### 8.0 Department-Agnostic Core Schema
- `department_type` (e.g., `sales`, `marketing`, `research`)
- `business_outcome_type` (e.g., `qualified_lead`, `campaign_pack`, `research_brief`)
- `business_outcome_success` (`yes` / `no` / `partial`)
- `business_outcome_value` (optional numeric metric)
- `human_approval` / `customer_success` flags

### 8.1 Sales Department
Possible signals (extending the core schema):

- qualified lead quality,
- meeting-booking rate,
- outreach acceptance quality,
- CRM correctness,
- cost per qualified lead.

### 8.2 Marketing Department
Possible signals (extending the core schema):

- campaign readiness,
- copy quality,
- asset completeness,
- channel alignment,
- report usefulness,
- cost per campaign.

### 8.3 Research Department
Possible signals (extending the core schema):

- factual reliability,
- coverage,
- source quality,
- decision usefulness.

### 8.4 Delivery Department
Possible signals (extending the core schema):

- artifact completeness,
- specification clarity,
- readiness for execution,
- defect/clarification rate.

### 8.5 Support / Ops Department
Possible signals (extending the core schema):

- resolution correctness,
- escalation quality,
- audit usefulness,
- billing accuracy.

---

## 9. Memory Evaluation

Pith must evaluate memory as a real subsystem, not as a background convenience.

Memory evaluation should include:

- retrieval relevance,
- retrieval precision and recall (for tasks where this is measurable),
- retrieval usefulness,
- contradiction detection,
- stale-memory detection,
- workspace-boundary correctness,
- long-term write value,
- memory-induced failure cases.

Important principle:
a memory hit is not automatically a good memory hit.

Evaluation should explicitly tag workflows where memory helped vs harmed, based on human or model judgment.

---

## 10. Evaluation Signals

Pith should combine four types of evaluation signals.

### 10.1 Deterministic Signals

Examples:

- schema validation,
- artifact existence,
- policy match,
- required fields present,
- workflow status consistency.

### 10.2 Model-based Signals

Examples:

- rubric scoring,
- groundedness judgment,
- summary quality,
- plan quality.

These should be explicit and inspectable; prompts and scoring scales must be versioned.

### 10.3 Human Signals

Examples:

- approval,
- correction,
- rejection,
- annotation,
- operator rating.

Human feedback is particularly important for high-value workflows and new verticals.

### 10.4 Business Signals

Examples:

- lead accepted,
- campaign used,
- artifact delivered,
- customer satisfied,
- support case resolved,
- workflow monetized successfully.

These signals close the loop between runtime behavior and real business outcomes.

---

## 11. Regression Philosophy

Every meaningful production failure should be considered a candidate regression test.

This means:

- incidents become future eval cases,
- bad outputs become rubric examples,
- broken traces become route tests,
- failed memory behavior becomes retrieval tests,
- policy mistakes become governance checks.

Pith should become harder to break over time because failures feed the evaluation loop.

A small set of **golden workflows** should be kept as canaries and run regularly to detect regressions in planner/orchestrator/prompt/model behavior.

---

## 12. Evaluation and Evolution

Evaluation is one of the foundations of governed evolution.

Pith should not "learn" or expand autonomy based only on intuition.
It should use evaluation evidence such as:

- quality improvement over time,
- stable success rate,
- reduced human override rate,
- better cost efficiency,
- lower policy violation risk.

Evolution proposals (changes to prompts, tools, routing, memory, policies) should reference evaluation data, not only narrative arguments.

No claimed evolution is valid unless it improves measurable behavior.

---

## 13. Minimum v1 Metrics

Pith Evaluation v1 should at minimum track:

- task completion rate (success/partial/failure),
- partial completion rate,
- failure rate by taxonomy,
- human override rate,
- human approval rate,
- average latency per workflow,
- p95 latency,
- cost per workflow,
- cost per successful workflow,
- retry count,
- sampled quality score,
- policy violation rate,
- memory usefulness score (sampled),
- department outcome rate (e.g. qualified leads, campaigns, briefs).

These metrics can start simple, but they must exist and be derived from trace data.

---

## 14. v1 Implementation Priorities

Start with:

1. A stable evaluation vocabulary (task success states, quality rubric, failure taxonomy).
2. Task success / partial success / failure states stored with workflows/tasks.
3. Human review capture for priority workflows.
4. Sampled quality scoring (model- and human-based).
5. Cost-quality correlation (cost per successful workflow).
6. Regression case collection from real failures.

Do not overbuild a perfect evaluation platform before the runtime emits stable traces and outcomes (see `PITH_OBSERVABILITY_V1.md`).

> **Current v1 Implementation Pattern:** For single-task flows, evaluation results are stored as `eval` metadata on the assistant episode via `memory.save_episode(..., metadata={"eval": ...})`. This blob must conform to the `EvaluationRecord v1` structure and explicitly include `task_id` and `trace_id` to maintain end-to-end traceability.

---

## 14a. Eval Ops v1 Implementation (Runtime)

На момент v5.2 базовый eval-цикл реализован в виде golden-наборов и smoke gate.

**Текущее состояние (v5.2):**

1. **`scripts/run_golden.py`** — выполняет валидацию golden YAML по JSON-схеме и генерирует заглушку `EvaluationRecord v1` через `fake_evaluation_record()`. Реальный runtime (RuntimePlanner, Router, TaskService, Evaluator) **не вызывается**. Результат сохраняется в `output/eval_runs/*.json`.

2. **`scripts/run_single_golden_runtime.py`** — новый, экспериментальный runtime-path. Вызывает реальный LLM через `core.cognition.router.call_llm()`, прогоняет ответ через `core.evolution.evaluator.Evaluator.evaluate_response()`, формирует полный `EvaluationRecord v1` с метаданными (модель, cost, токены). Результат сохраняется в `output/eval_runs/*.json` (совместимый формат).  
   *Ограничения Phase 1:* не использует RuntimePlanner, trace_id/task_id генерируются локально, initial_context передаётся как system_prompt, а не через Memory.

3. **`scripts/eval_smoke_summary.py`** — агрегирует результаты из `output/eval_runs/*.json` и применяет простые правила: `task_success == "success"`, `policy_violation == False`, `quality_score ≥ threshold`. Работает с обоими источниками (заглушки и реальные записи).

4. **`make eval-smoke-gate`** (`eval-smoke` + `eval-smoke-summary`) — текущий минимальный quality gate. Проверяет заглушки, а не реальный runtime.

**План перехода к runtime-native eval:**
- Замена `fake_evaluation_record()` на реальный вызов RuntimePlanner с интеграцией TaskService, TraceStore и Evaluator запланирована на v5.3.
- Golden workflows лежат в `eval/golden/*.yaml` и валидируются схемой `eval/golden/golden_workflow_schema.json`.

Eval Ops v1 специально начинается с небольшой, но операциональной поверхности, которая
может эволюционировать в более полный EvaluationRun/RegressionRun-пайплайн.

---

## 15. Out of Scope for v1

Not required immediately:

- universal benchmark dominance,
- full automated grading for every workflow,
- perfect agent simulation,
- deeply adaptive auto-tuning,
- zero-human-review operation.

The v1 goal is disciplined measurement, not evaluation perfection.

---

## 15a. Golden Eval Trace Inspection

For golden runtime evaluations executed via `scripts/run_single_golden_runtime.py --via-planner`, every run is persisted into `episodes.db` (`tasks` + `task_traces`).

A small CLI helper is available:

```bash
# list recent golden tasks
python scripts/inspect_golden_traces.py tasks --limit 5

# list recent golden traces
python scripts/inspect_golden_traces.py traces --limit 5

# inspect all runs for a specific golden
python scripts/inspect_golden_traces.py golden --golden-id support_ops_faq_v1

# inspect a run by trace_id
python scripts/inspect_golden_traces.py trace --trace-id TRACE_support_ops_faq_v1_ae846f881426
```

This makes it easy to correlate evaluation JSON blobs with TaskStore (`tasks`) and TraceStore (`task_traces`), and to verify that `runtime_mode=eval`, `task_type=golden_runtime`, and `quality_score` are set end-to-end.

---

## 16. Integration Points

This document should influence:

- `docs/PITH_OBSERVABILITY_V1.md`
- `docs/PITH_GOVERNANCE_V1.md`
- `docs/PITH_AGENT_COMPANY_V1.md`
- `docs/EVOLUTION.md`
- planner/orchestrator contracts
- execution result schemas
- operator review flows
- future regression tooling

Pith should not scale autonomy, monetization, or department complexity without an evaluation layer strong enough to detect quality drift and operational regression.

---

<div style="text-align: center; margin-top: 40px; color: #666;">

**Pith Lab · Москва · 2026**

*Версия v1.1.2 · Май 2026 · CONFIDENTIAL / INTERNAL*

</div>