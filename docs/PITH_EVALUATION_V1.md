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

This document exists because a system that “runs” is not necessarily a system that works well.[web:2095]

Evaluation is a **first‑class runtime concern** and is built on top of observability traces and events, not as a separate analytics afterthought.[web:2079][web:2087]

---

## 2. Why Evaluation Is Required

Pith is designed for:

- long-running cognitive work,
- continuity across sessions and tasks,
- governed evolution,
- multi-agent workflows,
- department-oriented execution,
- monetizable outcomes.

In such a system, failure may appear even when nothing crashes.[web:2092]

Examples:

- the planner chooses the wrong mode,
- the orchestrator finishes but the workflow is low-quality,
- the tool call succeeds but the business outcome is wrong,
- memory retrieval happens but is irrelevant or harmful,
- the agent completes the task but at unacceptable cost,
- the department appears productive but requires too much human correction.

Therefore, evaluation must be treated as part of architecture, not as an optional analytics layer.[web:2094][web:2102]

---

## 3. Evaluation Principles

### 3.1 Workflow-first

Pith must evaluate complete workflows, not only single responses or isolated tool calls.[web:2096]

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

Evaluation should use real runtime traces and events from Observability v1, not abstract benchmark-only assumptions.[web:2079][web:2082]

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
- `human_override_rate` (how often humans must correct or redo work).[web:2092][web:2097]

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
- was autonomy level (L0–L3) respected,
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

Task success labels should be attached to workflows/tasks in the trace store for later analysis and regression.[web:2096][web:2102]

### 5.2 Human Override Rate

How often does a human need to intervene, correct, or replace the result?

This is one of the strongest indicators that the system is not yet trustworthy or cost-effective.[web:2092][web:2097]

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

Cost efficiency metrics should be computed using the same cost telemetry as Observability v1.[web:2086][web:2100]

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

Offline evaluation can run against recorded traces (replay) or synthetic tasks, but should reuse the same evaluation dimensions and metrics.[web:2096][web:2102]

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

This is the main health layer for production.
All signals must be attributable by `tenant`, `workspace`, `department`, and `workflow_type`.[web:2097]

### 6.3 Post-Workflow Review

Used after important workflow completion.

Includes:

- artifact review,
- business outcome validation,
- sampled human scoring,
- incident-linked evaluation,
- regression creation from real failures.

Real failures should become future evaluation cases and regression tests.[web:2095][web:2101]

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

Department-level evaluation should align with billable outcomes from `PITH_AGENT_COMPANY_V1.md`.[web:2097]

---

## 8. Department-Level Evaluation

Because Pith is becoming an Agent Company OS, evaluation must also work at department level.[web:2094][web:2097]

### 8.1 Sales Department

Possible signals:

- qualified lead quality,
- meeting-booking rate,
- outreach acceptance quality,
- CRM correctness,
- cost per qualified lead.

### 8.2 Marketing Department

Possible signals:

- campaign readiness,
- copy quality,
- asset completeness,
- channel alignment,
- report usefulness,
- cost per campaign.

### 8.3 Research Department

Possible signals:

- factual reliability,
- coverage,
- source quality,
- decision usefulness.

### 8.4 Delivery Department

Possible signals:

- artifact completeness,
- specification clarity,
- readiness for execution,
- defect/clarification rate.

### 8.5 Support / Ops Department

Possible signals:

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

Evaluation should explicitly tag workflows where memory helped vs harmed, based on human or model judgment.[web:2096][web:2102]

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

These signals close the loop between runtime behavior and real business outcomes.[web:2097][web:2100]

---

## 11. Regression Philosophy

Every meaningful production failure should be considered a candidate regression test.[web:2095][web:2101]

This means:

- incidents become future eval cases,
- bad outputs become rubric examples,
- broken traces become route tests,
- failed memory behavior becomes retrieval tests,
- policy mistakes become governance checks.

Pith should become harder to break over time because failures feed the evaluation loop.

A small set of **golden workflows** should be kept as canaries and run regularly to detect regressions in planner/orchestrator/prompt/model behavior.[web:2096][web:2098]

---

## 12. Evaluation and Evolution

Evaluation is one of the foundations of governed evolution.

Pith should not “learn” or expand autonomy based only on intuition.
It should use evaluation evidence such as:

- quality improvement over time,
- stable success rate,
- reduced human override rate,
- better cost efficiency,
- lower policy violation risk.

Evolution proposals (changes to prompts, tools, routing, memory, policies) should reference evaluation data, not only narrative arguments.[web:2092][web:2102]

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

These metrics can start simple, but they must exist and be derived from trace data.[web:2097][web:2100]

---

## 14. v1 Implementation Priorities

Start with:

1. A stable evaluation vocabulary (task success states, quality rubric, failure taxonomy).
2. Task success / partial success / failure states stored with workflows/tasks.
3. Human review capture for priority workflows.
4. Sampled quality scoring (model- and human-based).
5. Cost-quality correlation (cost per successful workflow).
6. Regression case collection from real failures.

Do not overbuild a perfect evaluation platform before the runtime emits stable traces and outcomes (see `PITH_OBSERVABILITY_V1.md`).[web:2079][web:2082]

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

Pith should not scale autonomy, monetization, or department complexity without an evaluation layer strong enough to detect quality drift and operational regression.[web:2092][web:2097][web:2102]