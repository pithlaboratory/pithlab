# Pith v5.4 — Execution Plan (Runtime Stabilization + Support/Ops Desk)

> **Status:** DRAFT (execution plan from Pith v5.4 baseline)
> This plan supersedes the original “Pith v5 — Execution Plan: Weeks 1–6” and assumes TraceStore v1/v1.1, EvaluationRecord v1, and trace correlation are already shipped.
---

## Completed Baseline (Pre-v5.4)
The following structural gaps have already been closed and are considered production-stable:
- ✅ `workspace_id` flows through core persistence layers (`episodes.db`, `task_traces`, eval blobs).
- ✅ TraceStore v1 & v1.1 shipped: enriched `task_traces` schema (`runtime_mode`, `task_type`, `failure_class`, `error_code`, `cost_estimate_usd`, `runtime_config_ver`).
- ✅ EvaluationRecord v1 contract live: end-to-end trace correlation (`trace_id` + `task_id`), `human_override` sync, `failure_class` wiring.
- ✅ Governance guards active in Telegram interface (delete, leak, exfiltration, workspace isolation).
- ✅ `autonomy.yaml` structure defined; runtime enforces L0–L1 tiers only.

---

## Phase 1 — Horizon 0–2 Weeks: Structural Foundations

### 1.1 Workspace Scoping — Confirmed Baseline + Gaps
**Context:** `workspace_id` is already present in traces, eval, and memory. This phase closes residual gaps to guarantee strict isolation.

**What to implement:**
- **Audit & enforce:** Verify that *every* new and existing persistence surface (`episodes.db`, `llm_calls`, `failure_cases`, new tables) uses `workspace_id` as a mandatory filter or composite key.
- **Context retrieval:** Ensure `get_recent_context()` strictly filters by `workspace_id`, never falling back to user-only scoping.
- **Schema enforcement:** Run a one-off audit script that flags any rows with `workspace_id = NULL` or default fallbacks, and add `NOT NULL` constraints where safe.

**How to test it:** After audit/fix, run parallel requests across two distinct workspaces. Confirm `SELECT DISTINCT workspace_id FROM episodes` returns isolated sets, and that `get_recent_context` for Workspace A returns zero records tagged to Workspace B.

**Logs & metrics:**
- `DEBUG`: `workspace_id=<value>` logged on every `save_episode` and `get_recent_context` call.
- Zero `workspace_id` leakage or `NULL` rows in production post-migration.

---

### 1.2 `autonomy.yaml` — Schema Validation & PatchGate Decision Log
**Context:** Autonomy tiers are currently L0–L1 only. This work wires `PatchGate` and `autonomy.yaml` validation without enabling higher autonomy.

**What to implement:**
- **Schema validation:** Create `core/governance/autonomy_schema.py` (Pydantic model: `version`, `blocked_targets`, `safe_autopatch_targets`, `environments: dict[EnvironmentPolicy]`). Validate on startup; fail fast if invalid.
- **Decision logging:** Append-only JSONL at `data/patch_gate_decisions.log`. Every `PatchGate.check()` writes: `timestamp`, `patch_id`, `target`, `decision`, `reason`, `policy_version`.
- **Integration:** Align field names and policy logic with `PITH_GOVERNANCE_V1.md`.

**How to test it:** Introduce a deliberate schema typo. Confirm runtime refuses to start with a clear error. Fix it, confirm clean startup, and verify `patch_gate_decisions.log` grows with well-formed entries after policy evaluations.

**Logs & metrics:**
- `[governance] autonomy.yaml v<version> loaded and validated OK`
- Startup fails with `[governance] FATAL: autonomy.yaml validation failed: <field> <error>` on mismatch.

---

### 1.3 AgentSpec Contract — Interface Boundary Only
**Context:** For v5.4, `AgentSpec` is primarily used inside Support/Ops Desk and internal engineering flows; full Agent Company topology is vNext.

