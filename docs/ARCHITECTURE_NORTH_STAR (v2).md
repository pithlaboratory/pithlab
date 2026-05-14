# Pith Architecture North Star v2

> **Purpose:** Single source of truth for Pith's architectural vision, product boundaries, and directional build logic.  
> **Status:** `ACTIVE` — supersedes previous North Star drafts.  
> **Last updated:** 2026-05-14  
> **Owner:** Pith Lab (Internal)

---

## 1. Purpose & Core Identity

Pith — это **self-improving continuity runtime и Agent Company OS** для длинных когнитивных и инженерных задач внутри workspace’ов.

Его задача — не отвечать на единичные промпты, а вести работу во времени: задачи, контекст, память, артефакты, навыки, департаменты агентов и решения внутри одного управляемого, наблюдаемого и контролируемого контура.

Pith не привязан к одной модели или одному вендору.  
Это **слой над моделями, памятью, агентами и инструментами**; их можно менять, не ломая continuity, архитектуру и дисциплину исполнения.

**Core one‑liner:**

> **Chat solves prompts. Pith solves continuity.**  
> **Agent tools do actions. Pith runs the company of agents around your workspaces.**

---

## 2. North Star Goal

На текущем горизонте Pith должен стать устойчивым **runtime‑first cognitive operating layer + Agent Company OS**, в котором:

1. Несколько типов агентов, департаментов и execution paths работают через один Core Runtime и общую governed state model.
2. Любая работа живёт в `Workspace / Task / Workflow / Artifact / MemoryRecord / Trace`, а не «где‑то в чате».
3. Система может накапливать reusable execution patterns, department workflows и policies, а не только выдавать разовые ответы.
4. Эволюция моделей, промптов, skills и политик идёт только через governance: версии, traces, evaluation, canary, rollback.
5. Есть минимально надёжный runtime‑substrate, пригодный для long‑running work в реальных workspace‑сценариях.
6. Поверх runtime поднимается **цифровая компания из агентов** (Agent Company OS) с департаментами (research, sales, marketing, delivery, ops), работающими поверх общего continuity‑слоя.
7. Наблюдаемость, оценка качества, governance и deployment‑модель встроены в архитектуру, а не подвешены сбоку.

---

## 3. Core Promise

Pith делает сложную работу **continuous, accumulative, governable и observable**.

| Принцип | Значение |
|---------|----------|
| **Continuous** | Работа не обнуляется между сессиями, интерфейсами, моделями и агентами. Контекст не нужно проговаривать заново. |
| **Accumulative** | Каждый запуск оставляет след: артефакт, память, trace, навык, улучшенную политику или execution‑pattern. |
| **Governable** | Поведение системы наблюдаемо и под контролем: трассировка, версии, политики, budget‑лимиты, autonomy‑tiers и approval‑матрица. |
| **Observable** | Видно не только “что вышло”, но и “как прошли решения”: planner, orchestrator, департаменты, tools, memory, стоимость, ошибки. |

---

## 4. Product Test & One‑Liner

**Product Test:**  
Любая часть системы проходит проверку: *усиливает ли она continuity, reusable execution, workspace state, artifact flow, observability, evaluation или control over long‑running work и агентные департаменты?* Если нет — это может быть полезный модуль, но это не ядро Pith.

**Guiding One‑Liner:**

> **Chat solves prompts. Pith solves continuity.**  
> **Pith vNext solves continuity, capability accumulation, governed intelligence and agent departments inside workspaces.**

---

## 5. Anti‑Goals

Pith **не должен** становиться:

- ❌ Ещё одним LLM‑чатом (даже «с хорошей памятью»).
- ❌ Telegram‑ботом как продуктом (Telegram — только один из интерфейсов).
- ❌ «Зоопарком» агентов, где ценность — количество ролей/персон, а не их связность, качество и воспроизводимость.
- ❌ Системой неконтролируемой автоэволюции (изменения без observability, evaluation и rollback).
- ❌ Декоративной AI‑надстройкой к Notion/Jira/Slack/CRM без самостоятельного runtime‑ядра.
- ❌ UI‑first shell без integrity runtime underneath.
- ❌ “Agent framework” без жёсткой связи с workspaces, memory, traces и governance.

