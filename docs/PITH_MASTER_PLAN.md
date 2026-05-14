# PITH MASTER PLAN · v5.2

**Single source of truth: architecture, roadmap, guardrails.**  
**Last updated:** 2026‑05‑14 · **Status:** v5.2 / Runtime‑first baseline + Agent Company framing · **Owner:** Pith Lab

---

## 1. Vision

Pith — **self‑improving continuity runtime и Agent Company OS** для длинных инженерных и когнитивных задач.

Система:

- оркестрирует несколько агентов и внешние сервисы (Tool Plane, Model Plane),
- поддерживает непрерывность работы через Kernel / Workspace / Memory,
- умеет самоулучшаться через замкнутый evolution‑loop (failures → patches → skills),
- формирует виртуальные департаменты для автономного выполнения бизнес‑процессов.

**Цель v5:** стабильный, бюджет‑осознанный, конфигурируемый рантайм, который:

- живёт 24/7 на одном VPS,
- обслуживает несколько интерфейсов (Telegram, CLI, позже web),
- даёт ощущение «персонального CTO/Researcher/DevOps» + «цифрового отдела» поверх существующих workspaces.

---

## 2. Product North Star

**Primary user:** одиночный разработчик / маленькая инженерная команда / solopreneur.

**Primary use‑cases:**

- системная архитектура и агентные воркфлоу (AOS‑уровень, LangGraph‑style графы),
- сложный кодинг (репозитории, миграции, рефакторинг, runtime‑checklist),
- длительные и многошаговые задачи (исследование, планирование, мониторинг, лидогенерация).

**Core promise:** Pith делает работу **continuous, accumulative, governable** — не просто отвечает, а ведёт, контролирует и улучшает ход работы в рамках Workspace.

**Success criteria:**

- минимальный cognitive load при управлении агентами и моделями (router/config‑driven),
- предсказуемые расходы на LLM с budget‑guard’ами и трейсами,
- лёгкий онбординг нового окружения (новый репо, проект, стек) через Kernel/Workspace setup.

---

## 3. System Architecture (High‑Level)

### 3.1 Planes & Layers

Используем двухмерный взгляд: **planes** (что делает система) и **layers** (где это живёт).

**Planes:**

- **Runtime Plane** — операционный цикл: Intake → Task → Context → Plan → Execute → Evaluate → Persist → Trace.
- **Model Plane** — роутинг и вызовы LLM (OpenRouter, Timeweb, локальные модели).
- **Tool Plane** — MCP, shell, HTTP API, внутренние инструменты.
- **State Plane** — Tenant, Workspace, Task, Workflow, Artifact, MemoryRecord, User, RuntimeConfig.
- **Governance Plane** — TraceStore, PolicyDecision, Kill Switch, Autonomy levels.
- **Agent Company Plane** — Department registry, department agents, workflows, billable events.
- **Evolution Plane** — FailureMiner, PatchPlanner, PatchGate, RolloutManager, SkillCompiler.

**Core‑слои реализации:**

| Слой                  | Назначение                            | Ключевые компоненты                                                   |
|-----------------------|----------------------------------------|------------------------------------------------------------------------|
| **Interface Layer**   | Пользовательские интерфейсы           | Telegram, CLI, (позже) web dashboard                                  |
| **Cognition Layer**   | Принятие решений и планирование       | Router, RuntimePlanner, Orchestrator, Policy Engine                   |
| **Agent Company Layer** | Цифровые департаменты и workflows   | Department registry, Sales/Marketing/Research/Delivery/Ops agents     |
| **Execution Layer**   | Выполнение действий                   | Tools, MCP servers, shell, внешние API                                |
| **Memory Layer**      | Контекст и знания                     | MemoryManager, vector store, episodes, profiles                       |
| **Evolution Layer**   | Самоулучшение                         | Evaluator, FailureMiner, PatchPlanner, PatchGate, RolloutManager, SkillCompiler |

### 3.2 Главные компоненты v5

