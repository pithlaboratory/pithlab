Claude Architecture Workspace   статус (draft/accepted)
## Pith v5 — Execution Plan: Weeks 1–6

---

## Phase 1 — This Week: Structural Foundations (Days 1–5)

**Goal:** Make the three urgent gaps structurally impossible to ignore. No new features. No rewrites. Minimal safe patches that enforce contracts and prevent silent failures in production today.

---

### 1.1 Workspace Scoping — Schema Migration

**What to implement first.**

Add `workspace_id: str` to every entity that touches persistent state. This is a schema change, not a logic change.

Files to touch:
- `core/memory/manager.py` — add `workspace_id` param to `save_episode()` and `get_recent_context()`. Default to `"default"` if not provided so existing calls don't break.
- `data/episodes.db` — migration: `ALTER TABLE episodes ADD COLUMN workspace_id TEXT NOT NULL DEFAULT 'default'`. Same for `llm_calls` and `failure_cases` if they exist as tables.
- `core/runtime_planner.py` — ensure `workspace_id` is resolved from the incoming request before context assembly begins. It must be a required field in the internal task representation, not an optional afterthought.
- `interfaces/telegram_bot.py` — derive `workspace_id` from chat ID or user ID for now. This is a temporary heuristic; the real WorkspaceService comes in Phase 2.

**What stays stubbed.** `WorkspaceService` as a full CRUD service stays out of scope this week. You only need the ID to flow through the call stack and act as a retrieval filter.

**How to test it.** After migration, run two parallel conversations with different chat IDs. Query `episodes.db` and confirm that `get_recent_context` for user A does not return episodes tagged with user B's workspace ID. One SQL query: `SELECT DISTINCT workspace_id FROM episodes` should show two rows.

**Logs and metrics that confirm it works.**
- Every `save_episode` call logs `workspace_id=<value>` at DEBUG level.
- Every `get_recent_context` call logs how many records were returned and what `workspace_id` filter was applied.
- Zero episodes with `workspace_id = NULL` in production after migration.

---

### 1.2 `autonomy.yaml` — Schema Validation and PatchGate Decision Log

**What to implement first.**

Define a Pydantic model for `autonomy.yaml` and validate it on startup. Add a `PatchGateDecision` log entry for every evaluation.

Files to touch:
- New file: `core/governance/autonomy_schema.py` — Pydantic model with fields: `version: str`, `blocked_targets: list[str]`, `safe_autopatch_targets: list[str]`, `environments: dict[str, EnvironmentPolicy]`. `EnvironmentPolicy` has `max_auto_risk: str`, `require_review: bool`, `canary_threshold: float`.
- `core/governance/patch_gate.py` — on module load, parse `autonomy.yaml` through the Pydantic model. If validation fails, raise a `RuntimeError` with a clear message. The runtime must not start with an invalid governance config.
- New file: `data/patch_gate_decisions.log` (append-only JSONL) — every `PatchGate.check()` call writes: `timestamp`, `patch_id`, `target`, `decision` (allowed/blocked/escalated), `reason`, `policy_version`.
- `core/runtime_planner.py` or startup entrypoint — validate `autonomy.yaml` before the bot starts accepting traffic.

**What stays stubbed.** `RolloutManager` and the canary ring logic stay out of scope this week. You only need the gate to be verifiable and its decisions to be auditable.

**How to test it.** Introduce a deliberate typo in `autonomy.yaml` (`blocked_targetss` instead of `blocked_targets`). Confirm the runtime refuses to start with a clear error message naming the invalid field. Then fix it and confirm normal startup. Check `patch_gate_decisions.log` contains a well-formed JSONL entry after any patch candidate is evaluated.

**Logs and metrics that confirm it works.**
- Startup log line: `[governance] autonomy.yaml v<version> loaded and validated OK`.
- Any startup failure due to schema mismatch produces: `[governance] FATAL: autonomy.yaml validation failed: <field> <error>`.
- `patch_gate_decisions.log` grows with one entry per patch evaluation, never silently.