**What to implement:**
- Define typed boundaries in `core/agents/spec.py`: `AgentInput`, `AgentOutput`, `AgentSpec`.
- Wrap existing agent stubs (`tera.py`, `hex.py`, `coda.py`, `plex.py`) to conform to `async def process_async(input: AgentInput) -> AgentOutput`. Internal logic stays unchanged this week.
- Update `core/orchestrator.py` to consume `AgentOutput` explicitly and log `agent_name`, `success`, `fallback_used`, `latency_ms`.

**How to test it:** Pytest per agent: pass valid `AgentInput`, assert return type `AgentOutput`, `success: bool`, and `content` non-empty or `error` set.

**Logs & metrics:**
- `[orchestrator] agent=tera success=True latency_ms=340 fallback=False`
- Timeout logs: `[orchestrator] agent=hex TIMEOUT after 30s fallback_mode=stub`

---

## Phase 2 — Horizon 2–4 Weeks: Hardening & Boundaries

### 2.1 TraceStore v1.1 — Hardening & Linkage
**Context:** TraceStore v1 and v1.1 are shipped. Goal: harden end-to-end linkage and expose minimal operational visibility for Support/Ops Desk.

**What to implement:**
- Ensure `trace_id` propagates seamlessly: Telegram → Planner/Orchestrator → TraceStore → EvaluationRecord v1.
- Validate that required fields (`runtime_mode`, `task_type`, `failure_class`, `error_code`, `cost_estimate_usd`, `runtime_config_ver`) are **always** populated.
- Expose minimal queries/dashboards for Support/Ops Desk: tasks/day, cost/workflow, `failure_class` distribution, `human_override` rate.

**How to test it:** Run real Support/Ops Desk requests via Telegram. Verify each produces:
1. A `task_traces` row with all required fields populated.
2. An eval blob with `task_success`, `human_override`, `failure_class`, `cost_per_workflow`.
3. A verifiable `trace_id` + `task_id` linkage across both.

**Logs & metrics:**
- New queryable baselines per workspace.
- Alert threshold: `WARNING` if any single task trace reports `cost_usd > 0.50`.

---

### 2.2 WorkspaceService v0
**Context:** First concrete step toward `PITH_DEPLOYMENT_MODEL_V1` workspace/tenant separation. Minimal service for single-developer / early-pilot use.

**What to implement:**
- `core/services/workspace_service.py`: `create_workspace()`, `get_workspace()`, `resolve_for_user(user_id, hint) -> Workspace`.
- SQLite table: `workspaces(id, name, owner_id, created_at, active)`.
- Replace Telegram `chat_id` heuristic with `workspace_service.resolve_for_user()` at request intake.
- `runtime_planner.py` now receives `workspace_id` from the service, not the caller.

**What stays stubbed:** Multi-workspace switching, CRUD API, full tenant isolation. Users get exactly one active workspace.

**How to test it:** Two distinct users → two distinct workspace rows. Memory/context retrieval strictly scoped. SQL logs confirm `WHERE workspace_id = ?` on all reads.

---

### 2.3 Evaluator Calibration Baseline
**Context:** Addresses Gap 7 before any auto-patching is considered. Calibrate against real traffic. Aligned with `PITH_EVALUATION_V1` & `PITH_EVAL_OPS_V1`.

**What to implement:**
- `scripts/calibrate_evaluator.py`: Reads historical episodes, runs evaluator, computes distribution (mean, p5, p50, p95), writes `data/eval_baseline_v0.json`.
- Update `core/governance/patch_gate.py` to read thresholds from baseline JSON instead of hardcoded values.
- In v5.4, calibrated thresholds drive **manual review & gating**, not auto-apply.

**How to test it:** Run calibration. Inspect p5 score. If `p5 < 0.5`, current thresholds are too loose; if `p5 > 0.5`, too conservative. Commit `eval_baseline_v0.json` as a versioned governance artifact.

---

## Phase 3 — Horizon 4–6 Weeks: Focused Agents & Evolution Loop v0

### 3.1 Real Agent Implementations — Tera & Coda (Support/Ops Focus)
**Context:** In v5.4, the primary wedge is Support/Ops Desk. Real Tera and Coda implementations must first target Support/Ops workflows (workspace KB/SOP retrieval, ticket/incident next-action planning).

