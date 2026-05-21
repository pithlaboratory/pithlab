# PITH CHANGELOG

Этот файл фиксирует значимые изменения в разработке, инфраструктуре, архитектуре и workflow Pith Runtime.

**Важно:**
- Это не manifesto и не doctrine.
- Здесь пишем факты изменений, решений и сдвигов фокуса.
- Любое нетривиальное изменение в runtime, routing, memory, governance, interfaces или tooling должно быть отражено здесь.

**Формат записи:** см. раздел "Changelog rules" в конце документа.

---

## 2026-05-21

### [docs] PITH_MASTER_PLAN v5.4 — Product Focus + Governance + Scale Path

- Полностью переработан `docs/PITH_MASTER_PLAN.md` до версии **v5.4**:
  - Добавлен **раздел 0: Product Focus & GTM** с таргет-сегментом, персонами, hero use case, monetization, GTM-стратегией.
  - Добавлен **0.8 Product Hierarchy** — явная иерархия: wedge → platform → deferred narrative.
  - Добавлен **0.9 Customer Profile (Hypothesis)** — гибкий профиль, а не жёсткий фильтр.
  - Добавлен **0.10 Runtime & Product Status (May 2026)** — таблица статусов компонентов (✅/🔧/📐).
  - Обновлён **раздел 2 (Product North Star)** — синхронизирован с разделом 0 (internal vs external users).
  - Обновлён **раздел 6 (Agent Topology)**:
    - `6.1 Agent Categories` вместо фиксированного списка агентов.
    - `6.2 AgentSpec Contract` с `category`, `department`, `risk_tier`, `allowed_data_scopes`.
    - `6.3.1 Multi-Agent Maturity Levels` — уровни A→D эволюции оркестрации.
    - `6.7 Workflow Contract Standard` — YAML-контракт с `risk_class`, `approval_policy`, `acceptance_criteria`.
  - Обновлён **раздел 12 (Evaluation Ops)**:
    - `12.7 Business Usefulness Scorecard` — метрики бизнес-полезности (часы, deflection, quality).
  - Обновлён **раздел 14 (Billing)**:
    - `14.3 Product Packs / Vertical Packs` — последовательность вертикалей: IT/MSP → Logistics → Professional Services.
  - Обновлён **раздел 15 (Data Governance)**:
    - `15.4 Safe Tool Runtime Policy` — defense-first подход к MCP/tools: deny-by-default, sandbox profiles, scoped permissions.
  - Обновлён **раздел 19 (Roadmap)**:
    - Добавлены квартальные привязки: `Q2 2026`, `Q2–Q3 2026`, `Q3–Q4 2026`.
    - Добавлены ссылки на раздел 27 (пятилетнюю карту).
  - Обновлён **раздел 20 (Required Platform Layers)**:
    - Добавлен статус для каждого слоя: ✅/🔧/📐 + ссылки на детальные секции.
  - Обновлён **раздел 23 (ADR)**:
    - Добавлены краткие обоснования для каждого ADR (2–3 предложения).
  - Добавлен **раздел 27: Five-Year Capability Map (2026–2030)**:
    - 2026: Digital Support/Ops Desk (v5.x)
    - 2027: Operational Layer & Product Packs
    - 2028: Platform for Digital Departments
    - 2029: Managed Digital Workforces
    - 2030: Strategic AI Operations Layer
  - Обновлён **раздел 26 (Pith vNext)**:
    - Добавлены ссылки на раздел 27.
    - Уточнён framing: "Chat solves prompts. Pith solves continuity."
  - Добавлен раздел **"How to use this document"** в начало.
  - Добавлен **раздел 28: Glossary (Working)**.

- **Risk:** Low — изменения в документации, не затрагивают runtime.
- **Rollback:** Вернуть предыдущую версию файла из git.
- **Docs:** `docs/PITH_MASTER_PLAN.md`, `docs/PITH_KERNEL.md`, `docs/ADR/`
- **Commit:** `docs: PITH_MASTER_PLAN v5.4 — Product Focus + Governance + Scale Path`

