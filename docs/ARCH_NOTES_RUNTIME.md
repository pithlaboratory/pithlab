# Pith v5 — Runtime Architecture Notes (Runtime Core)

Status: aligned with runtime protocol v1, Phase 1.5 cleanup  
Scope: ModelRegistry/Router → RuntimePlanner → ContextAssembler  
Sources:
- docs/PITH_ARCHITECTURE_NORTH_STAR_V2.md
- docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md
- Claude Sonnet runtime architecture review (Pith v5 – Runtime Architecture Review)


## 1. Current Runtime Core State

### 1.1 Model Plane / Router

- ModelRegistry.json acts as SSOT for models, lanes, pricing, and routing hints.
- Router is registry-first: it resolves models and pricing exclusively via ModelRegistry.
- Router owns:
  - lane selection (free / paid / premium),
  - budget and hard limit enforcement,
  - fallback behaviour when a lane/model is unavailable.
- No automatic policy updates: routing behaviour changes only via explicit registry edits and code changes.


### 1.2 RuntimePlanner

- `RuntimePlanner` is Phase 1.5:
  - heuristic task type detection (keyword-based),
  - heuristic complexity gating (simple vs complex),
  - branch selection:
    - simple → direct LLM via Router,
    - complex → orchestrator (multi-agent flow).
- `RuntimePlanner` has explicit boundaries:
  - owns execution branching only,
  - does not claim to be SSOT for task taxonomy or routing policy,
  - treats its task type mapping as Phase 1 heuristic, not a permanent contract.
- Mode alignment:
  - `RuntimeMode` from ContextAssembler (NORMAL / DIAGNOSTICS / VISION) can override/router mode in a safe, explicit way (e.g. diagnostics → coder lane).


### 1.3 ContextAssembler

- `ContextAssembler` builds layered prompt context:
  - workspace identity,
  - runtime mode instructions,
  - current request,
  - current task context,
  - compressed conversation summary,
  - relevant memory (vector search),
  - relevant artifacts/documents,
  - recent conversation (noise-filtered).
- System prompt is **not** duplicated inside the assembled prompt and is passed separately as a true system message.
- Mode-dependent behaviour:
  - NORMAL: generic memory and task artifacts.
  - DIAGNOSTICS: incident-like memory and diagnostics guidance.
  - VISION: architecture/roadmap memory and North Star stub docs.
- History and memory filters remove explicit persona/meta noise.


## 2. Confirmed Design Decisions

### 2.1 Separation of Concerns

- ModelRegistry + Router:
  - single source of truth for models, lanes, prices, and high-level routing hints,
  - responsible for budget, limits, and fallbacks.
- RuntimePlanner:
  - responsible for execution branching only (direct vs orchestrated, lane choice hints),
  - does not store canonical task taxonomy or model-level knowledge.
- ContextAssembler:
  - responsible for structured, layered context assembly,
  - observes runtime protocol ordering and does not merge system and user contexts.

### 2.2 Phase 1.5 Heuristics are Explicitly Temporary

- Task detection and complexity heuristics are:
  - documented as Phase 1,
  - marked as candidates for replacement by IntentClassifier / registry-driven routing,
  - implemented in a way that allows delegation to a future registry- or classifier-based decision function.

### 2.3 Layered Context is the Default

- Prompt assembly follows a fixed, protocol-aligned order:
  1. Workspace identity
  2. Mode instructions
  3. Current request
  4. Current task context
  5. Conversation summary
  6. Relevant memory
  7. Relevant artifacts/documents
  8. Recent conversation
- This is the canonical structure for runtime v1 and any deviation must be explicit and documented.


## 3. Runtime Risk Profile (from Claude review)

### 3.1 Priority 1 — Registry Drift / Stale Routing

Risk:
- ModelRegistry is SSOT but static.
- Providers can change model pricing, availability, and quality asynchronously.
- Without feedback and review loops, Router can keep sending traffic to degraded or more expensive models with no awareness.
- `task_routes` may point to models which are no longer optimal or acceptable by cost.

Impact:
- Silent degradation of quality and cost-efficiency at the routing layer.
- Difficult retrospectives (“why did cost spike in March?”) without versioning and metrics.

### 3.2 Priority 2 — Context Poisoning via Layered Assembly

Risk:
- Layered context (workspace → mode → task → summary → memory → artifacts → history) is built without validation.
- Different layers can introduce conflicting instructions (e.g. workspace wants concise answers, mode asks for exhaustive analysis, history shows long-form examples).
- LLM receives contradictory guidance with no explicit priority markers, making behaviour unstable and hard to reproduce.

Impact:
- Unpredictable answers, brittle behaviour, drift in style and policy enforcement.
- Harder debugging: conflicts live across multiple layers, not in one spot.

### 3.3 Priority 3 — Orchestrator Without Marginal Value Measurement

Risk:
- RuntimePlanner sends requests to orchestrator based on heuristics (length, keywords, question count).
- There is no systematic measurement of whether orchestrated paths actually outperform direct LLM calls in quality vs cost.
- Orchestrator can silently become the default for “complex” tasks and triple cost with little to no gain.

Impact:
- Potential chronic overuse of orchestrator where it does not justify its cost.
- Inability to reason about where orchestration is actually valuable.


## 4. Guardrails and Metrics (Claude Suggestions)

### 4.1 Model Plane / Router Guardrails

Recommended practices:

- Safe-gating for new models:
  - Introduce models with `dev_only: true` in the registry,
  - Send traffic only from owner/internal workspaces,
  - Observe for at least 48 hours:
    - error_rate,
    - average latency,
    - evaluator-based avg_score.

- Versioned registry updates:
  - Do not overwrite existing model entries when pricing/capabilities change,
  - Create new versions (e.g. `{model_id}_v2` with `supersedes: model_id_v1`),
  - Keep history for later “why did X change?” investigations.

- RoutingReviewJob:
  - A scheduled job produces a report, not an auto-patch:
    - top lanes/models by cost and score,
    - comparison with previous interval,
    - degradation flags (cost spike, error surge, score drop).
  - Frequency: weekly or triggered by error_rate spikes.

Useful metrics (per lane/model):

- `cost_per_useful_call` — primary economics signal.
- `error_rate` — provider degradation signal.
- `fallback_rate` — indicates when Router struggles to find a working model.
- `avg_score` — evaluator-based quality.

Non-primary at this stage:

- Latency p99.
- Raw token counts (they are derivative of cost).


### 4.2 Planner / Orchestrator Metrics

Suggested EpisodeTrace fields:

- `execution_path: "direct" | "orchestrated"`
- `agent_count`
- `steps_actual`
- `steps_planned`
- `cost_usd`
- `score_final`
- `score_context_use`
- `task_type`

Signals to monitor:

- Orchestrator wandering:
  - `steps_actual > steps_planned * 1.5`
- Orchestrator instability:
  - `error_rate(orchestrated) > 2x error_rate(direct)`
- Clear negative marginal value:
  - `avg_score(orchestrated) < avg_score(direct) - 0.05`
  - while `cost(orchestrated) > 2x cost(direct)`


### 4.3 ContextAssembler / Context Engineering

Common pitfalls identified:

- Order effects:
  - Most LLMs weight the beginning and end of the prompt more heavily.
  - Critical instructions lost in the middle (between summary and artifacts).

- Silent contradictions:
  - Conflicting instructions across workspace/mode/history/memory without explicit priorities.

- Memory flooding:
  - Vector similarity ≠ true usefulness.
  - Old/low-quality episodes pollute context.

- Persona noise:
  - Experimental personas and style tests in history/memory cause identity drift.

Layered-design-specific risk:

- Boundary between summary (session background) and memory (episodic, past tasks) can become blurry if not clearly marked, leading to confusion about what is “current” vs “background”.


## 5. Agreed Next Actions (Next 30–60 Days)

These are the concrete actions to implement next, in order.

### 5.1 Add `execution_path` and basic episode metrics

Goal:
- Make direct vs orchestrated paths measurable.

Actions:
- Extend evaluator/episodes schema with:
  - `execution_path`,
  - `cost_usd`,
  - `score_final`,
  - `score_context_use`,
  - `task_type`,
  - `steps_actual` / `steps_planned` where applicable.
- Ensure RuntimePlanner sets `execution_path` appropriately for both direct and orchestrated flows.
- After 1–2 weeks of data, analyse:
  - avg_score and cost per path,
  - whether orchestrator is worth its marginal cost on different task types.

Priority: **High (P1)**


### 5.2 Add relevance floor and token budget for memory

Goal:
- Reduce memory noise and flooding.

Actions:
- For vector search results:
  - introduce `relevance_score` threshold (e.g. ≥ 0.65),
  - enforce a maximum token budget for memory (e.g. ~800 tokens),
  - prefer “no memory” over low-signal memory.
- Keep implementation simple and cheap (no complex policies yet).

Priority: **High (P1)**


### 5.3 Introduce `ContextValidator` as post-build step

Goal:
- Make layered context assembly observable and safer.

Actions:
- Add a lightweight `ContextValidator` that runs after `ContextAssembler.build()` and before LLM call:
  - token budget check,
  - check for duplicated system-level instructions,
  - basic contradiction scan (keyword-based),
  - persona noise check in history/memory.
- On failure (`passed=False`):
  - log issues for later inspection,
  - degrade gracefully (e.g. drop noisy parts: memory/history) instead of crashing.

Priority: **Medium (P2)**


### 5.4 Explicit priority markers in prompt

Goal:
- Reduce order effects and clarify intent boundaries.

Actions:
- Add lightweight markers/titles for major sections in assembled prompt:
  - e.g. `## [CURRENT MODE INSTRUCTIONS — HIGHEST PRIORITY]`,
  - `## [CURRENT TASK]`,
  - `## [SESSION BACKGROUND — lower priority]`,
  - `## [PAST CONTEXT — background only]`, etc.
- Do **not** overcomplicate formatting: clarity over cleverness.

Priority: **Medium (P2)**


## 6. Deferred Items (Later Phases)

These are acknowledged needs, but not immediate.

### 6.1 Planner Heuristic Optimization

- Do not optimise task-type and complexity heuristics until:
  - there is meaningful data from evaluator (direct vs orchestrated),
  - routing and orchestration marginal value are measured.
- Future direction:
  - IntentClassifier,
  - registry-driven task-to-lane mapping.

### 6.2 Automatic Routing Policy Updates

- No automated policy rewrites until:
  - evaluation loop is closed,
  - routing metrics are stable and trustworthy.
- For now: keep RoutingReviewJob as a human-in-the-loop report generator.

### 6.3 Deep Registry Versioning and Migration

- Proper versioning for:
  - models,
  - pricing,
  - routing configurations.
- Keep it on the roadmap, but not a hard blocker for the next 30 days.