- `core/cognition/router.py` — LLM‑router: режимы, lanes, fallback, budget‑aware, candidate dedupe.
- `core/model_registry.json` — единственный реестр моделей, lanes и task_routes.
- `core/runtime/planner.py` — классификация `task_type`, выбор топологии (direct LLM vs orchestrator graph).
- `core/orchestrator.py` — координация агентов и A2A‑handoff, async fan‑out/fan‑in.
- `core/memory/manager.py` — Memory v2 (short‑term, episodic, semantic, profile) с namespace isolation и summarization.
- `core/evolution/*` — Evaluator, FailureMiner, PatchPlanner, SkillCompiler; связаны с episodes и runtime_versions.
- `interfaces/telegram_bot.py` — основной боевой интерфейс (Telegram, systemd‑service).
- `dashboard.py` (+ Streamlit) — вспомогательный dashboard для метрик/бюджетов.

### 3.3 Config‑Driven Runtime

Вынесено в `config.yaml` / `.config.*.yaml`:

- model lanes, task_routes и escalation rules (меняются без правки кода),
- budget лимиты и политики (monthly_usd, hard_stop, warning_threshold, premium‑reserve),
- persona directives, prefixes, loading‑messages для разных конфигов (engineer/coach/viktor),
- routing triggers (keywords, max_tokens, repo size, risk),
- параметры Memory (summarizer thresholds, forgetting policy, namespaces),
- настройки observability: пути для `router_stats.json`, `episodes.db`, лог‑файлы.

---

## 4. LLM Stack & Routing

### 4.1 Providers

- **Primary provider:** OpenRouter (multi‑model, multi‑vendor).
- **Reserve provider:** Timeweb (DeepSeek, Gemini, Qwen) для fallback/резерва.
- **Target state:** provider‑агностичный router — смена OpenRouter/Timeweb/локальной модели без переписывания ядра.

### 4.2 Registry (`core/model_registry.json`)

Единственный источник правды для:

- моделей (DeepSeek, Kimi, Qwen, Llama, Claude, Mistral и т.п.),
- lanes (chat_default, chat_fast, code_free, code_paid, reasoner_free, reasoner_paid…),
- task_routes (simple_chat, general_work, planning_reasoning, code_edit, repo_refactor…),
- escalation rules (по токенам, repo size, confidence, spend).

### 4.3 Router Modes & Lanes

| Mode           | Назначение                     | Примеры моделей (через lanes)                 |
|----------------|--------------------------------|-----------------------------------------------|
| **core**       | Общий reasoning / анализ       | `deepseek/deepseek-v4-flash`                  |
| **coder**      | Код / репозитории             | `qwen/qwen3-coder-plus`, `moonshot/kimi-k2.6` |
| **agent**      | Планирование и сложные воркфлоу | `moonshot/kimi-k2.6`                         |
| **free**       | Бесплатный слой               | `qwen/qwen3-coder:free`, `llama-3.3-70b:free` |
| **long_context** | Длинные тексты / репо       | `deepseek/deepseek-v4-flash (1M context)`     |
| **premium**    | High‑stakes ответы            | `anthropic/claude-3.5-sonnet`                 |

**Lane‑паттерн:** FAST, CORE, REASONING, EVAL, FREE_FALLBACK, RESERVE (Timeweb).

### 4.4 Candidate Formation (CORE mode)

1. Если `mode == core` → взять baseline‑кандидата из lane `chat_default`.
2. Добавить модели из `config.yaml` по режиму / `task_type`.
3. Если `prefer_free_first` → prepend free‑пул.
4. Применить `_dedupe_model_specs()` по `model_id`.
5. Итерировать кандидатов с учётом `max_paid_hops`, `budget_weight` и ошибок 4xx/5xx.

**Принципы:**

