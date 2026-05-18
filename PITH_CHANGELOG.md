# PITH CHANGELOG

Этот файл фиксирует значимые изменения в разработке, инфраструктуре, архитектуре и workflow Pith Runtime.

**Важно:**
- Это не manifesto и не doctrine.
- Здесь пишем факты изменений, решений и сдвигов фокуса.
- Любое нетривиальное изменение в runtime, routing, memory, governance, interfaces или tooling должно быть отражено здесь.

---

## 2026-05-18

### Telegram interface — env token lookup + eval v1 storage

- Нормализован источник Telegram bot token:
  - `core/secrets.TG_TOKEN` теперь читается через `require_env("TELEGRAM_BOT_TOKEN", "TG_TOKEN", "TGTOKEN")`.
  - Рекомендуемый ключ для новых деплоев — `TELEGRAM_BOT_TOKEN`; `TG_TOKEN` и `TGTOKEN` остаются backward-compatible alias'ами.
  - Документацию/пример `.env` нужно обновить под эту схему.

- Расширен `RuntimePlanner` для трейс‑корреляции:
  - `RuntimePlanner.plan_and_answer(...)` принимает `trace_id` и пробрасывает его дальше в direct LLM flow.
  - Telegram interface генерирует `trace_id` на входе, передаёт его в `TaskService`/`RuntimePlanner` и сохраняет в `episodes.metadata` (user + assistant episodes).

- Telegram interface пишет EvaluationRecord v1 в assistant episodes:
  - `interfaces/telegram_bot.py` после `evaluator.evaluate_response(...)` обогащает eval‑blob полями:
    - `trace_id`, `workspace_id`, `task_id`,
    - `cost_per_workflow`,
    - `runtime_mode`, `task_type`, `workflow_type`,
    - `failure_class` (если задано).
  - В `episodes.metadata.eval` теперь сохраняется полный `EvaluationRecord v1`:
    `task_success`, `human_override`, `quality_score`, `eval_source`, `eval_version`,
    `rubric_version`, `cost_per_workflow`, `policy_violation`, `failure_class`,
    `workflow_type`, `runtime_mode`, `trace_id`, `workspace_id`, `tokens`, `cost`, `scores`.

- Smoke test (Telegram, user_id=191175045):
  - Для свежего диалога `user: "салют smoke" / assistant: "Салют. Слышу. Чем помогу?" / user: "test eval v1"` в `episodes.db` появились:
    - user episode с `metadata.task_id` и `metadata.trace_id`,
    - assistant episode с `metadata.eval.eval_version = "evaluation_v1"` и всеми полями EvaluationRecord v1.
  - Проверено через прямой SQLite‑запрос с `ORDER BY rowid DESC` и фильтрацией по `user_id`.

- Backward compat:
  - Исторические assistant episodes до 2026‑05‑18 могут содержать старый eval‑формат (без `task_success` и `eval_version`).
  - Backward migration не выполнялась; для фильтрации актуальных records использовать:
    `json_extract(metadata, '$.eval.eval_version') = 'evaluation_v1'`.

- Risk: Low — изменения additive:
  - env‑lookup расширен через fallback,
  - schema `episodes.db` не менялась,
  - EvaluationRecord v1 совместим с уже существующими eval‑blob'ами (добавляются поля, не удаляются).

---

## 2026-05-14

### EvaluationRecord v1 — end-to-end traceable evaluation contract
- Aligned `core/evolution/evaluator.py` with `EvaluationRecord v1` contract:
  - `evaluate_response()` now returns canonical fields: `task_success`, `human_override`, `quality_score`, `cost_per_workflow`, `policy_violation`, `failure_class`, `eval_source`, `eval_version`.
  - `human_override` defaults to `"none"`; caller may enrich based on correction path.
  - `task_success` is canonical source for task completion analytics (`success` / `partial_success` / `failure`).
  - `trace_id` and `workspace_id` remain caller responsibility (runtime layer).