### [docs] PITH_DEV_CONTEXT.md — дев-гайд с правилами добавления фич

- Создан новый файл `PITH_DEV_CONTEXT.md` как краткий дев-гайд:
  - **Раздел 1**: Что такое Pith (дев-оптика) — runtime, а не бот.
  - **Раздел 2**: Текущий статус (v5.4) — таблица ✅/🔧/📐.
  - **Раздел 3**: Системная карта — где что живёт в коде.
  - **Раздел 4**: Дев-воркфлоу и ограничения (среда, правила, приоритеты).
  - **Раздел 5**: Технические приоритеты на Q2 2026 (Trace, Eval, Interfaces).
  - **Раздел 6**: Runtime-ограничения и бюджеты ($30/мес, L0–L1 автономия).
  - **Раздел 7**: Identity guardrails — куда не скатываемся.
  - **Раздел 8**: Канонические ссылки перед изменениями.
  - **Раздел 9**: Core сейчас / строим потом / не делаем.
  - **Раздел 10**: **How to add a new feature safely** — пошаговый алгоритм:
    - 10.1 Before you touch code (слой, сверка, формулировка)
    - 10.2 Minimal plan (MVP-патч: data, flow, guardrails)
    - 10.3 Implementation checklist (атомарность, additive, smoke-test, logging, changelog)
    - 10.4 What to avoid (большие рефакторинги, особые режимы без observability, автономия без eval)
    - 10.5 After merge (changelog, docs, eval)

- **Risk:** Low — документация, не влияет на runtime.
- **Rollback:** Удалить файл или вернуть предыдущую версию.
- **Docs:** `PITH_DEV_CONTEXT.md`, `docs/PITH_MASTER_PLAN.md`
- **Commit:** `docs: add PITH_DEV_CONTEXT.md — дев-гайд с правилами безопасного добавления фич`

### [docs] Update PITH_ACTIVE_CONTEXT for v5.4 runtime + Support/Ops Desk

- Обновлён `PITH_ACTIVE_CONTEXT.md` под `PITH_MASTER_PLAN v5.4`:
  - зафиксирована текущая фаза: Runtime stabilization + Observability/Eval v1 + Support/Ops Desk wedge;
  - добавлен snapshot канонических доков (PITH_MASTER_PLAN v5.4, PITH_DEV_CONTEXT, PITH_CHANGELOG);
  - обновлён список active priorities (runtime/tracing, Support/Ops Desk, eval/governance, docs);
  - явно перечислены short-term next steps и out-of-scope для текущей фазы.
- Старый фокус на Agent Company v1 (Sales/Marketing/Research) вынесен в исторический контекст через master plan, но больше не считается активным контекстом.

- **Risk:** None — документация только.
- **Rollback:** Вернуть предыдущую версию `PITH_ACTIVE_CONTEXT.md` из git.
- **Docs:** `PITH_ACTIVE_CONTEXT.md`, `docs/PITH_MASTER_PLAN.md`, `PITH_DEV_CONTEXT.md`
- **Commit:** `docs: align PITH_ACTIVE_CONTEXT with PITH_MASTER_PLAN v5.4`

### [config] config.yaml v5.0.1-clean-grounded

- Обновлён `config.yaml`:
  - Убраны все `# ✅ ...` комментарии для чистоты продакшен-конфига.
  - Уточнён `persona.system_prompt`:
    - Было: "нет прямого доступа... если не показано"
    - Стало: две чёткие строки: "нет самостоятельного доступа" + "можно рассуждать только по явно присланным данным"
  - Исправлен обрыв в функции `_validate_interface_config()` (была обрезана).
  - Добавлен `fcntl` single-instance lock в `interfaces/telegram_bot.py` для предотвращения дублирования процессов.
  - Интегрированы 4 governance guards в Telegram: dangerous_delete, internal_leak, data_exfiltration, workspace_isolation.
  - Добавлена запись в TraceService для каждого governance refusal.

