# Pith Runtime Refactor Checklist v1

Scope: Phase 1–2 из `IMPLEMENTATION_ROADMAP_V1.md` — стабилизация ядра и workspace-substrate.[file:1219]

Цель: привести runtime в состояние, описанное в:

- `docs/PITH_KERNEL.md`
- `docs/ARCHITECTURE_NORTH_STAR.md`
- `docs/PITH_MASTER_PLAN.md`
- `docs/IMPLEMENTATION_ROADMAP_V1.md`

---

## 0. Meta

- [ ] Этот файл обновлён под текущую структуру репозитория.
- [ ] Любой завершённый пункт отражён в `PITH_CHANGELOG.md` (с датой и кратким описанием).
- [ ] Любые архитектурные отклонения от Kernel/North Star задокументированы в ADR/notes.

---

## 1. Model Plane & config/secrets hygiene

1.1 Registry & lanes

- [ ] Все прямые вызовы моделей проходят через `core/modelregistry.py` / `core/models.py`.[file:1219]
- [ ] В `modelregistry` есть явные **lanes/roles** (например: `chat_fast`, `chat_smart`, `tool_reasoner`, `embedding`).
- [ ] Каждому lane заданы:
  - модель(и),
  - приоритеты / fallback-порядок,
  - бюджетные лимиты (max cost / max tokens per task/workspace).

1.2 Конфиги и секреты

- [ ] `config.yaml` не содержит секретов (ключей, токенов).[file:1219]
- [ ] Все секреты живут в `.env` и/или `core/secrets.py`.
- [ ] `core/secrets.py` — единственная точка доступа к секретам для runtime.
- [ ] Существующие backup-файлы `config.yaml.bak.*` и `router.py.bak.*` задокументированы или удалены как legacy (если точно не нужны).

---

## 2. Router & RuntimePlanner

2.1 CognitionRouter

- [ ] `core/cognition_router.py`:
  - не содержит хардкода конкретных моделей,
  - использует lanes из `modelregistry`,
  - ведёт базовую статистику в `data/metrics/router_stats.json`.[file:1219]
- [ ] Для каждой ветки решения в Router есть понятный критерий (по типу задачи, длине, риску).

2.2 RuntimePlanner

- [ ] `core/runtime_planner.py` определяет `task_type` / `risk_level` для входящего Task.
- [ ] Planner чётко разделяет:
  - direct LLM запросы,
  - мультиагентный/многошаговый путь через `core/orchestrator.py`.
- [ ] Для каждого `task_type` есть:
  - выбранная топология в Cognition Graph,
  - список инструментов/skills, которые Planner может включать.

---

## 3. Orchestrator & agents

3.1 Orchestrator

- [ ] `core/orchestrator.py`:
  - не использует магических строк типa `"TERA"`, `"PLEX"` и т.п. в коде,
  - берёт список агентов из явной конфигурации (registry/список).
- [ ] Ошибки отдельных агентов не ломают всю задачу:
  - падение одного агента логируется, но не рушит общий план,
  - в результате ясно видно, какие агенты отработали, какие нет.

3.2 Agents (`tera`, `hex`, `coda`, `plex`)

- [ ] У каждого агента:
  - есть чёткий контракт (`process` / `process_async`, схемы ввода/вывода),
  - stub/legacy-логика заменена на реальные полезные действия (минимальный прод-бейзлайн).
- [ ] Оркестратор не знает деталей агентов, только их интерфейс.

---

## 4. Memory & traces

4.1 MemoryManager

- [ ] `core/memory_manager.py` / `core/memory/context.py`:
  - используют единую схему `MemoryRecord` (с полями `relevance_score`, `last_accessed`, `source_task`, `decay_policy`).[file:1219]
- [ ] Есть базовая политика forget/decay:
  - либо явно реализована,
  - либо описана TODO в коде с ссылкой на `docs/EVOLUTION.md` / Memory v2.

4.2 Episodes & traces

- [ ] `episodes.db` и `data/episodes.db` (если оба есть) согласованы или консолидированы (нет расщепления прод/тест без пояснения).[file:1219]
- [ ] Для каждой задачи создаётся хотя бы один `episode` / trace-запись.
- [ ] Структура trace:
  - `Semantic Trace` (человекочитаемое описание),
  - `Raw Trace` (сырые llm/tool вызовы)
  соответствует описанию в `docs/PITH_KERNEL.md`.

---

## 5. Evolution pipeline (eval → miner → patch planner → skill compiler)

- [ ] `core/evolution/evaluator.py` реализует:
  - базовый quality score,
  - context-use score,
  - risk/uncertainty signals.
- [ ] `core/evolution/failure_miner.py` может:
  - находить повторяющиеся failure patterns,
  - помечать кейсы для ручного ревью.
- [ ] `core/evolution/patch_planner.py`:
  - превращает failure patterns в patch-candidates,
  - различает: “patch код/конфигурации” vs “update skill/процедуры”.
- [ ] `core/evolution/skill_compiler.py`:
  - умеет собирать skill-definition из успешных/неуспешных эпизодов,
  - сохраняет skills в `skills/index.json` и/или отдельных файлов.

---

## 6. Workspace substrate & TaskService

- [ ] Есть `TaskService` (например, `core/services/task_service.py`), который:
  - создаёт `TaskRecord`,
  - обновляет статусы,
  - привязывает задачи к `Workspace`.
- [ ] Любой интерфейс (Telegram, HTTP) создаёт Task через TaskService, а не “голым” вызовом Router/Planner.
- [ ] `ArtifactStore` (файлы, отчёты, патчи) реализован как единый слой:
  - не менее одного места в коде, где все артефакты регистрируются и связываются с Task/Workspace.

---

## 7. Logging & observability

- [ ] `logs/*.log` имеют понятные источники (router, evolution, dashboard, miner и т.п.) и не дублируют друг друга без причины.[file:1219]
- [ ] Для LLM-вызовов есть:
  - лог (`llm_calls` или аналог),
  - связь с Task/Trace.
- [ ] В `dashboard.py` (или эквиваленте) можно увидеть:
  - список последних задач,
  - базовые стоимости по моделям,
  - хотя бы количество ошибок / failed episodes.

---

## 8. Safety & autonomy

- [ ] `autonomy.yaml` согласован с `docs/PITH_KERNEL.md` (уровни L0–L1 сейчас, L2+ только как план).[file:1219]
- [ ] `core/governance/patch_gate.py` и `core/governance/rollout_manager.py`:
  - не вызываются автоматически без флагов/конфигов,
  - имеют явные точки входа (CLI/скрипты) для ручного запуска.
- [ ] Любое потенциально опасное действие (запись в репо, прод-БД, внешние API) проходит через:
  - явный tool/skill с контрактом,
  - политику уровня Workspace/RuntimeConfig.

---

## 9. Runtime boundaries (router/planner/memory/evaluator)

- [ ] В коде нет “смазанных” границ между Router/Planner/Memory/Evaluator:
  - Router отвечает за lane/model selection,
  - Planner — за topology/steps,
  - Memory — за контекст и persistence,
  - Evaluator — за оценку качества/риска.
- [ ] В местах, где границы пока нарушены, есть явные TODO-комментарии с ссылками на соответствующий раздел `docs/PITH_KERNEL.md` или `docs/ARCHITECTURE_NORTH_STAR.md`.