- Сначала бесплатный/дешёвый путь, затем эскалация.
- Жёсткие бюджет‑лимиты (`hard_stop: true`), отдельная квота premium‑моделей.
- Возможность явно указать модель/лану (override) в запросе.
- Graceful fallback по 404/429/5xx → следующая модель в цепочке.

### 4.5 Diagnostic Logging

- Ранний `logging.basicConfig()` до импорта ModelRegistry для детализированной загрузки.
- DEBUG в `model_registry.load()`: путь файла, top‑level keys, список lanes.
- Sanity‑check: `[lanes] CORE baseline candidate from chat_default lane: ...`.
- При ошибках — `KeyError` с перечислением доступных lanes/models.
- `router_stats.json` — агрегированные метрики по вызовам и fallback’ам.

---

## 5. Agent Topology & Agent Company

### 5.1 Базовые агенты

| Агент               | Назначение                                            | Контракт                              |
|---------------------|--------------------------------------------------------|----------------------------------------|
| **Tera (Researcher)** | Web‑research, сбор/нормализация внешней информации | `async process_async(query) → str`     |
| **Plex (Coherence)**  | Проверка связности, critique, clarification/planning | `process(query) → str`                |
| **Hex (Strategist)**  | Критика, риски, trade‑offs, foresight               | `async process_async(query) → str`     |
| **Coda (Executor)**   | Patch‑planning, next actions, execution framing     | `process(query) → str`                |

Агенты оформлены как модульные `AgentSpec` с контрактом и namespace‑политиками:

```python
@dataclass
class AgentSpec:
    name: str
    timeout_sec: int = 30
    max_tokens: int = 4096
    fallback_mode: Literal["stub", "skip", "error"] = "stub"
    required_tools: list[str] = field(default_factory=list)
```

Orchestrator вызывает агентов через `asyncio.gather(..., return_exceptions=True)` с graceful fallback по `fallback_mode`.

### 5.2 A2A / Topology

- Базовая модель — простая state machine / граф:  
  `User → Tera → Plex → Hex → Coda → User` (варианты сокращаются по необходимости).
- Следующий этап — полноценные графы (LangGraph‑style) с A2A‑handoff (AgentTask Protocol).
- Агентные топологии и права на инструменты/память описываются в registry (`agents_registry.yaml` / `autonomy.yaml`).

### 5.3 Agent Company Departments (Commercial Workflows)

| Департамент     | Агенты (примеры)                            | Что делают                                                   | Billable outcome                                  |
|-----------------|---------------------------------------------|--------------------------------------------------------------|---------------------------------------------------|
| **Sales**       | LeadFinder, Qualifier, Outreach             | Ищут лиды, квалифицируют, пишут касания, ведут pipeline      | Qualified leads, meetings, pipeline runs          |
| **Marketing**   | ICP Agent, Offer Agent, Copy Agent, Channel Agent, Analytics | Формируют ICP, офферы, контент, каналы, аналитику | Campaign packs, контент, отчёты                   |
| **Research**    | Market Agent, Competitor Agent, Trend Agent, Source Verifier | Рынки, конкуренты, тренды, факты                            | Research briefs, market maps                      |
| **Delivery**    | Builder, Reviewer, Doc, Launch Agent        | Собирают артефакты, проверяют качество, пакуют к запуску     | Launch kits, docs, packaged output                |
| **Support/Ops** | Support, Incident, Billing, Audit Agent     | Поддержка, инциденты, биллинг, аудит                         | SLA, incident reports, billing, governed execution |

---

## 6. Persistence & Memory (v2)

### 6.1 Типы памяти

| Тип          | Назначение                               | Реализация                 |
|--------------|------------------------------------------|----------------------------|
| **Short‑term** | Текущий диалог, локальный контекст     | RAM / session state        |
| **Episodic** | История запросов/ответов + метрики      | `episodes.db` (SQLite)     |
| **Semantic** | Факты, docs, repo‑фрагменты             | vector store + файловая система |
| **Profile**  | Профили пользователей/Workspace         | Profiles в SQLite / JSON   |