---

### 1.3 AgentSpec Contract — Interface Boundary Only

**What to implement first.**

Define the typed contract. Do not rewrite any agent logic this week. The goal is to put a typed boundary around the existing stub behavior so that Phase 2 can replace internals without touching callers.

Files to touch:
- New file: `core/agents/spec.py` — defines:

```python
@dataclass
class AgentInput:
    query: str
    workspace_id: str
    task_id: str
    context: str
    max_tokens: int = 2048

@dataclass  
class AgentOutput:
    agent_name: str
    content: str
    success: bool
    fallback_used: bool
    tokens_used: int
    latency_ms: float
    error: str | None = None

@dataclass
class AgentSpec:
    name: str
    timeout_sec: int = 30
    max_tokens: int = 2048
    fallback_mode: Literal["stub", "skip", "error"] = "stub"
```

- `core/agents/tera.py`, `hex.py`, `coda.py`, `plex.py` — wrap existing logic inside `async def process_async(input: AgentInput) -> AgentOutput`. The internal implementation stays as-is. The return type must be `AgentOutput`, even if the agent is still calling a single LLM endpoint.
- `core/orchestrator.py` — update to call `agent.process_async(input)` and handle `AgentOutput` explicitly. Log `agent_name`, `success`, `fallback_used`, `latency_ms` for every agent invocation.

**What stays stubbed.** Every agent's internal implementation. You are not replacing stub LLM calls this week. You are wrapping them in a typed envelope.

**How to test it.** Write one pytest for each agent: pass a valid `AgentInput`, assert the return type is `AgentOutput`, assert `success` is a bool, assert `content` is a non-empty string or `error` is set. This should take 20 minutes to write and immediately catches any agent that returns `None` or raises an unhandled exception.

**Logs and metrics that confirm it works.**
- Orchestrator logs one line per agent: `[orchestrator] agent=tera success=True latency_ms=340 fallback=False`.
- Any agent that hits its timeout produces: `[orchestrator] agent=hex TIMEOUT after 30s fallback_mode=stub`.
- These lines do not exist today. Their presence after this change is the confirmation.

---

## Phase 2 — Weeks 2–3: Real Boundaries, Proper Traces, WorkspaceService v0

**Goal:** Promote the structural stubs from Phase 1 into functional components. Close the observability gap so you can see what the runtime is actually doing in production.

---

### 2.1 TraceStore v1

**Goal:** Every task produces a structured trace that records mode, agents used, memory records retrieved, model lane selected, cost, and evaluator score. Without this, Phases 3 and beyond are debugging blind.

Files to touch:
- New file: `core/tracing/trace_store.py` — wraps `episodes.db` or a separate `traces.db`. Schema: `task_id`, `workspace_id`, `detected_mode`, `agents_called` (JSON array), `memory_records_used` (count + IDs), `model_lane`, `total_tokens`, `cost_usd`, `evaluator_score`, `timestamp`, `duration_ms`.
- `core/runtime_planner.py` — emit a `TraceEvent` at the start of each task with `detected_mode` populated. This closes the Gap 4 observability issue from the prior analysis without yet building a proper ModeDetector.
- `core/orchestrator.py` — emit `TraceEvent` entries per agent using the `AgentOutput` data from Phase 1.
- `core/evolution/evaluator.py` — write evaluator score back to the trace record after scoring, not just to metrics files.

**What stays stubbed.** Semantic Trace (human-readable reasoning summary) stays out of scope. Raw Trace is sufficient for now.

**How to test it.** After a real production request, query `traces.db` (or `episodes.db` with the new columns) and confirm the row exists with non-null values for `detected_mode`, `cost_usd`, and `evaluator_score`. Run 10 real requests and check that zero traces are missing any required field.

**Logs and metrics.**
- New dashboard query: tasks per day, average cost per task, average evaluator score per task, per workspace. These should be readable from `traces.db` with a single SQL query.
- Alert threshold: if any task produces a trace with `cost_usd > 0.50`, log a WARNING.

