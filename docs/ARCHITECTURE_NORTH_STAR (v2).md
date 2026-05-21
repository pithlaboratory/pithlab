# Pith Architecture North Star v2

> **Purpose:** Single source of truth for Pith's architectural vision, product boundaries, and directional build logic.  
> **Status:** `ACTIVE` — supersedes previous North Star drafts.  
> **Last updated:** 2026-05-21  
> **Owner:** Pith Lab (Internal)

---

## 1. Purpose & Core Identity

Pith — это **self-improving continuity runtime и workspace-native orchestration runtime** для длинных когнитивных и инженерных задач внутри workspace’ов. [file:14]

Его задача — не отвечать на единичные промпты, а вести работу во времени: задачи, контекст, память, артефакты, навыки, департаменты агентов и решения внутри одного управляемого, наблюдаемого и контролируемого контура.

Pith не привязан к одной модели или одному вендору.  
Это **слой над моделями, памятью, агентами и инструментами**; их можно менять, не ломая continuity, архитектуру и дисциплину исполнения. [file:14]

**Core one-liner:**

> **Chat solves prompts. Pith solves continuity.** [file:14]

В продуктовом плане (см. `PITH_MASTER_PLAN v5.4`) первым внешним продуктом поверх этого runtime является **Support/Ops Desk для B2B команд**; последующие desks и “Agent Company OS” строятся поверх уже работающего wedge. [file:14]

---

## 2. North Star Goal

На текущем горизонте Pith должен стать устойчивым **runtime-first cognitive operating layer + цифровой слой департаментов**, в котором: [file:14]

1. Несколько типов агентов, департаментов и execution paths работают через один Core Runtime и общую governed state model.
2. Любая работа живёт в `Workspace / Task / Workflow / Artifact / MemoryRecord / Trace`, а не «где‑то в чате». [file:14]
3. Система может накапливать reusable execution patterns, department workflows и policies, а не только выдавать разовые ответы.
4. Эволюция моделей, промптов, skills и политик идёт только через governance: версии, traces, evaluation, canary, rollback. [file:14]
5. Есть минимально надёжный runtime‑substrate, пригодный для long‑running work в реальных workspace‑сценариях.
6. Поверх runtime поднимаются **цифровые департаменты / desks** (Support/Ops → Back Office → Revenue и т.д.), работающие поверх общего continuity‑слоя. [file:14]
7. Наблюдаемость, оценка качества, governance и deployment‑модель встроены в архитектуру, а не подвешены сбоку. [file:14]

---

## 3. Core Promise

Pith делает сложную работу **continuous, accumulative, governable и observable**. [file:14]

| Принцип | Значение |
|---------|----------|
| **Continuous** | Работа не обнуляется между сессиями, интерфейсами, моделями и агентами. Контекст не нужно проговаривать заново. |
| **Accumulative** | Каждый запуск оставляет след: артефакт, память, trace, навык, улучшенную политику или execution-pattern. |
| **Governable** | Поведение системы наблюдаемо и под контролем: трассировка, версии, политики, budget-лимиты, autonomy-tiers и approval-матрица. |
| **Observable** | Видно не только “что вышло”, но и “как прошли решения”: planner, orchestrator, департаменты, tools, memory, стоимость, ошибки. |

---

## 4. Product Test & One-Liner

**Product Test:**  
Любая часть системы проходит проверку: *усиливает ли она continuity, reusable execution, workspace state, artifact flow, observability, evaluation или control over long-running work и агентные/desk‑уровневые департаменты?* Если нет — это может быть полезный модуль, но это не ядро Pith. [file:14]

**Guiding One-Liner:**

> **Chat solves prompts. Pith solves continuity.**  
> **Pith vNext solves continuity, capability accumulation, and governed intelligence inside workspaces.** [file:14]

---

## 5. Anti-Goals

Pith **не должен** становиться:

- ❌ Ещё одним LLM‑чатом (даже «с хорошей памятью»).
- ❌ Telegram‑ботом как продуктом (Telegram — только один из интерфейсов). [file:14]
- ❌ «Зоопарком» агентов, где ценность — количество ролей/персон, а не их связность, качество и воспроизводимость.
- ❌ Системой неконтролируемой автоэволюции (изменения без observability, evaluation и rollback). [file:14]
- ❌ Декоративной AI‑надстройкой к Notion/Jira/Slack/CRM без самостоятельного runtime‑ядра.
- ❌ UI‑first shell без integrity runtime underneath.
- ❌ “Agent framework” без жёсткой связи с workspaces, memory, traces и governance. [file:14]