Дополнительно: **Medium‑term** (проектные файлы, чеклисты) в `MEMORY/` + git.

### 6.2 Memory v2 Features

- **Namespace isolation:** отдельные пространства памяти per agent / per workspace.
- **HierarchicalSummarizer:** raw turn → session summary → topic/workspace summary.
- **Forgetting policy:** эпизоды > N дней без ссылок архивируются.
- **Temporal validity + trust score** в метаданных каждого memory item.
- Ночной **consolidation loop** (`scripts/nightly_consolidation.py`).

---

## 7. Self‑Improvement Loop (v5)

### 7.1 Контур

1. Ответ пользователю.
2. **Evaluator** → weighted score (task_success, quality, context_use, disclaimer, cost).
3. **FailureMiner** → группировка сбоев по паттернам + гипотезы причин.
4. **PatchPlanner** → предложения патчей (JSON‑манифесты).
5. **PatchGate** → policy‑check (whitelist/canary/block).
6. **RolloutManager** → canary‑выкатка, наблюдение за регрессиями.
7. **RollbackMonitor** → авто‑откат при нарушении метрик.
8. **SkillCompiler** → успешные паттерны в `skills/index.json` и mined skills.
9. Следующий запрос → улучшенный контекст/навыки.

### 7.2 Артефакты

- `MEMORY/` — долговременные заметки и knowledge.
- `logs/*.log` — budget, routing, evolution, incidents.
- `skills/*.md` + `skills/index.json` — mined skills.
- Ключевые документы: `docs/MANIFESTO.md`, `docs/PRODUCT_DOCTRINE.md`, `docs/ARCHITECTURE_NORTH_STAR (v2).md`, `docs/PITH_KERNEL.md`, `PITH_CHANGELOG.md`.

---

## 8. Budget & Observability

### 8.1 Budget Policy

- `monthly_usd: 30.0` + soft‑limit + premium‑reserve.
- Отдельные лимиты на premium‑модели (Kimi, Claude, DeepSeek R1).
- `warning_threshold: 0.8` → алерт до `hard_stop`.
- При превышении лимита — принудительный переход на FREE‑модели (`hard_stop: true`).
- `max_premium_hops_per_day: 8`.

### 8.2 Метрики

| Категория   | Метрики                                           | Хранение        |
|-------------|----------------------------------------------------|-----------------|
| **Quality** | `task_completion_rate`, `human_override_rate`, `quality_score` | `episodes.db` |
| **System**  | `latency_p50/p95`, `fallback_rate`, `cache_hit_ratio`          | `router_stats.json` |
| **Economics** | `cost_per_task`, `quality_weighted_cost`, `budget_utilization` | `router_stats.json` |
| **Governance** | `approval_frequency`, `policy_violation_rate`              | `episodes.db` |
| **Evolution** | `patch_acceptance_rate`, `rollback_rate`, `skill_growth`    | `episodes.db` |

### 8.3 TraceStore & Traces

**TraceStore v1 (task‑level backbone) — уже реализован:**

- `task_traces` таблица в `episodes.db` (одна строка на `task_id`).
- `TaskService` пишет `task_started` / `task_finished` / `task_failed`.
- Используется для базовой атрибуции длительности задач и статуса (`ok` / `failed` / `cancelled`).

**Следующие шаги (TraceStore v1.1+):**

- per‑LLM‑call spans (link к `llm_calls`),
- per‑agent spans,
- evaluator score linkage,
- trace query/read API,
- billable event references.

### 8.4 Blocking Thresholds

| Условие                                   | Действие                                |
|-------------------------------------------|------------------------------------------|
| `task_completion_rate < 0.5` 2h подряд    | кандидат на откат патча                  |
| `cost_spike > 3x baseline` за 1h          | kill switch + алерт                      |
| `fallback_rate > 30%` за сессию           | принудительный switch на core lane       |

---

## 9. Interfaces (CLI, Telegram, Web)

### 9.1 Telegram

