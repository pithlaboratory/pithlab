# Pith Runtime Refactor Checklist v1

> **Purpose:** Пошаговый чеклист для стабилизации и рефакторинга runtime-слоя Pith: model plane, router/planner, memory/traces, workspace substrate, observability, safety, и runtime boundaries.  
> **Alignment:** Operational checklist для `docs/PITH_KERNEL.md`, `docs/PITH_ARCHITECTURE_NORTH_STAR_V2.md`, `docs/PITH_MASTER_PLAN.md`, `docs/IMPLEMENTATION_ROADMAP_V1.md`.  
> **Status:** `ACTIVE`  
> **Last updated:** 2026-05-12  
> **Owner:** Core Runtime Engineering

---

## 1. Purpose & Scope

Этот документ задаёт **практический runtime-checklist** для приведения Pith к целевому состоянию, описанному в Kernel, North Star, Master Plan и roadmap.

**Scope:** Phase 1–2 из `docs/IMPLEMENTATION_ROADMAP_V1.md` — стабилизация ядра, runtime boundaries, model plane, traces/memory и workspace substrate.

**Цели:**
- Убрать архитектурную размытость между Router / Planner / Memory / Evaluator.
- Привести runtime к каноническим runtime-объектам и управляемым границам.
- Снизить количество legacy-paths, backup-логики и скрытого хардкода.
- Сделать runtime наблюдаемым, проверяемым и эволюционируемым.
- Подготовить основу для дальнейшего evolution pipeline и governed autonomy.

---

## 2. Meta

- [ ] Этот файл обновлён под текущую структуру репозитория.
- [ ] Любой завершённый пункт отражён в `PITH_CHANGELOG.md` (с датой и кратким описанием).
- [ ] Любые архитектурные отклонения от Kernel / North Star задокументированы в ADR / notes.
- [ ] Если пункт пока не реализован, в коде есть явный TODO с привязкой к соответствующему doc/source of truth.

---

## 3. Model Plane & config/secrets hygiene

### 3.1 Registry & lanes

- [ ] Все прямые вызовы моделей проходят через `core/modelregistry.py` / `core/models.py`.
- [ ] В `modelregistry` есть явные **lanes / roles** (например: `chat_fast`, `chat_smart`, `tool_reasoner`, `embedding`).
- [ ] Каждому lane заданы:
  - модель(и),
  - приоритеты / fallback-порядок,
  - бюджетные лимиты (`max cost`, `max tokens per task/workspace`).

### 3.2 Configs & secrets

- [ ] `config.yaml` не содержит секретов (ключей, токенов).
- [ ] Все секреты живут в `.env` и/или `core/secrets.py`.
- [ ] `core/secrets.py` — единственная точка доступа к секретам для runtime.
- [ ] Backup-файлы `config.yaml.bak.*`, `router.py.bak.*` и аналогичные либо задокументированы как legacy, либо удалены.

---

## 4. Router & RuntimePlanner

### 4.1 CognitionRouter

- [ ] `core/cognition_router.py`:
  - не содержит хардкода конкретных моделей,
  - использует lanes из `modelregistry`,
  - ведёт базовую статистику в `data/metrics/router_stats.json`.
- [ ] Для каждой ветки решения в Router есть понятный критерий: task type, длина, риск, стоимость, latency budget.

### 4.2 RuntimePlanner

- [ ] `core/runtime_planner.py` определяет `task_type` / `risk_level` для входящего Task.
- [ ] Planner чётко разделяет:
  - direct LLM path,
  - multi-step / multi-agent path через `core/orchestrator.py`.
- [ ] Для каждого `task_type` есть:
  - выбранная topology в cognition graph,
  - допустимые tools / skills,
  - rule-set для escalation / fallback.

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

### 5.2 Agents (`tera`, `hex`, `coda`, `plex`)

- [ ] У каждого агента есть чёткий контракт: `process` / `process_async`, схемы ввода/вывода, минимальные guarantees.
- [ ] Stub / legacy-логика заменена на минимальный полезный production baseline.
- [ ] Orchestrator знает только интерфейс агента, а не его внутренние детали.

---

## 6. Memory & traces

