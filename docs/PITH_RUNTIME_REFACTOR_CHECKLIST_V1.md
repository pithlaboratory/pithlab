# Pith Runtime Refactor Checklist v1

> **Purpose:** Пошаговый чеклист для стабилизации и рефакторинга runtime‑слоя Pith: model plane, router/planner, memory/traces, workspace substrate, observability, safety и runtime boundaries.  
> **Alignment:** Operational checklist для `docs/PITH_KERNEL.md`, `docs/ARCHITECTURE_NORTH_STAR (v2).md`, `docs/PITH_MASTER_PLAN.md`, `docs/IMPLEMENTATION_ROADMAP_V1.md`, `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`, `docs/PITH_OBSERVABILITY_V1.md`, `docs/PITH_EVALUATION_V1.md`, `docs/PITH_GOVERNANCE_V1.md`.  
> **Status:** `ACTIVE`  
> **Last updated:** 2026‑05‑14  
> **Owner:** Core Runtime Engineering

---

## 1. Purpose & Scope

Этот документ задаёт **практический runtime‑checklist** для приведения Pith к целевому состоянию, описанному в Kernel, North Star, Master Plan, Runtime Context Protocol, Observability, Evaluation и Governance.

**Scope:** Phase 1–2 из `docs/IMPLEMENTATION_ROADMAP_V1.md` — стабилизация ядра, runtime boundaries, model plane, traces/memory, workspace substrate и базовый governance/evaluation.

**Цели:**

- Убрать архитектурную размытость между Router / RuntimePlanner / Memory / Evaluator / Orchestrator.
- Привести runtime к каноническим runtime‑объектам и управляемым границам (Tenant / Workspace / Task / Workflow / Artifact / Trace / RuntimeConfig).
- Снизить количество legacy‑paths, backup‑логики и скрытого хардкода.
- Сделать runtime наблюдаемым, проверяемым и эволюционируемым (по OBS/EVAL).
- Подготовить основу для evolution pipeline и governed autonomy (L0–L1).

---

## 2. Meta

- [ ] Этот файл обновлён под текущую структуру репозитория.
- [ ] Любой завершённый пункт отражён в `PITH_CHANGELOG.md` (с датой и кратким описанием).
- [ ] Любые архитектурные отклонения от Kernel / North Star / Runtime Context Protocol / OBS / EVAL / GOV задокументированы в ADR / notes.
- [ ] Если пункт пока не реализован, в коде есть явный TODO с привязкой к соответствующему doc/source of truth.

---

## 3. Model Plane & config/secrets hygiene

### 3.1 Registry & lanes

- [ ] Все прямые вызовы моделей проходят через Model Plane (`core/modelregistry.py` / `core/models.py`).
- [ ] В `modelregistry` есть явные **lanes / roles** (например: `chat_fast`, `chat_smart`, `tool_reasoner`, `embedding`).
- [ ] Каждому lane заданы:
  - модель(и),
  - приоритеты / fallback‑порядок,
  - бюджетные лимиты (`max cost`, `max tokens per task/workspace`), согласованные с `PITH_GOVERNANCE_V1.md`.

### 3.2 Configs & secrets

- [ ] `config.yaml` не содержит секретов (ключей, токенов).
- [ ] Все секреты живут в `.env` и/или `core/secrets.py`.
- [ ] `core/secrets.py` — единственная точка доступа к секретам для runtime.
- [ ] Backup‑файлы `config.yaml.bak.*`, `router.py.bak.*` и аналогичные либо задокументированы как legacy, либо удалены.

---

## 4. Router & RuntimePlanner

### 4.1 CognitionRouter

- [ ] `core/cognition_router.py`:
  - не содержит хардкода конкретных моделей,
  - использует lanes из Model Plane,
  - ведёт базовую статистику в `data/metrics/router_stats.json`.
- [ ] Для каждой ветки решения в Router есть понятный критерий: `task_type`, длина, риск, стоимость, latency budget.
- [ ] Router не нарушает Kernel‑границы: не делает planning, не лезет в память, не решает governance.

### 4.2 RuntimePlanner