- Главный боевой интерфейс.
- Запущен как `pith_v5.service` на выделенном сервере (`msk-1-vm-ngf0`).
- Реализован на базе `python-telegram-bot`.
- Интерфейс не выполняет тяжёлые задачи локально; делегация в Runtime.

### 9.2 CLI

- Главный dev‑интерфейс: `pith ask`, `pith dev`, `pith incident`, `pith doc`.
- Удобный доступ к router‑debug, agent‑tests, incident‑analysis.

### 9.3 Web (v6‑target)

- Dashboard: метрики, бюджет, trace‑трейсировки.
- UI для настройки registry, lanes, routes.
- Визуализация agent‑графов и trace flow.

---

## 10. Roadmap (v5.2 → v6)

### 10.1 Short‑term (v5.x, 0–30 дней)

- Стабилизировать router + registry (lane‑first, dedupe, безопасный fallback).
- Завинтить диагностический logging в `model_registry.load()` и Router.
- Протянуть end‑to‑end self‑improvement loop (Evaluator → FailureMiner → PatchPlanner → SkillCompiler).
- Оформить `AgentSpec` для Tera, Plex, Hex, Coda.
- Реализовать namespace isolation в памяти.
- Довести TraceStore v1 до стабильного task‑level backbone (`task_traces`).
- Зафиксировать первые billable events для Agent Company (workflow, lead, campaign, brief).

### 10.2 Mid‑term (v5.y, 30–90 дней)

- Вынести workflows в декларативный формат (YAML/JSON), ближе к Agent Company OS.
- Добавить self‑eval/self‑critique для high‑stakes workflows.
- Встроить auto‑refactor / runtime‑checklist в CI.
- Расширить TraceStore (per‑LLM‑call spans, per‑agent spans, evaluator score linkage, billable event refs).
- Реализовать HierarchicalSummarizer.
- Запустить первую коммерческую вертикаль: Sales + Marketing + Research.
- Минимальный operator console: workflows, traces, approvals, billing.

### 10.3 Long‑term (v6, 90+ дней)

- Self‑evolving agent workflows с полным OBS/EVAL/GOV контуром.
- Авто‑обновление документации из runtime.
- Multi‑project orchestration на одном Pith‑ядре.
- Web dashboard с real‑time метриками, governance и department outcomes.
- Deployment model hardening: tenant/workspace isolation, data categories, retention/deletion.

Detaily по фазам: `docs/PITH_KERNEL.md` (Phase 1–6), `docs/PITH_ACTIVE_CONTEXT.md`.

---

## 11. Development Workflow & Checks

- **Smoke‑test:** `python core/cognition/router.py` с `OPENROUTER_KEY=dummy`.
- **Syntax check:** `python -m py_compile core/cognition/router.py`.
- **Lane diagnostics:** по логам `[registry]` / `[lanes]` / `[budget]`.
- **Budget guard test:** mock `spent_usd > limit` → проверка `hard_stop`.
- **Fallback test:** mock 404/429 → проверка переключения на следующую модель.
- **Commit rule:** любое изменение в router/registry/memory/Kernel отражается в `PITH_CHANGELOG.md` + этом master‑plan.

---

## 12. Guardrails & Non‑Goals

### 12.1 Guardrails

- Не превращать Pith в монолитный IDE/GUI.
- Не завязываться жёстко на одного LLM‑провайдера (provider‑agnostic router).
- Любая новая фича **testable** и **observable** (traces, metrics).
- **Reversibility by design:** любое автономное действие обратимо (rollback, kill switch).
- **Attribution:** каждое решение объяснимо через trace + manifest + scores.
- Autonomy только по мере накопления доверия (L0–L4, по Kernel).
- Agent Company не обходит Core Runtime и Governance.

### 12.2 Non‑Goals (для ближайших релизов)

- Full multi‑tenant SaaS UI.
- Универсальный no‑code builder «для всех кейсов».
- Полноценная MLOps‑платформа.
- AGI‑маркетинг; только прагматичный runtime поверх моделей.
- Одновременный запуск всех возможных департаментов.