Pith — это ядро и операционный слой, вокруг которого живут интерфейсы, агенты, UI, API и интеграции, а не наоборот.

---

## 6. System Layers

Слои North Star архитектуры: [file:14]

| Слой | Назначение | Ключевые компоненты |
|------|-----------|---------------------|
| **1. Core Runtime** | Оркестрация, планирование, маршрутизация, память, базовая оценка | Runtime Planner, Router, Orchestrator, Memory Manager, Evaluator, Runtime Services |
| **2. State Layer** | Реальность и continuity. Канонические сущности | Tenant, Workspace, Task, Workflow, Artifact, MemoryRecord, Trace, RuntimeVersion, PolicyDecision, User |
| **3. Capability Layer** | Расширяемые операции и skills | Web research, repo reading, coding/refactor, planning, tool/action integrations, department/desk‑specific skills |
| **4. Department / Desk Layer** | Цифровые департаменты и workflow‑команды | Department registry (Support/Ops, Back Office, Revenue, Research, Delivery), department agents, workflow definitions, billable events |
| **5. Governance Layer** | Контроль, безопасность, политика и бюджет | Observability, evaluation, rollout/canary/revert, autonomy tiers, action classes, approvals, budget/risk policies |
| **6. Interface Layer** | Точки входа, но не identity Pith | Telegram, REST API / FastAPI, Dashboard / Operator Console, CLI, IDE integrations |

---

## 7. Bounded Contexts

| Контекст | Фокус |
|----------|-------|
| **Execution** | Запуск задач, orchestration, routing, вызовы tools/skills, lifecycle, департаментные workflows |
| **Workspace** | Проекты, user-boundaries, файлы, репозитории, artifacts, task/workflow history |
| **Memory** | Эпизодическая и долговременная память, semantic recall, continuity пользователя и workspace |
| **Capability** | Skills, tools, repo/web intelligence, reusable процедуры и department/desk‑abilities |
| **Governance** | Evaluator, policies, approvals, rollout/rollback, autonomy tiers, budget/risk |
| **Delivery** | Telegram‑бот, API adapters, dashboard / operator UI, CLI, notifications, entrypoints |
| **Deployment** | Tenant/workspace isolation, data categories, secrets, hosting scenarios |

---

## 8. Canonical Entities

| Entity | Role |
|--------|------|
| `Tenant` | Высокоуровневая граница клиента/организации |
| `Workspace` | Контейнер долгоживущей рабочей реальности |
| `Task` | Единица исполнения и прогресса |
| `Workflow` | Связанная цепочка шагов/департаментов/agents |
| `Artifact` | Результат: файл, summary, patch, отчёт, решение, кампания |
| `MemoryRecord` | Сохраняемый контекст и continuity‑substrate |
| `Trace` | Наблюдаемая история reasoning / execution path / governance events |
| `Skill` | Версионируемая reusable процедура / способность |
| `PolicyDecision` | Зафиксированное governance‑решение |
| `Evaluation` | Оценка качества, риска, успеха, регресса |
| `RuntimeVersion` | Версия поведения / конфигурации runtime |
| `Department` / `Desk` | Логический отдел/desk (Support/Ops, Back Office, Research, Delivery, Revenue) |
| `BillableEvent` | Бизнес‑событие для монетизации и cost‑аналитики |
| `User` | Человек или сервис‑клиент |

---

## 9. Operating Loop

Высокоуровневый цикл исполнения: [file:14]

1. Interface получает запрос / цель.
2. Workspace Resolver определяет контекст (`tenant`, `workspace`, `user`).
3. Task Service создаёт/обновляет `Task` и, при необходимости, `Workflow`.
4. Context Assembler собирает `memory + artifacts + repo/web/file context` внутри workspace.
5. Runtime Planner / Router выбирает режим (direct vs orchestrated), topology, model lane, tools, skills и, при необходимости, департаменты / desk. [file:14]
6. Orchestrator / Execution Engine исполняет задачу через model plane, tool plane и department workflows.
7. Evaluator оценивает результат (качество, риск, стоимость, регресс, business outcome). [file:14]
8. Artifact Service сохраняет output в `ArtifactStore`.
9. Memory Manager записывает continuity‑информацию в `MemoryRecord` с учётом workspace и политик.
10. Observability / Trace / Policy Engine фиксируют decision path, cost, governance‑сигналы и billable events. [file:14]