Pith — это ядро и операционный слой, вокруг которого живут интерфейсы, агенты, UI, API и интеграции, а не наоборот.

---

## 6. System Layers

Слои North Star архитектуры:

| Слой | Назначение | Ключевые компоненты |
|------|-----------|---------------------|
| **1. Core Runtime** | Оркестрация, планирование, маршрутизация, память, базовая оценка | Runtime Planner, Router, Orchestrator, Memory Manager, Evaluator, Runtime Services |
| **2. State Layer** | Реальность и continuity. Канонические сущности | Tenant, Workspace, Task, Workflow, Artifact, MemoryRecord, Trace, RuntimeVersion, PolicyDecision, User |
| **3. Capability Layer** | Расширяемые операции и skills | Web research, repo reading, coding/refactor, planning, tool/action integrations, department‑specific skills |
| **4. Agent Company Layer** | Цифровые департаменты и workflow‑команды | Department registry (Sales, Marketing, Research, Delivery, Support/Ops), department agents, workflow definitions, billable events |
| **5. Governance Layer** | Контроль, безопасность, политика и бюджет | Observability, evaluation, rollout/canary/revert, autonomy tiers, action classes, approvals, budget/risk policies |
| **6. Interface Layer** | Точки входа, но не identity Pith | Telegram, REST API / FastAPI, Dashboard / Operator Console, CLI, IDE integrations |

---

## 7. Bounded Contexts

| Контекст | Фокус |
|----------|-------|
| **Execution** | Запуск задачи, orchestration, routing, вызовы tools/skills, lifecycle, департаментные workflows |
| **Workspace** | Проекты, user‑boundaries, файлы, репозитории, artifacts, task/workflow history |
| **Memory** | Эпизодическая и долговременная память, semantic recall, continuity пользователя и workspace |
| **Capability** | Skills, tools, repo/web intelligence, reusable процедуры и department‑abilities |
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
| `Workflow` | Связанная цепочка шагов/департаментов/агентов |
| `Artifact` | Результат: файл, summary, patch, отчёт, решение, кампания |
| `MemoryRecord` | Сохраняемый контекст и continuity‑substrate |
| `Trace` | Наблюдаемая история reasoning / execution path / governance events |
| `Skill` | Версионируемая reusable процедура / способность |
| `PolicyDecision` | Зафиксированное governance‑решение |
| `Evaluation` | Оценка качества, риска, успеха, регресса |
| `RuntimeVersion` | Версия поведения / конфигурации runtime |
| `Department` | Логический отдел агентной компании (Sales, Marketing, Research, Delivery, Support/Ops) |
| `BillableEvent` | Бизнес‑событие для монетизации и cost‑аналитики |
| `User` | Человек или сервис‑клиент |

---

## 9. Operating Loop

Высокоуровневый цикл исполнения:

1. Interface получает запрос / цель.
2. Workspace Resolver определяет контекст (`tenant`, `workspace`, `user`).
3. Task Service создаёт/обновляет `Task` и, при необходимости, `Workflow`.
4. Context Assembler собирает `memory + artifacts + repo/web/file context` внутри workspace.
5. Runtime Planner / Router выбирает режим (direct vs orchestrated), topology, model lane, tools, skills и, при необходимости, департаменты.
6. Orchestrator / Execution Engine исполняет задачу через model plane, tool plane и department workflows.
7. Evaluator оценивает результат (качество, риск, стоимость, регресс, business outcome).
8. Artifact Service сохраняет output в `ArtifactStore`.
9. Memory Manager записывает continuity‑информацию в `MemoryRecord` с учётом workspace и политик.
10. Observability / Trace / Policy Engine фиксируют decision path, cost, governance‑сигналы и billable events.

Принципы:

- цикл логически event‑driven;
- каждый шаг оставляет явный след;
- шаги по возможности идемпотентны;
- департаментные операции не ломают единый trace и workspace‑scope.

---

## 10. Core vs Non‑Core