- **Risk:** Medium — изменения в конфиге и runtime; требуется тестирование.
- **Rollback:** Вернуть `config.yaml.bak` и `interfaces/telegram_bot.py.bak`; перезапустить сервис.
- **Docs:** `config.yaml`, `interfaces/telegram_bot.py`, `docs/PITH_MASTER_PLAN.md#0.8`
- **Commit:** `config: v5.0.1-clean-grounded — governance guards + fcntl lock + prompt hardening`

---

## 2026-05-18

### [interfaces] Telegram — env token lookup + eval v1 storage

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

- **Risk:** Low — изменения additive:
  - env‑lookup расширен через fallback,
  - schema `episodes.db` не менялась,
  - EvaluationRecord v1 совместим с уже существующими eval‑blob'ами (добавляются поля, не удаляются).
- **Rollback:** Вернуть предыдущую версию `interfaces/telegram_bot.py`; перезапустить сервис.
- **Docs:** `docs/PITH_OBSERVABILITY_V1.md`, `docs/PITH_EVALUATION_V1.md`
- **Commit:** `feat: telegram eval v1 storage + trace correlation`

---

## 2026-05-14

### [eval] EvaluationRecord v1 — end-to-end traceable evaluation contract

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

- **Risk:** Low — all changes are backward-compatible; additive schema migrations only.
- **Rollback:** Вернуть предыдущие версии `core/evolution/evaluator.py` и `interfaces/telegram_bot.py`.
- **Docs:** `docs/PITH_EVALUATION_V1.md`, `docs/PITH_OBSERVABILITY_V1.md`
- **Commit:** `feat: evaluation v1.1 — traceable EvaluationRecord contract + feedback sync`

### [docs] Runtime context review and hardening plan

- Added `docs/PITH_RUNTIME_CONTEXT_REVIEW_2026-05-14.md` as the first structured runtime context review and hardening baseline.
- Documented initial Patch / Execution Plan for:
  - TraceStore schema (task_traces runtime_mode, task_type, failure_class, error_code, cost_estimate_usd, runtime_config_ver),
  - FailureClass enum introduction,
  - ExecutionResult schema,
  - RuntimeConfig versioning,
  - ContextAssembler audit.
- Scope: runtime hardening for v5.2, no expansion into Agent Company workflows or operator console in this phase.

- **Risk:** None — documentation only.
- **Rollback:** N/A
- **Docs:** `docs/PITH_RUNTIME_CONTEXT_REVIEW_2026-05-14.md`
- **Commit:** `docs: add runtime context review and hardening plan`

### [observability] TraceStore v1.1 — failure taxonomy and enriched task traces

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