Принципы:

- цикл логически event-driven;
- каждый шаг оставляет явный след;
- шаги по возможности идемпотентны;
- департаментные операции не ломают единый trace и workspace‑scope.

---

## 10. Core vs Non-Core

| ✅ Core для Pith | ⚠️ Важно, но не identity |
|------------------|--------------------------|
| Workspaces, Tasks, Workflows, Artifacts | Telegram UX, конкретные LLM-вендоры |
| Memory, Planner / Router / Orchestrator | Dashboard polish и UI‑бриллианты |
| Evaluator / Policies / Governance | Persona-слои и стилистика |
| Observability, Traces, ExecutionResult | Отдельные каналы доставки |
| Department / Desk Layer (департаменты, workflows, billable events) | Разнообразие “персон” и аватарок |
| Governed execution runtime | Repo/web intelligence как capability expansion |

---

## 11. Phased Build

Эта таблица дополняет Master Plan (§19, §27) на архитектурном уровне. [file:14]

| Фаза | Цель | Ключевые deliverables |
|------|------|----------------------|
| **Phase 1 — Core Stabilization** | Управляемый runtime без хардкода | `model_registry`, secrets hygiene, canonical task lifecycle, TraceStore v1/v1.1, чёткие границы router/planner/memory/evaluator |
| **Phase 2 — Workspace Substrate** | Работа живёт в workspace | `WorkspaceService`, `TaskService`, `ArtifactStore`, unified workspace/task/workflow state |
| **Phase 3 — Governance Baseline** | Наблюдаемость и контроль | `docs/PITH_OBSERVABILITY_V1.md`, `docs/PITH_EVALUATION_V1.md`, `docs/PITH_GOVERNANCE_V1.md`, evaluation schema, `runtime_versions` / `patch_candidates`, rollback hooks, budget/risk policies, operator view v1 |
| **Phase 4 — Capability & Departments** | Накопление способностей и департаментов | `SkillRegistry`, department/desk registry, mining успешных/провальных tasks, review‑pipeline → approve/reject → rollout |
| **Phase 5 — Intelligence Expansion** | Контекст без потери управляемости | `RepoIndexer`, `ContextRetriever`, WebResearch/WebMonitor, `DocumentIngestor`, autonomy boundaries по департаментам/desk’ам |
| **Phase 6 — Deployment & Enterprise Readiness** | Готовность к более строгим средам | `docs/PITH_DEPLOYMENT_MODEL_V1.md`, упрочнение workspace/tenant isolation, data categories, базовая retention/deletion story |

---

## 12. Autonomy Boundaries & Draft Levels

Автономность — не данность, а то, что зарабатывается после observability и governance (см. Kernel + Master Plan §10, §15, §22). [file:14]

На текущем v5.x:

- допустимы L0–L1, точечный L2 для узких, хорошо наблюдаемых сценариев;
- L3–L4 возможны только через явные gates (eval + governance + rollback). [file:14]

Уровни:

| Level | Название | Описание |
|-------|----------|----------|
| `L0` | Manual | Pith предлагает, человек исполняет. |
| `L1` | Assisted | Безопасные действия без внешних side-effects (черновики, отчёты, локальные артефакты). |
| `L2` | Supervised | Ограниченные внешние действия по approved policy и с трассировкой (draft PR, задачи, обновление систем с review). |
| `L3` | Auto / Canary | Изменения внешних систем только через canary-rollout, чёткие метрики и жёсткий governance. |
| `L4` | High Autonomy (rare) | Только для узких, полностью проверенных workflows под строгими ограничениями. |

---

## 13. Mental Model

- `Chat` = interaction surface  
- `Pith` = continuity substrate + orchestration runtime + governance [file:14]  
- `Departments / Desks` = организованный слой поверх Pith (Support/Ops Desk и последующие) [file:14]  
- `Skills / tools` = исполнители внутри управляемого runtime  
- `Governance` = безопасность, экономика, воспроизводимость, одобрения [file:14]  
- `Workspace` = unit of reality и основная граница контекста  
- `Tenant` = внешняя бизнес-граница клиента

> Pith — не бот с памятью.  
> Pith — это **workspace-native orchestration runtime для continuity‑driven работы**,  
> который эволюционирует под наблюдением, управляется политиками и остаётся объяснимым. [file:14]