---

### 2.2 WorkspaceService v0

**Goal:** Replace the `workspace_id = chat_id` heuristic from Phase 1 with a minimal service that creates and retrieves workspaces explicitly.

Files to touch:
- New file: `core/services/workspace_service.py` — three methods only: `create_workspace(name, owner_id) -> Workspace`, `get_workspace(workspace_id) -> Workspace | None`, `resolve_for_user(user_id, hint: str | None) -> Workspace`. The third method handles the common case: given a user ID, find their active workspace or create a default one.
- New table in SQLite: `workspaces(id TEXT PK, name TEXT, owner_id TEXT, created_at TIMESTAMP, active BOOL)`.
- `interfaces/telegram_bot.py` — replace the chat_id heuristic with `workspace_service.resolve_for_user(user_id)` at request intake.
- `core/runtime_planner.py` — `workspace_id` now comes from `WorkspaceService`, not from the caller.

**What stays stubbed.** Multi-workspace switching, workspace CRUD via API, tenant isolation. Users have exactly one active workspace for now. That is sufficient and correct for the single-developer use case.

**How to test it.** Create two users. Confirm each gets a distinct workspace row. Confirm memory retrieval is scoped correctly by checking the `workspace_id` filter in SQL logs.

---

### 2.3 Evaluator Calibration Baseline

**Goal:** Address Gap 7 before any auto-patching is enabled. Run the evaluator over the last 90 days of episodes and derive empirical thresholds.

Files to touch:
- New script: `scripts/calibrate_evaluator.py` — reads all episodes from `episodes.db`, runs the evaluator over each, computes score distribution (mean, p5, p50, p95), writes results to `data/eval_baseline_v0.json`.
- `core/governance/patch_gate.py` — replace the hardcoded `score.final < 0.5` threshold with `load_baseline_threshold("score.final", percentile=5)` read from `eval_baseline_v0.json`.
- `data/eval_baseline_v0.json` — committed to the repo, versioned, treated as a governance artifact.

**How to test it.** Run the calibration script. Inspect the p5 score. If it is above 0.5, the current hardcoded threshold is too conservative and you are not blocking real failures. If it is below 0.5, the threshold is too loose. Either way, you now have a real number instead of an assertion.

---

## Phase 3 — Weeks 4–6: Real Agents, ModeDetector, Evolution Loop v0

**Goal:** Replace the last major stubs. Make the evolution pipeline emit one real, human-reviewable patch candidate per week based on production traffic. Do not auto-apply anything yet.

---

### 3.1 Real Agent Implementations — Tera and Coda First

**Why Tera and Coda first.** Tera (web research / external context) and Coda (execution framing / next actions) are the two agents with the clearest input/output contracts and the most direct user-visible impact. Plex (coherence) and Hex (strategist/critic) can remain as LLM pass-throughs longer because their failure mode is lower-quality synthesis, not missing functionality.

Files to touch:
- `core/agents/tera.py` — real implementation: given a query, perform a structured web search or doc lookup, return a normalized `AgentOutput.content` with source attribution. Uses the Tool Plane for web search. Respects `max_tokens` from `AgentSpec`.
- `core/agents/coda.py` — real implementation: given the synthesized context from other agents, produce a structured next-action plan (JSON with `steps: list[str]`, `requires_human: bool`, `risk_level: str`). Coda's output must be machine-parseable, not prose.
- `core/orchestrator.py` — update synthesis to consume Coda's structured output, not just its text.

**What stays stubbed.** Plex and Hex remain as typed LLM wrappers behind `AgentSpec`. They satisfy the contract from Phase 1 without being replaced.

**How to test it.** For Tera: given query "latest Python 3.13 release notes", assert `AgentOutput.content` contains structured data, `success=True`, and `fallback_used=False`. For Coda: given a multi-step planning query, assert `AgentOutput.content` is valid JSON with a `steps` key.

---

### 3.2 ModeDetector — Explicit Classification

**Goal:** Close Gap 4. Mode classification becomes an auditable decision, not an implicit keyword scan.

