# PITH CHANGELOG

Этот файл фиксирует значимые изменения в разработке, инфраструктуре, архитектуре и workflow Pith Runtime.

**Важно:**
- Это не manifesto и не doctrine.
- Здесь пишем факты изменений, решений и сдвигов фокуса.
- Любое нетривиальное изменение в runtime, routing, memory, governance, interfaces или tooling должно быть отражено здесь.

---

## 2026-05-12

### TraceStore v1 — minimal task-level backbone
- Added minimal `TraceStore v1` backbone for task-level observability.
- Introduced new SQLite table `task_traces` in `data/episodes.db`.
- Implemented new module:
  - `core/observability/trace_store.py`
- Integrated task lifecycle tracing into `core/services/task_service.py`:
  - `create_task()` → `task_started(task_id, workspace_id)`
  - `update_status(... completed ...)` → `task_finished(task_id, duration_ms)`
  - `update_status(... failed/cancelled ...)` → `task_failed(task_id, error_type, duration_ms)`
- Scope intentionally kept minimal:
  - no changes to existing tables,
  - no router-level trace wiring,
  - no per-LLM-call spans,
  - no per-agent spans,
  - no evaluator score wiring in this phase.
- Verified with smoke test:
  - task created,
  - status moved through `executing` → `completed`,
  - corresponding row appeared in `task_traces`,
  - `status='ok'`,
  - `workspace_id` recorded,
  - `duration_ms` non-null.
- Commit/push completed as isolated minimal patch:
  - `Add minimal task trace backbone`

### Engineering significance
- This is the first concrete implementation step for structured observability beyond existing `episodes.db` / `llm_calls` / `failure_cases` baseline.
- Task-level trace backbone now exists as a reversible production-safe first phase.
- Future observability expansion remains deferred:
  - per-LLM-call trace,
  - per-agent spans,
  - evaluator score linkage,
  - trace query/read API,
  - dashboards / analytics.

---

## 2026-05-07

### vNext framing added to PITH_MASTER_PLAN
- Added section 16 "Pith vNext" to `docs/PITH_MASTER_PLAN.md` as post-baseline expansion roadmap.
- Clarified next evolution layer beyond v5.1 runtime-first baseline:
  - **repo intelligence** (RepoIndexer, ContextRetriever, DocumentIngestor, WebResearch),
  - **capability accumulation** via SkillRegistry, SkillBinding, candidate mining, review pipeline,
  - **governed agent topology** (AgentSpec, A2A delegation, per-agent namespaces, policy-bound tools),
  - **multimodal context** (voice, image/doc/audio ingestion, multi-source assembly),
  - **rich operator experience** (dashboard v2, trace explorer, workspace UX).
- vNext phase map (A–G) extends current phases 1–5 without breaking runtime-first identity:
  - A. Kernel Hardening,
  - B. Workspace OS,
  - C. Governance Core,
  - D. Capability Engine,
  - E. Intelligence Fabric,
  - F. Experience & Modalities,
  - G. Governed Autonomy.
- Updated master plan header: **v5.1 / Runtime-first baseline + vNext framing**.
- Updated one-liner evolution:
  - v5.1: *"Chat solves prompts. Pith solves continuity."*
  - vNext: *"Pith vNext solves continuity, capability accumulation and governed intelligence inside workspaces."*

### Technical fixes
- Fixed `interfaces/telegram_bot.py` syntax error in `build_application()`:
  - **Before:** `write_timeout: 30.0,` (invalid colon syntax inside function call)
  - **After:** `write_timeout=30.0,` (correct kwarg syntax)
  - **Impact:** Bot startup was broken, now fixed.
  - **Risk:** Low — syntax error caught before production deploy.
- Simplified feedback handler (`handle_feedback`) in Telegram interface:
  - Removed chat-visible reply ("Feedback recorded" message).
  - Kept ephemeral `query.answer()` for instant spinner removal.
  - Kept internal logging (`logger.info`) for observability.
  - User experience: button removal + silent ack, no chat noise.
  - **Rationale:** Feedback should be background signal, not interruption.

### Documentation alignment
- Master plan now covers both v5.1 runtime-first baseline **and** vNext expansion roadmap in one canonical doc.
- vNext is positioned as natural next layer, not as separate fork or rewrite.
- Core identity remains unchanged:
  - *workspace-native orchestration runtime for continuity-driven long-running work*.