**What to implement:**
- `tera.py`: Structured KB/web search over workspace docs & SOPs. Returns normalized `AgentOutput.content` with source attribution. Respects `max_tokens`.
- `coda.py`: Given synthesized context, produces machine-parseable next-action plan (`{"steps": [], "requires_human": bool, "risk_level": str}`).
- `orchestrator.py`: Consumes structured Coda output, not raw prose.

**How to test it:** Tera: query `"latest SOP for incident escalation"` → assert structured, attributed content, `success=True`. Coda: multi-step planning query → assert valid JSON with `steps` key.

---

### 3.2 ModeDetector — Explicit Classification
**Context:** Close Gap 4. Mode classification becomes auditable, not implicit. Terminology aligned with `PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`.

**What to implement:**
- `core/runtime/mode_detector.py`: Transparent scoring function over recent messages + query. Returns `RuntimeMode` + `confidence: float` + `reason: str`.
- Replace implicit planner logic with explicit `mode_detector.detect()`. Log as `TraceEvent`.
- Low-confidence (`<0.6`) modes flagged in trace for manual review.

**How to test it:** Pytest with 20 labeled examples (`normal`, `diagnostics`, `vision`). Target ≥18/20 accuracy. These examples seed the future eval dataset.

**Logs & metrics:**
- Every trace contains: `detected_mode`, `mode_confidence`, `mode_reason`.
- Explicit fallback/log when `confidence < 0.6`.

---

### 3.3 Evolution Loop v0 — Failure Mining → Human-Reviewable Patch
**Context:** Close the loop to produce 1–2 reviewable patch candidates/week for Support/Ops & core runtime. **No auto-apply.** Human reviews every candidate. Aligned with `PITH_EVAL_OPS_V1` & Governance.

**What to implement:**
- `core/evolution/failure_miner.py`: Nightly script (`scripts/nightly_mine.py`). Reads TraceStore v1.1 using `FailureClass` taxonomy & `EvaluationRecord v1`. Outputs `data/failure_candidates_<date>.json`.
- `core/evolution/patch_planner.py`: Reads failure clusters → generates `patch_candidates.json` (`patch_id`, `target`, `proposed_change`, `risk_level`, `supporting_evidence`).
- `core/governance/patch_gate.py`: Evaluates against `autonomy.yaml` & Safe Tool Runtime Policy. Writes `patch_gate_decisions.log`. Allowed decisions → human-readable `data/patches_for_review/patch_<id>.md`.

**How to test it:** Run nightly mine → confirms ≥1 cluster. Run planner → produces `patch_candidates.json`. Run gate → logs decision + generates at least one `.md` review file.

---

## Summary Horizon Table

| Horizon | Primary Deliverable | Gap Closed / Hardened | Test Signal |
|---------|---------------------|------------------------|-------------|
| **Baseline** | TraceStore v1/v1.1, EvalRecord v1, Trace Correlation, Telegram Guards | Gaps 1, 3, 5, 7 | Production telemetry shows complete trace ↔ eval linkage |
| **0–2 wks** | Workspace audit + strict scoping, `autonomy.yaml` validation, `AgentSpec` boundary | Residual Gap 3, Gap 6 | Zero `NULL` workspace_id; runtime fails on bad autonomy config; typed agent logs appear |
| **2–4 wks** | TraceStore v1.1 hardening, WorkspaceService v0, Evaluator calibration | Gaps 3, 7 | Full trace row after every request; two users → two isolated memory namespaces; baseline JSON committed |
| **4–6 wks** | Tera & Coda (Support/Ops), ModeDetector, Evolution Loop v0 | Gaps 1, 2, 4 | Structured agent outputs; `detected_mode` in every trace; `patches_for_review/*.md` generated weekly |

---

## Invariants
- **Viktor in Telegram stays live throughout.** Every change is a minimal safe patch.
- **No phase involves a rewrite** of the router, planner, or memory manager internals.
- **Production stability is not traded** for any of this.
- See `PITH_DEV_CONTEXT.md` (§5–8) for canonical development rules and identity guardrails.