- [ ] `core/runtime_planner.py`:
  - определяет `task_type`, `runtime_mode` (`NORMAL` / `DIAGNOSTICS` / `VISION`) и `risk_level` для входящего Task по `PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`;
  - выбирает autonomy level (L0–L1) в рамках текущего `RuntimeConfig`.
- [ ] Planner чётко разделяет:
  - direct LLM path,
  - multi‑step / multi‑agent path через `core/orchestrator.py`.
- [ ] Для каждого `task_type` есть:
  - выбранная topology в cognition graph,
  - допустимые tools / skills,
  - rule‑set для escalation / fallback.
- [ ] Planner отдаёт заказ на контекст в `ContextAssembler` и логирует выбранный режим/контекстный профиль в TraceStore (см. OBS v1).

---

## 5. Orchestrator & agents

### 5.1 Orchestrator

- [ ] `core/orchestrator.py`:
  - не использует магические строки типа `"TERA"`, `"PLEX"` и т.п. как источник оркестрационной логики,
  - берёт список агентов из явной конфигурации / registry.
- [ ] Ошибки отдельных агентов не ломают всю задачу:
  - падение одного агента логируется,
  - общий plan/result остаётся валидным,
  - видно, какие агенты отработали, какие нет.
- [ ] Orchestrator пишет ключевые шаги (step_id, parent_step_id, status, duration_ms, failure_class) в TraceStore в соответствии с `PITH_OBSERVABILITY_V1.md`.

### 5.2 Agents (`tera`, `hex`, `coda`, `plex`)

- [ ] У каждого агента есть чёткий контракт: `process` / `process_async`, схемы ввода/вывода, минимальные guarantees.
- [ ] Stub / legacy‑логика заменена на минимальный полезный production baseline.
- [ ] Orchestrator знает только интерфейс агента, а не его внутренние детали.
- [ ] Агенты не обходят ContextAssembler / Memory / Governance напрямую (никаких hidden side effects).

---

## 6. Memory, ContextAssembler & traces

### 6.1 MemoryManager

- [ ] `core/memory_manager.py` / `core/memory/context.py` используют единую схему `MemoryRecord` (см. Kernel / Runtime Context Protocol).
- [ ] В схеме есть поля:
  - `relevance_score`,
  - `last_accessed`,
  - `source_task`,
  - `decay_policy`.
- [ ] Есть базовая политика forget / decay:
  - либо реализована,
  - либо отмечена как TODO с ссылкой на `docs/EVOLUTION.md` / Memory v2.
- [ ] Memory operations логируются в TraceStore (read/write, scope, workspace filter) по OBS v1.

### 6.2 ContextAssembler

- [ ] Есть `ContextAssembler`, который собирает контекст по `PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`:
  - `system_policy`, `mode_block`, `task_intent`,
  - `recent_history`, `summary`,
  - `memory_records`, `artifacts`, `knowledge_context`, `trace_signals`.
- [ ] ContextAssembler:
  - уважает token budget и pruning order (dialog → summary → memory → artifacts → knowledge),
  - не нарушает policy / autonomy constraints,
  - не смешивает нерелевантный background с task‑critical context.
- [ ] `ContextAssembler` возвращает структурированный пакет, а не один сырой prompt string, и пишет `mode`, `autonomy_level`, `runtime_config_version`, counts и `pruning_applied` в TraceStore (OBS v1, секция 12).

### 6.3 Episodes & TraceStore v1

- [ ] `episodes.db` и `data/episodes.db` (если оба существуют) согласованы или консолидированы.
- [ ] Для каждой задачи создаётся хотя бы один trace record (`task_traces`), соответствующий минимальной схеме из `PITH_OBSERVABILITY_V1.md`:
  - `trace_id`, `tenant_id`, `workspace_id`, `task_id`, `runtime_mode`, `status`, `duration_ms`,
  - `failure_class`, `error_code`, `cost_estimate_usd`, `runtime_config_version`.

---

## 7. Evolution pipeline

- [ ] `core/evolution/evaluator.py` реализует:
  - базовый task success state (`success`, `partial_success`, `failure`, `rejected_after_review`),
  - quality score (accuracy/completeness/usefulness),
  - context‑use / persona drift / risk signals,
  - присвоение `failure_class` (routing/tool/memory/quality/etc.) по OBS/EVAL.