---

## 2026-04-29

### Master Plan baseline
- Finalized `docs/PITH_MASTER_PLAN.md` as the canonical runtime plan for Pith v5.1.
- Master plan now defines:
  - product layer,
  - architecture layer,
  - implementation plan (30 / 60 / 90 days),
  - metrics & governance,
  - ADR principles.

### Canonical product definition
- Locked the one-line product definition:
  - **Pith is a self-improving continuity engine / workspace-native orchestration runtime for long-running cognitive work.**
- Locked the guiding principle:
  - **Chat solves prompts. Pith solves continuity.**

### Current engineering priorities
1. Stabilize real agents (`tera`, `hex`, `coda`) and reduce bridge/stub behaviour.
2. Add TraceStore + structured observability + cost attribution.
3. Build `PithEval v0.1` with 30–50 ground-truth tasks.
4. Move toward Memory v2:
   - namespace isolation,
   - summarization hierarchy,
   - forgetting policy.
5. Prepare A2A protocol and typed tool contracts.

### Documentation / architecture alignment
- Added canonical kernel contract: `docs/PITH_KERNEL.md` (ADR-Kernel-001).
- Added architecture decision index: `docs/ADR_INDEX.md`.
- Updated `PITH_DEV_CONTEXT.md` canonical references to point to the new kernel/ADR docs.
- Fixed documentation hierarchy so Manifesto / Product Doctrine / Architecture North Star / Kernel / Roadmap are aligned around continuity runtime framing.

---

## 2026-04-28

### Identity alignment
- Pith is now explicitly treated as a **self-improving continuity runtime / workspace-native orchestration runtime**, not as a Telegram bot, not as an AGI claim, and not as a persona product.
- Telegram, CLI, HTTP API are treated as interfaces over the same runtime.
- Viktor remains the main live interface, but is no longer treated as the identity of the product.

### Documentation alignment
- Aligned core docs around the same language:
  - `docs/MANIFESTO.md`
  - `docs/PRODUCT_DOCTRINE.md`
  - `docs/PITH_MASTER_PLAN.md`
- Core positioning fixed around:
  - continuity,
  - memory,
  - orchestration,
  - execution,
  - observability,
  - governed evolution.

### Engineering interpretation
- Runtime-first architecture is now the canonical framing.
- Personas, UI and channels are secondary to:
  - Router,
  - RuntimePlanner,
  - Memory,
  - Evaluator,
  - Governance,
  - Evolution loop.

---

## 2026-04-24

### Dev workflow
- Switched development workflow to VS Code + Remote SSH on server `msk-1-vm-ngf0`.
- Decided to use an IDE AI assistant via OpenRouter instead of terminal-only flow.
- Goal: stop losing development context and stabilize the Pith core runtime.

### Product / runtime reality
- Main live user interface remains Viktor via Telegram.
- Dashboard is secondary for now.
- Current practical priority is not UI expansion, but stabilization of the core runtime.

### Technical focus
1. Router + `config.yaml` + secrets alignment.
2. Stable startup and behaviour of Viktor / Telegram pipeline.
3. Clarifying `RuntimePlanner` and its interaction with Router and `MemoryManager`.

---

## Changelog rules

When updating this file:

- Record **what changed**, **why it changed**, and **what it affects**.
- Prefer concrete entries over vague notes.
- If the change is architectural, make sure the long-form rationale exists in:
  - `docs/PITH_MASTER_PLAN.md`,
  - `docs/PRODUCT_DOCTRINE.md`,
  - or ADR notes (e.g. `docs/PITH_KERNEL.md`, `docs/ADR_INDEX.md`).
- If the change affects production runtime, mention:
  - affected component,
  - risk level,
  - rollback path if relevant.
  ---

## 2026-05-14

### Runtime context review and hardening plan
- Added `docs/PITH_RUNTIME_CONTEXT_REVIEW_2026-05-14.md` as the first structured runtime context review and hardening baseline.
- Documented initial Patch / Execution Plan for:
  - TraceStore schema (task_traces runtime_mode, task_type, failure_class, error_code, cost_estimate_usd, runtime_config_ver),
  - FailureClass enum introduction,
  - ExecutionResult schema,
  - RuntimeConfig versioning,
  - ContextAssembler audit.
- Scope: runtime hardening for v5.2, no expansion into Agent Company workflows or operator console in this phase.