### 6.1 MemoryManager

- [ ] `core/memory_manager.py` / `core/memory/context.py` используют единую схему `MemoryRecord`.
- [ ] В схеме есть поля:
  - `relevance_score`,
  - `last_accessed`,
  - `source_task`,
  - `decay_policy`.
- [ ] Есть базовая политика forget / decay:
  - либо реализована,
  - либо отмечена как TODO с ссылкой на `docs/EVOLUTION.md` / Memory v2.

### 6.2 Episodes & traces

- [ ] `episodes.db` и `data/episodes.db` (если оба существуют) согласованы или консолидированы.
- [ ] Для каждой задачи создаётся хотя бы один `episode` / trace record.
- [ ] Структура trace соответствует `docs/PITH_KERNEL.md`:
  - `Semantic Trace` — человекочитаемое описание,
  - `Raw Trace` — сырые llm / tool вызовы.

---

## 7. Evolution pipeline

- [ ] `core/evolution/evaluator.py` реализует:
  - базовый quality score,
  - context-use score,
  - risk / uncertainty signals.
- [ ] `core/evolution/failure_miner.py`:
  - находит повторяющиеся failure patterns,
  - помечает кейсы для ручного review.
- [ ] `core/evolution/patch_planner.py`:
  - превращает failure patterns в patch candidates,
  - различает patch code/config vs update skill/procedure.
- [ ] `core/evolution/skill_compiler.py`:
  - собирает skill definitions из эпизодов,
  - сохраняет их в `skills/index.json` и/или отдельных skill-файлах.

---

## 8. Workspace substrate & TaskService

- [ ] Есть `TaskService` (например, `core/services/task_service.py`), который:
  - создаёт `TaskRecord`,
  - обновляет статусы,
  - привязывает задачи к `Workspace`.
- [ ] Любой интерфейс (Telegram, HTTP, CLI) создаёт Task через `TaskService`, а не “голым” вызовом Router / Planner.
- [ ] `ArtifactStore` реализован как единый слой регистрации артефактов и их связи с Task / Workspace.

---

## 9. Logging & observability

- [ ] `logs/*.log` имеют понятные источники (router, evolution, dashboard, miner и т.п.) и не дублируют друг друга без причины.
- [ ] Для LLM-вызовов есть:
  - лог (`llm_calls` или аналог),
  - связь с Task / Trace.
- [ ] В `dashboard.py` (или эквиваленте) видны:
  - последние задачи,
  - базовые стоимости по моделям,
  - количество ошибок / failed episodes.

---

## 10. Safety & autonomy

- [ ] `autonomy.yaml` согласован с `docs/PITH_KERNEL.md` (L0–L1 сейчас, L2+ только как future plan).
- [ ] `core/governance/patch_gate.py` и `core/governance/rollout_manager.py`:
  - не запускаются автоматически без флагов / конфигов,
  - имеют явные CLI / script entry points.
- [ ] Любое потенциально опасное действие (запись в repo, prod DB, внешние API) проходит через:
  - явный tool / skill с контрактом,
  - policy уровня Workspace / RuntimeConfig.

---

## 11. Runtime boundaries

- [ ] В коде нет смазанных границ между Router / Planner / Memory / Evaluator:
  - Router отвечает за lane / model selection,
  - Planner — за topology / steps,
  - Memory — за context и persistence,
  - Evaluator — за quality / risk assessment.
- [ ] В местах, где границы пока нарушены, есть явные TODO-комментарии с ссылками на соответствующий раздел `docs/PITH_KERNEL.md` или `docs/PITH_ARCHITECTURE_NORTH_STAR_V2.md`.

---

## 12. Exit Criteria

Checklist может считаться завершённым для текущей фазы, если:

- [ ] runtime-слой перестал зависеть от скрытых legacy-paths и backup-логики;
- [ ] Planner, Router, Memory, Evaluator и Orchestrator имеют явные границы ответственности;
- [ ] model lanes, traces, task/workspace binding и artifact registration работают как единая система;
- [ ] базовые governance / safety constraints соответствуют `PITH_KERNEL`;
- [ ] все завершённые изменения отражены в changelog и/или ADR.