| ✅ Core для Pith | ⚠️ Важно, но не identity |
|------------------|--------------------------|
| Workspaces, Tasks, Workflows, Artifacts | Telegram UX, конкретные LLM‑вендоры |
| Memory, Planner / Router / Orchestrator | Dashboard polish и UI‑бриллианты |
| Evaluator / Policies / Governance | Persona‑слои и стилистика |
| Observability, Traces, ExecutionResult | Отдельные каналы доставки |
| Agent Company Layer (департаменты, workflows, billable events) | Разнообразие “персон” и аватарок |
| Governed execution runtime | Repo/web intelligence как capability expansion |

---

## 11. Phased Build

| Фаза | Цель | Ключевые deliverables |
|------|------|----------------------|
| **Phase 1 — Core Stabilization** | Управляемый runtime без хардкода | `model_registry`, secrets hygiene, canonical task lifecycle, TraceStore v1, чёткие границы router/planner/memory/evaluator |
| **Phase 2 — Workspace Substrate** | Работа живёт в workspace | `WorkspaceService`, `TaskService`, `ArtifactStore`, unified workspace/task/workflow state |
| **Phase 3 — Governance Baseline** | Наблюдаемость и контроль | `docs/PITH_OBSERVABILITY_V1.md`, `docs/PITH_EVALUATION_V1.md`, `docs/PITH_GOVERNANCE_V1.md`, evaluation schema, `runtime_versions` / `patch_candidates`, rollback hooks, budget/risk policies, operator view v1 |
| **Phase 4 — Capability & Agent Company** | Накопление способностей и департаментов | `SkillRegistry`, `docs/PITH_AGENT_COMPANY_V1.md`, department registry, mining успешных/провальных tasks, review‑pipeline → approve/reject → rollout |
| **Phase 5 — Intelligence Expansion** | Контекст без потери управляемости | `RepoIndexer`, `ContextRetriever`, WebResearch/WebMonitor, `DocumentIngestor`, autonomy boundaries по департаментам |
| **Phase 6 — Deployment & Enterprise Readiness** | Готовность к более строгим средам | `docs/PITH_DEPLOYMENT_MODEL_V1.md`, упрочнение workspace/tenant isolation, data categories, базовая retention/deletion story |

vNext направление продолжает эти фазы, а не заменяет их:

- Kernel Hardening  
- Workspace OS  
- Governance Core  
- Capability & Department Engine  
- Intelligence Fabric  
- Operator Experience & Modalities  
- Governed Autonomy & Monetization

---

## 12. Autonomy Boundaries & Draft Levels

Автономность — не данность, а то, что зарабатывается после observability и governance.

**На v1 / v5.1 недопустимы без жёсткого review и governance:**

- runtime self‑modification,
- automatic code patch rollout,
- unrestricted external actions,
- критичные prod‑изменения,
- uncontrolled agent/department spawning,
- high‑impact send/publish/spend/delete.

Уровни:

| Level | Название | Описание |
|-------|----------|----------|
| `L0` | Manual | Pith предлагает, человек исполняет. |
| `L1` | Assisted | Безопасные действия без внешних side‑effects (черновики, отчёты, локальные артефакты). |
| `L2` | Supervised | Ограниченные внешние действия по approved policy и с понятной трассировкой (draft PR, задачи, обновление систем с review). |
| `L3` | Auto / Canary | Изменения внешних систем только через canary‑rollout, чёткие метрики и жёсткий governance. |
| `L4` | High Autonomy (rare) | Только для узких, полностью проверенных workflows под строгими ограничениями. |

Текущий допустимый рабочий режим: **L0–L1**, постепенный переход в L2 для узких, хорошо наблюдаемых сценариев.

---

## 13. Mental Model

- `Chat` = interaction surface  
- `Pith` = continuity substrate + orchestration runtime + governance  
- `Agent Company` = организованный слой департаментов и workflows поверх Pith  
- `Skills / tools` = исполнители внутри управляемого runtime  
- `Governance` = безопасность, экономика, воспроизводимость, одобрения  
- `Workspace` = unit of reality и основная граница контекста  
- `Tenant` = внешняя бизнес‑граница клиента

> Pith — не бот с памятью.  
> Pith — это **workspace‑native orchestration runtime + Agent Company OS для continuity‑driven работы**,  
> который эволюционирует под наблюдением, управляется политиками и остаётся объяснимым.