- **Risk:** Low — additive schema migrations only; no data loss possible.
- **Rollback:** Откатить миграцию через `ALTER TABLE ... DROP COLUMN` (если поддержка SQLite позволяет) или создать новую БД.
- **Docs:** `docs/PITH_OBSERVABILITY_V1.md`, `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
- **Commit:** `runtime: add failure taxonomy and enrich task traces`

---

## 2026-05-12

### [observability] TraceStore v1 — minimal task-level backbone

- Added minimal `TraceStore v1` backbone for task-level observability.
- Introduced new SQLite table `task_traces` in `data/episodes.db`.
- Implemented new module: `core/observability/trace_store.py`
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

- **Risk:** Low — isolated module, no breaking changes.
- **Rollback:** Удалить таблицу `task_traces` и модуль `trace_store.py`.
- **Docs:** `docs/PITH_OBSERVABILITY_V1.md`
- **Commit:** `Add minimal task trace backbone`

---

## 2026-05-07

### [docs] vNext framing added to PITH_MASTER_PLAN

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

- **Risk:** None — documentation only.
- **Rollback:** N/A
- **Docs:** `docs/PITH_MASTER_PLAN.md`
- **Commit:** `docs: add vNext framing to PITH_MASTER_PLAN`

### [fix] interfaces/telegram_bot.py syntax error

- Fixed `interfaces/telegram_bot.py` syntax error in `build_application()`:
  - **Before:** `write_timeout: 30.0,` (invalid colon syntax inside function call)
  - **After:** `write_timeout=30.0,` (correct kwarg syntax)
  - **Impact:** Bot startup was broken, now fixed.

- **Risk:** Low — syntax error caught before production deploy.
- **Rollback:** Вернуть предыдущую версию файла.
- **Commit:** `fix: telegram_bot syntax error in build_application()`

### [ux] Simplified feedback handler in Telegram interface

- Simplified feedback handler (`handle_feedback`) in Telegram interface:
  - Removed chat-visible reply ("Feedback recorded" message).
  - Kept ephemeral `query.answer()` for instant spinner removal.
  - Kept internal logging (`logger.info`) for observability.
  - User experience: button removal + silent ack, no chat noise.
  - **Rationale:** Feedback should be background signal, not interruption.

- **Risk:** Low — UX change only, no functional impact.
- **Rollback:** Вернуть предыдущую версию `handle_feedback()`.
- **Commit:** `ux: silent feedback ack in Telegram interface`

---

## 2026-04-29

### [docs] Master Plan baseline

- Finalized `docs/PITH_MASTER_PLAN.md` as the canonical runtime plan for Pith v5.1.
- Master plan now defines:
  - product layer,
  - architecture layer,
  - implementation plan (30 / 60 / 90 days),
  - metrics & governance,
  - ADR principles.

- **Risk:** None — documentation only.
- **Rollback:** N/A
- **Docs:** `docs/PITH_MASTER_PLAN.md`
- **Commit:** `docs: finalize PITH_MASTER_PLAN v5.1 baseline`

### [product] Canonical product definition

- Locked the one-line product definition:
  - **Pith is a self-improving continuity engine / workspace-native orchestration runtime for long-running cognitive work.**
- Locked the guiding principle:
  - **Chat solves prompts. Pith solves continuity.**

- **Risk:** None — conceptual alignment only.
- **Rollback:** N/A
- **Docs:** `docs/PITH_MASTER_PLAN.md`, `docs/PRODUCT_DOCTRINE.md`
- **Commit:** `docs: lock canonical product definition`

### [priority] Current engineering priorities

- Defined current engineering priorities:
  1. Stabilize real agents (`tera`, `hex`, `coda`) and reduce bridge/stub behaviour.
  2. Add TraceStore + structured observability + cost attribution.
  3. Build `PithEval v0.1` with 30–50 ground-truth tasks.
  4. Move toward Memory v2: namespace isolation, summarization hierarchy, forgetting policy.
  5. Prepare A2A protocol and typed tool contracts.

- **Risk:** None — planning only.
- **Rollback:** N/A
- **Docs:** `docs/PITH_MASTER_PLAN.md`, `PITH_DEV_CONTEXT.md`
- **Commit:** `docs: document current engineering priorities`

### [docs] Documentation / architecture alignment

- Added canonical kernel contract: `docs/PITH_KERNEL.md` (ADR-Kernel-001).
- Added architecture decision index: `docs/ADR_INDEX.md`.
- Updated `PITH_DEV_CONTEXT.md` canonical references to point to the new kernel/ADR docs.
- Fixed documentation hierarchy so Manifesto / Product Doctrine / Architecture North Star / Kernel / Roadmap are aligned around continuity runtime framing.

- **Risk:** None — documentation only.
- **Rollback:** N/A
- **Docs:** `docs/PITH_MASTER_PLAN.md`, `docs/PITH_KERNEL.md`, `docs/ADR_INDEX.md`
- **Commit:** `docs: align documentation hierarchy around continuity runtime`

---

## 2026-04-28

### [identity] Identity alignment

- Pith is now explicitly treated as a **self-improving continuity runtime / workspace-native orchestration runtime**, not as a Telegram bot, not as an AGI claim, and not as a persona product.
- Telegram, CLI, HTTP API are treated as interfaces over the same runtime.
- Viktor remains the main live interface, but is no longer treated as the identity of the product.

- **Risk:** None — conceptual alignment only.
- **Rollback:** N/A
- **Docs:** `docs/MANIFESTO.md`, `docs/PRODUCT_DOCTRINE.md`, `docs/PITH_MASTER_PLAN.md`
- **Commit:** `docs: identity alignment — runtime-first framing`

### [docs] Documentation alignment

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

- **Risk:** None — documentation only.
- **Rollback:** N/A
- **Docs:** `docs/MANIFESTO.md`, `docs/PRODUCT_DOCTRINE.md`, `docs/PITH_MASTER_PLAN.md`
- **Commit:** `docs: align core documentation language`

### [engineering] Engineering interpretation

- Runtime-first architecture is now the canonical framing.
- Personas, UI and channels are secondary to:
  - Router,
  - RuntimePlanner,
  - Memory,
  - Evaluator,
  - Governance,
  - Evolution loop.

- **Risk:** None — conceptual alignment only.
- **Rollback:** N/A
- **Docs:** `docs/PITH_MASTER_PLAN.md`, `PITH_DEV_CONTEXT.md`
- **Commit:** `docs: engineering interpretation — runtime-first priority`

---

## 2026-04-24

### [workflow] Dev workflow

- Switched development workflow to VS Code + Remote SSH on server `msk-1-vm-ngf0`.
- Decided to use an IDE AI assistant via OpenRouter instead of terminal-only flow.
- Goal: stop losing development context and stabilize the Pith core runtime.

- **Risk:** Low — workflow change only, no code impact.
- **Rollback:** Вернуть предыдущий workflow.
- **Docs:** `PITH_DEV_CONTEXT.md`
- **Commit:** `workflow: switch to VS Code + Remote SSH for Pith development`

### [product] Product / runtime reality

- Main live user interface remains Viktor via Telegram.
- Dashboard is secondary for now.
- Current practical priority is not UI expansion, but stabilization of the core runtime.

- **Risk:** None — conceptual clarification.
- **Rollback:** N/A
- **Docs:** `docs/PITH_MASTER_PLAN.md`, `PITH_DEV_CONTEXT.md`
- **Commit:** `docs: clarify product/runtime reality priorities`

### [focus] Technical focus

- Defined immediate technical focus:
  1. Router + `config.yaml` + secrets alignment.
  2. Stable startup and behaviour of Viktor / Telegram pipeline.
  3. Clarifying `RuntimePlanner` and its interaction with Router and `MemoryManager`.

- **Risk:** None — planning only.
- **Rollback:** N/A
- **Docs:** `PITH_DEV_CONTEXT.md`, `docs/PITH_MASTER_PLAN.md`
- **Commit:** `docs: document immediate technical focus`

---

## Changelog rules (template for future entries)

When updating this file, follow this structure and rules.

### 1. Date block

- Каждый блок изменений начинается с даты в формате `YYYY-MM-DD`:

```markdown
---