- [ ] `core/evolution/failure_miner.py`:
  - находит повторяющиеся failure patterns,
  - помечает кейсы для ручного review,
  - использует trace data и failure taxonomy.
- [ ] `core/evolution/patch_planner.py`:
  - превращает failure patterns в patch candidates,
  - различает patch code/config vs update skill/procedure,
  - ссылается на оценки из Evaluation (метрики/качественные сигналы).
- [ ] `core/evolution/skill_compiler.py`:
  - собирает skill definitions из эпизодов,
  - сохраняет их в `skills/index.json` и/или отдельных skill‑файлах,
  - не включает auto‑apply без Governance (PatchGate).

---

## 8. Workspace substrate & TaskService

- [ ] Есть `TaskService` (например, `core/services/task_service.py`), который:
  - создаёт `TaskRecord`,
  - обновляет статусы,
  - привязывает задачи к `Workspace` и `Tenant`.
- [ ] Любой интерфейс (Telegram, HTTP, CLI) создаёт Task через `TaskService`, а не “голым” вызовом Router / Planner.
- [ ] `ArtifactStore` реализован как единый слой регистрации артефактов и их связи с Task / Workflow / Workspace.
- [ ] Task/Artifact schema согласована с Kernel (`Task`, `Workflow`, `Artifact` как канонические сущности).

---

## 9. Logging & observability

- [ ] `logs/*.log` имеют понятные источники (router, evolution, dashboard, miner и т.п.) и не дублируют друг друга без причины.
- [ ] Для LLM‑вызовов есть:
  - лог (`llm_calls` или аналог),
  - связь с Task / Trace (через `trace_id` / `task_id` / `step_id`).
- [ ] В dashboard / observability surface видны:
  - последние задачи,
  - базовые стоимости по моделям/туллам,
  - количество ошибок / failed episodes,
  - базовые Evaluation‑сигналы (task success, failure_class, human override).

---

## 10. Safety & autonomy

- [ ] `autonomy.yaml` согласован с `docs/PITH_KERNEL.md` и `docs/PITH_GOVERNANCE_V1.md`:
  - активны только Tier 0–1 (L0–L1),
  - Tier 2+ описаны как future, но не включены.
- [ ] `core/governance/patch_gate.py` и `core/governance/rollout_manager.py`:
  - не запускаются автоматически без флагов / конфигов,
  - имеют явные CLI / script entry points,
  - логируют свои решения (allow / allow_with_constraints / require_approval / deny / escalate) в TraceStore.
- [ ] Любое потенциально опасное действие (запись в repo, prod DB, внешние API) проходит через:
  - явный tool / skill с контрактом,
  - policy engine / governance check на уровне Workspace / Tenant / RuntimeConfig.

---

## 11. Runtime boundaries

- [ ] В коде нет смазанных границ между Router / RuntimePlanner / ContextAssembler / Memory / Evaluator / Orchestrator:
  - Router отвечает за lane / model selection,
  - RuntimePlanner — за topology / steps / mode / autonomy_level,
  - ContextAssembler — за сборку контекста,
  - Memory — за persistence и retrieval,
  - Evaluator — за quality / risk assessment,
  - Orchestrator — за execution / agent orchestration.
- [ ] В местах, где границы пока нарушены, есть явные TODO‑комментарии с ссылками на соответствующий раздел `docs/PITH_KERNEL.md` или `docs/ARCHITECTURE_NORTH_STAR (v2).md`.

---

## 12. Exit Criteria

Checklist может считаться завершённым для текущей фазы, если:

- [ ] runtime‑слой перестал зависеть от скрытых legacy‑paths и backup‑логики;
- [ ] RuntimePlanner, Router, ContextAssembler, Memory, Evaluator и Orchestrator имеют явные границы ответственности;
- [ ] model lanes, traces, task/workspace binding и artifact registration работают как единая система;
- [ ] базовые governance / safety constraints соответствуют `PITH_KERNEL.md` и `PITH_GOVERNANCE_V1.md`;
- [ ] базовые Evaluation‑метрики (task success, human override rate, failure taxonomy, cost per workflow) начинают считаться из TraceStore;
- [ ] все завершённые изменения отражены в `PITH_CHANGELOG.md` и/или ADR.