---

## 13. Architecture Decision Records (ADR)

1. **Config‑driven routing & UI** — модели, префиксы, loading‑профили меняются без правки кода.
2. **Provider‑agnostic router** — отсутствие vendor lock‑in.
3. **Canonical runtime manifest** — по `trace_id` / `runtime_config_version` можно восстановить состояние системы.
4. **Official memory taxonomy** — Short‑term / Episodic / Semantic / Profile.
5. **Tool contracts standard** — JSON Schema для инструментов, versioning, validation.
6. **Blocking eval metrics** — `task_completion_rate < 0.5` и `cost_spike > 3x` блокируют.
7. **Safe autopatch boundaries** — только `risk=low`, `confidence>=0.8` автоприменяются.
8. **Ring policy (Canary)** — owner → canary (5%) → full, с rollback по метрикам.
9. **Unit of versioning** — весь манифест компонента: prompt + tools + memory_policy + model_lane.
10. **Kill switch path** — единая точка остановки автономных действий с audit log и per‑component freeze.
11. **Agent Company on top of Runtime** — департаменты и workflows не обходят Core Runtime, TraceStore и PolicyDecision.
12. **Workspace/Tenant isolation** — `workspace_id` и `tenant_id` first‑class в State Layer, трейсах и биллинге.

---

## 14. Philosophy (Kernel View)

Синхронизация с `docs/PITH_KERNEL.md` и `docs/PRODUCT_DOCTRINE.md`:

1. **Reversibility by design** — всегда есть путь назад (rollback, kill switch, trace‑driven postmortem).
2. **Attribution** — любое поведение привязано к артефактам (Trace, Manifest, Scores).
3. **Graduated autonomy** — L0 (manual) → L1 (assisted) → L2 (supervised) → L3 (canary auto) → L4 (high autonomy, редко).
4. **Continuity > feature‑zoo** — приоритет continuity / orchestration над количеством «фич».
5. **Runtime‑first** — интерфейсы и персоны — skin над ядром, а не драйвер архитектуры.
6. **Observable & Evaluable** — система видна изнутри и снаружи; нет «магии без объяснений».
7. **Agent Company поверх Runtime** — коммерческий слой, а не замена ядра.

**One‑liner:**

> Pith — self‑improving continuity runtime и Agent Company OS:  
> он не просто отвечает, а ведёт, контролирует, наблюдает и улучшает ход работы внутри ваших workspaces.

---

## 15. Governance of This Document

- **Файл:** `docs/PITH_MASTER_PLAN.md`.
- **Версионирование:** git tags (`v5.0`, `v5.1`, `v5.2`, ...).
- **Обновлять при:**
  - изменении LLM‑стека или routing‑политик,
  - значимых архитектурных решениях,
  - изменении product‑фокуса Pith,
  - запуске новых департаментов Agent Company.
- Перед любым крупным изменением — сверка с разделами 12 (Guardrails) и 14 (Philosophy).

---

## 16. Pith vNext

### 16.1 Purpose

**Pith vNext** — следующий этап развития Pith после runtime‑first baseline: переход от стабильного continuity runtime к **production‑grade cognitive operating layer и зрелой Agent Company OS**, который накапливает способности, работает с богатыми knowledge surfaces и даёт управляемую операторскую среду.

Pith vNext не меняет identity продукта. Он остаётся:

> **workspace‑native orchestration runtime и Agent Company OS for continuity‑driven long‑running work.**

**Roadmap‑формулировка:**

> **Pith vNext solves continuity, capability accumulation, governed intelligence and agent company operations inside workspaces.**

### 16.2 Core Idea

Pith vNext строится вокруг **семи контуров**, работающих как единая операционная среда:

1. **Kernel Runtime** — event‑driven operating loop, planner, router, evaluator, policy engine.
2. **Workspace Substrate** — tenants, workspaces, tasks, workflows, artifacts, memory, repo bindings.
3. **Capability System** — skills, tools, reusable procedures, agent contracts.
4. **Agent Company System** — department registry, department agents, billable events, commercial workflows.
5. **Intelligence System** — repo/docs/web ingestion, context retriever, multi‑source assembly.
6. **Governance System** — traces, runtime versions, policy decisions, rollback, approval queues, budgets.
7. **Experience Layer** — Telegram, CLI, dashboard, voice, operator shell.

### 16.3 What Pith vNext Adds

#### Repo & Knowledge Intelligence

- `RepoIndexer` — карта репозитория, зависимостей, архитектурных узлов.
- `ContextRetriever` — контекст из memory + repo + artifacts + docs + web.
- `DocumentIngestor` — ingestion для PDF / Markdown / HTML / notes.
- `WebResearch` / `WebMonitor` — внешний ресёрч и мониторинг как часть workspace toolset.

#### Capability Accumulation

- `SkillRegistry` и `SkillBinding`.
- Candidate skill mining из traces, tasks, failures и successful patterns.
- Review / approve / reject / rollout pipeline для новых skills.

#### Agent Company Maturity

- Полноценный department registry с agent roles и workflow definitions.
- Billable event pipeline с cost attribution по tenant/workspace/department.
- Operator console: workflows, approvals, department outcomes, billing.

#### Governed Agents

- `AgentSpec` для всех агентов.
- A2A / async delegation topology.
- Per‑agent namespaces и policy‑bound tool permissions.

#### Multimodality & Operator Experience

- Voice input/output как interface adapter.
- Multimodal ingestion (документы, изображения, скриншоты, схемы).
- Rich dashboard: traces, workspace navigation, artifact browser, policy views, agent graphs.

### 16.4 vNext Phase Map

| vNext Phase           | Focus                               | Main Outcome                                           |
|-----------------------|--------------------------------------|--------------------------------------------------------|
| **A. Kernel Hardening** | Добить предсказуемость ядра       | router/planner/memory/task correctness, stable trace  |
| **B. Workspace OS**   | Workspace как единица работы        | workspace CRUD, artifact/task/workflow schemas, unified runtime |
| **C. Governance Core**| Объяснимость и управляемость        | RuntimeConfig, policies, dashboard v1, rollback, cost attribution |
| **D. Agent Company v1** | Первая коммерческая вертикаль     | Sales+Marketing+Research workflows, billable events, operator console |
| **E. Capability Engine** | Накопление способностей         | SkillRegistry, agent contracts, reusable procedures, mining pipeline |
| **F. Intelligence Fabric** | Богатый контекст              | RepoIndexer, DocumentIngestor, WebResearch, ContextRetriever |
| **G. Experience & Modalities** | Зрелая операторская оболочка | rich dashboard, trace explorer, voice, multimodal shell |
| **H. Governed Autonomy** | Расширение автономии без потери контроля | reviewed L2 actions, policy‑bound semi‑auto execution |

### 16.5 Guardrails for vNext

- Not a chatbot with more modes.
- Not a memory‑only product.
- Not an AI add‑on inside somebody else’s workspace product.
- Not an ungoverned autonomous agent swarm.
- Not a UI‑first shell без runtime integrity underneath.

**Каждая новая capability в vNext должна проходить три теста:**

1. Улучшает ли она **continuity** или **capability accumulation**?
2. Остаётся ли она **governable и observable**?
3. Усиливает ли она **Agent Company value layer**?

### 16.6 One‑Line Framing

> **Chat solves prompts. Pith solves continuity.**  
> **Pith vNext solves continuity, capability accumulation, governed intelligence and agent company operations inside workspaces.**

---

<div style="text-align: center; margin-top: 40px; color: #666;">

**Pith Lab · Москва · 2026**

*Версия v5.2 · Май 2026 · CONFIDENTIAL / INTERNAL*

</div>