## 2026-05-21
```

- Даты идут **вниз по файлу в обратном хронологическом порядке** (сначала свежие, потом старые).

### 2. Change entries within a date

Для каждой логической группы изменений добавляй заголовок вида:

```markdown
### [scope] short-title
```

Где:

- `scope` — одна из областей:
  - `docs` — документация,
  - `config` — конфиги / runtime-параметры,
  - `runtime` — ядро runtime/службы,
  - `interfaces` — Telegram/CLI/Web/HTTP,
  - `observability` — TraceStore, логи, метрики,
  - `eval` — Evaluation/Evaluator/корпуса,
  - `product` — продуктовые определения/позиционирование,
  - `workflow` — dev‑workflow/процессы,
  - `identity` — идентичность продукта/бренда,
  - другие области по мере необходимости, но по минимуму.
- `short-title` — короткое описание (1 строка, в стиле commit message).

Примеры:

```markdown
### [docs] PITH_MASTER_PLAN v5.4 — Product Focus + Governance + Scale Path
### [config] config.yaml v5.0.1-clean-grounded
### [observability] TraceStore v1 — minimal task-level backbone
```

### 3. Body: bullet list with details

Под каждым заголовком — маркированный список с конкретикой:

- Что изменено (файлы, модули, разделы доков).
- Как именно (1–3 уровня деталей).
- Зачем (краткая мотивация, если не очевидно).

Стиль:

- Короткие пункты.
- Без воды, но с достаточной инженерной точностью.
- Для крупных блоков допускается вложенный список.

### 4. Risk / Rollback / Docs / Commit

В конце каждого change entry обязателен мини‑блок:

```markdown
- **Risk:** Low | Medium | High — краткое пояснение.
- **Rollback:** Как откатить (файлы/команды/шаги).
- **Docs:** Список ключевых доков, которые описывают или опираются на изменение.
- **Commit:** Точный commit message (или несколько, если нужно).
```

Пример:

```markdown
- **Risk:** Medium — изменения в конфиге и runtime; требуется тестирование.
- **Rollback:** Вернуть `config.yaml.bak` и `interfaces/telegram_bot.py.bak`; перезапустить сервис.
- **Docs:** `config.yaml`, `interfaces/telegram_bot.py`, `docs/PITH_MASTER_PLAN.md#0.8`
- **Commit:** `config: v5.0.1-clean-grounded — governance guards + fcntl lock + prompt hardening`
```

Правила:

- `Risk` всегда есть. Если изменения только в документации — писать `Low` или `None` и явно указывать, что это doc‑only.
- `Rollback` описывает **реальный практический шаг**, а не абстрактное "revert in git".
- `Docs` помогает быстро найти контекст.
- `Commit` — как минимум один реальный commit message.

### 5. Scope for multi-area changes

Если изменение затрагивает несколько областей (runtime + docs и т.п.), можно:

- либо разделить на два заголовка в рамках одной даты:
  - `[runtime] ...`
  - `[docs] ...`
- либо указать комбинированный scope:

```markdown
### [runtime/docs] EvaluationRecord v1 — traceable contract
```

Рекомендуется **делить**, чтобы один блок соответствовал одной логической группе изменений.

### 6. Language and style

- Описания — **в прошедшем времени** ("Added", "Updated", "Fixed" / "Добавлен", "Обновлён", "Исправлен").
- Язык: технические сущности на английском (`TraceStore`, `EvaluationRecord`, `TaskService`), поясняющий текст — RU/EN микс, как удобно команде.

### 7. What NOT to put into changelog

В `PITH_CHANGELOG.md` не попадает:

- Чистые эксперименты/ветки, не дошедшие до main/staging.
- Временные ворк‑файлы и личные заметки.
- Мелкие refactor‑ы без изменения поведения, если они не важны для истории.

Если сомневаешься — лучше добавить краткую запись, но чётко обозначить `Risk: Low` и что это internal refactor.

---

> This changelog is a human-readable history of **meaningful changes** to
> the Pith runtime, configuration, governance, and documentation.  
> It is not auto-generated; every entry must be intentional and useful for
> future debugging, audits, and onboarding.

---

<div style="text-align: center; margin-top: 40px; color: #666;">

**Pith Lab · Москва · 2026**

*Версия 1.0 · Май 2026 · CONFIDENTIAL / INTERNAL*

</div>