Files to touch:
- New file: `core/runtime/mode_detector.py` — takes last N messages and current query, returns `RuntimeMode` with a `confidence: float` and `reason: str`. Implementation: a scoring function over signal keywords weighted by recency, query length, and presence of architecture/diagnostic terms. Not ML — a transparent scoring function is sufficient and testable.
- `core/runtime_planner.py` — replace implicit mode logic with `mode_detector.detect(history, query)`. Log the result as a `TraceEvent`.
- `core/tracing/trace_store.py` — `detected_mode` field now populated with the ModeDetector output plus its confidence score.

**How to test it.** Write a pytest with 20 labeled examples (10 NORMAL, 5 DIAGNOSTICS, 5 VISION). Assert the detector classifies correctly on at least 18/20. These examples become the seed of a future eval dataset.

**Logs.** Every task trace now contains: `detected_mode`, `mode_confidence`, `mode_reason`. Any task where `mode_confidence < 0.6` gets flagged in the trace for manual review.

---

### 3.3 Evolution Loop v0 — Failure Mining to Human-Reviewable Patch

**Goal:** Close the loop enough to produce one reviewable patch candidate per week. No auto-apply. Human reviews every candidate.

Files to touch:
- `core/evolution/failure_miner.py` — wire it to `traces.db`. It should run as a nightly script (`scripts/nightly_mine.py`), not inline during request handling. Output: a JSON file `data/failure_candidates_<date>.json` listing clustered failure patterns with example task IDs, failure type, and frequency.
- `core/evolution/patch_planner.py` — reads `failure_candidates.json`, generates one patch proposal per cluster. Output format: `patch_candidates.json` with fields `patch_id`, `target` (skill/prompt/policy), `proposed_change`, `risk_level`, `supporting_evidence` (list of task IDs).
- `core/governance/patch_gate.py` — reads `patch_candidates.json`, evaluates each against `autonomy.yaml`. Writes to `patch_gate_decisions.log`. For any `allowed` decision, writes a human-readable summary to `data/patches_for_review/patch_<id>.md`.

**What stays stubbed.** `RolloutManager`, canary deployment, auto-apply. Any patch that passes PatchGate produces a markdown file for human review, nothing more. You review and apply manually this phase.

**How to test it.** Run `nightly_mine.py` against production episodes. Confirm it produces at least one failure cluster. Run `patch_planner.py`. Confirm it produces a readable `patch_candidates.json`. Run `patch_gate.py`. Confirm `patch_gate_decisions.log` has a new entry and at least one `patches_for_review/*.md` exists.

---

## Summary Table

| Week | Primary deliverable | Gap closed | Test signal |
|---|---|---|---|
| 1 | `workspace_id` flows through all persistence calls | Gap 3 | Zero NULL workspace_id in episodes.db |
| 1 | `autonomy.yaml` validated on startup, decisions logged | Gap 6 | Runtime refuses to start on schema error |
| 1 | `AgentSpec` + typed `AgentOutput` on all four agents | Gap 1 | Per-agent latency and success in orchestrator logs |
| 2–3 | TraceStore v1 — one structured trace per task | Gaps 4, 7 | Full trace row in DB after every request |
| 2–3 | WorkspaceService v0 — workspace resolved at intake | Gap 3 | Two users, two isolated memory namespaces |
| 2–3 | Evaluator calibration baseline committed | Gap 7 | PatchGate thresholds derived from real data |
| 4–6 | Tera and Coda real implementations | Gap 1 | Structured AgentOutput, parseable by orchestrator |
| 4–6 | ModeDetector explicit + logged | Gap 4 | detected_mode in every trace, confidence > 0.6 |
| 4–6 | Nightly mine → patch candidate → human review file | Gap 2 | One patch_for_review/*.md generated per week |

**Invariant across all phases:** Viktor in Telegram stays live throughout. Every change is a minimal safe patch. No phase involves a rewrite of the router, planner, or memory manager internals. Production stability is not traded for any of this.