- Updated `interfaces/telegram_bot.py` to enrich eval blob with runtime linkage:
  - After `evaluator.evaluate_response(...)`, caller adds: `trace_id`, `workspace_id`, `task_id`, `cost_per_workflow`, `failure_class`, `runtime_mode`, `task_type`, `workflow_type`.
  - Removed `execution_path` from `eval_kwargs` (not in evaluator signature) — fixes potential `TypeError`.
  - Ensured `attach_execution_result()` is called **before** `update_status(..., completed)` — guarantees cost/metadata are persisted before trace finalization.
- Synchronized user feedback with `human_override` in `handle_feedback()`:
  - `👍 (positive)` → `human_override="none"`
  - `👎 (negative)` → `human_override="minor_correction"` (v1 heuristic; can be refined later).
- Verification:
  - Smoke test confirms `metadata["eval"]` in `episodes.db` contains all `EvaluationRecord v1` required fields.
  - Traceability rule enforced: every eval record resolvable to `task_traces` via `trace_id` + `task_id`.
- Risk: Low — all changes are backward-compatible; additive schema migrations only.
- Commit: `feat: evaluation v1.1 — traceable EvaluationRecord contract + feedback sync` (core/evolution/evaluator.py, interfaces/telegram_bot.py)

### [docs] Runtime context review and hardening plan
- Added `docs/PITH_RUNTIME_CONTEXT_REVIEW_2026-05-14.md` as the first structured runtime context review and hardening baseline.
- Documented initial Patch / Execution Plan for:
  - TraceStore schema (task_traces runtime_mode, task_type, failure_class, error_code, cost_estimate_usd, runtime_config_ver),
  - FailureClass enum introduction,
  - ExecutionResult schema,
  - RuntimeConfig versioning,
  - ContextAssembler audit.
- Scope: runtime hardening for v5.2, no expansion into Agent Company workflows or operator console in this phase.
- Risk: None — documentation only.

### TraceStore v1.1 — failure taxonomy and enriched task traces
- Implemented minimal failure taxonomy:
  - Added `core/observability/failure_taxonomy.py` with `FailureClass` enum (routing_failure, planner_failure, orchestrator_failure, tool_failure, memory_failure, policy_failure, approval_timeout, artifact_failure, quality_failure, cost_guardrail_violation, unknown_failure).
- Extended `task_traces` schema via additive migration:
  - Added columns `runtime_mode`, `task_type`, `failure_class`, `error_code`, `cost_estimate_usd`, `runtime_config_ver` to `data/episodes.db.task_traces` using `PRAGMA table_info` + `ALTER TABLE ... ADD COLUMN` (backward-compatible).
- Updated `core/observability/trace_store.py`:
  - `task_started(...)` now records workspace/runtime metadata (workspace_id, runtime_mode, task_type, runtime_config_ver) with COALESCE-safe updates.
  - `task_finished(...)` now records `duration_ms` and `cost_estimate_usd`.
  - `task_failed(...)` now records `error_type`, `failure_class`, `error_code`, `duration_ms`.
- Updated `core/services/task_service.py`:
  - Extended `update_status(...)` to accept `failure_class` and `error_code` (backward-compatible signature).
  - On completed tasks: passes `task.cost_usd` into TraceStore, populating `cost_estimate_usd`.
  - On failed/cancelled tasks: passes `error_type` (terminal status), resolved `FailureClass` (default `unknown_failure`), and optional `error_code` into TraceStore.
- Verification:
  - Smoke tests confirm:
    - successful tasks write `status='ok'`, `duration_ms`, `cost_estimate_usd`,
    - failed tasks write `status='error'`, `error_type`, `failure_class`, `error_code`, `task_type`.
- Risk: Low — additive schema migrations only; no data loss possible.
- Commit: `runtime: add failure taxonomy and enrich task traces` (core/observability/failure_taxonomy.py, core/observability/trace_store.py, core/services/task_service.py)

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
- Risk: Low — isolated module, no breaking changes.

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
- Risk: None — documentation only.

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
- Risk: None — documentation only.

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
- Risk: None — conceptual alignment only.

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
- Risk: Low — workflow change only, no code impact.

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