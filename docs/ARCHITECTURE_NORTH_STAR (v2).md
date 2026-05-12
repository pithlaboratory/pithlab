# Pith Architecture North Star v2

> **Purpose:** Single source of truth for Pith's architectural vision, product boundaries, and directional build logic.  
> **Status:** `ACTIVE` — supersedes previous North Star drafts.  
> **Last updated:** 2026-05-12  
> **Owner:** Pith Lab (Internal)

---

## 1. Purpose & Core Identity

Pith — это **self-improving continuity engine / workspace-native orchestration runtime** для длинных когнитивных и инженерных задач.

Его задача — не отвечать на единичные промпты, а вести работу во времени: задачи, контекст, память, артефакты, навыки и решения внутри одного управляемого контура.

Pith не привязан к одной модели или одному вендору. Это **слой над моделями, памятью и инструментами**; их можно менять, не ломая continuity и архитектуру.

**Core one-liner:**
> **Chat solves prompts. Pith solves continuity.**

---

## 2. North Star Goal

На текущем горизонте Pith должен стать устойчивым **runtime-first cognitive operating layer**, в котором:

1. Несколько типов агентов и execution paths работают через один Core Runtime и общую governed state model.
2. Любая работа живёт в `Workspace / Task / Artifact / MemoryRecord / Trace`, а не «где-то в чате».
3. Система может накапливать reusable execution patterns, а не только выдавать разовые ответы.
4. Эволюция моделей, промптов, skills и политик идёт только через governance: версии, traces, review, canary, rollback.
5. Есть минимально надёжный runtime substrate, пригодный для long-running work в реальных workspace-сценариях.

---

## 3. Core Promise

Pith делает сложную работу **continuous, accumulative и governable**.

| Принцип | Значение |
|---------|----------|
| **Continuous** | Работа не обнуляется между сессиями, интерфейсами и моделями. Контекст не нужно проговаривать заново. |
| **Accumulative** | Каждый запуск оставляет след: артефакт, память, trace, навык, улучшенную политику или знание. |
| **Governable** | Поведение системы наблюдаемо и под контролем: трассировка, версии, политики, budget-лимиты и понятные границы автономии. |

---

## 4. Product Test & One-Liner

**Product Test:**  
Любая часть системы проходит проверку: *усиливает ли она continuity, reusable execution, workspace state, artifact flow или control over long-running work?* Если нет — это может быть полезный модуль, но это не ядро Pith.

**Guiding One-Liner:**  
> **Chat solves prompts. Pith solves continuity.**

**vNext Framing:**  
> **Pith vNext solves continuity, capability accumulation and governed intelligence inside workspaces.**

---

## 5. Anti-Goals

Pith **не должен** становиться:

- ❌ Ещё одним LLM-чатом (даже «с хорошей памятью»).
- ❌ Telegram-ботом как продуктом (Telegram — только один из интерфейсов).
- ❌ «Зоопарком» агентов, где ценность — количество ролей, а не их качество и воспроизводимость.
- ❌ Системой неконтролируемой автоэволюции (изменения без observability и rollback).
- ❌ Декоративной AI-надстройкой к Notion/Jira/Slack.
- ❌ UI-first shell без integrity runtime underneath.

Pith — это ядро, вокруг которого живут боты, UI, API и интеграции, а не наоборот.

---

## 6. System Layers

| Слой | Назначение | Ключевые компоненты |
|------|-----------|-------------------|
| **1. Core Runtime** | Оркестрация, планирование, маршрутизация, память, оценка | Runtime Planner, Router, Orchestrator, Memory Manager, Evaluator, Policy Engine |
| **2. State Layer** | Реальность и continuity. Канонические сущности | Workspace, Task, Artifact, MemoryRecord, Trace, RuntimeVersion, PolicyDecision, User |
| **3. Capability Layer** | Расширяемые операции | Web research, repo reading, coding/refactor, planning, tool/action integrations, future skills |
| **4. Interface Layer** | Точки входа, но не identity Pith | Telegram, REST API / FastAPI, Dashboard, CLI, IDE integrations |
| **5. Governance Layer** | Контроль, безопасность, экономика | Observability, evaluation metrics, rollout/canary/revert, autonomy gates, budget/risk policies |

---

## 7. Bounded Contexts

| Контекст | Фокус |
|----------|-------|
| **Execution** | Запуск задачи, orchestration, routing, вызовы tools/skills, lifecycle |
| **Workspace** | Проекты, user boundaries, файлы, репозитории, artifacts, task history |
| **Memory** | Эпизодическая память, semantic recall, continuity пользователя и workspace |
| **Capability** | Skills, tools, repo/web intelligence, reusable procedures |
| **Governance** | Evaluator, policies, review/approval, rollout/rollback |
| **Delivery** | Telegram-бот, API adapters, dashboard UI, CLI, notifications, entrypoints |

---

## 8. Canonical Entities

| Entity | Role |
|--------|------|
| `Workspace` | Контейнер долгоживущей рабочей реальности |
| `Task` | Единица исполнения и прогресса |
| `Artifact` | Результат: файл, summary, patch, отчёт, решение |
| `MemoryRecord` | Сохраняемый контекст и continuity-substrate |
| `Trace` | Наблюдаемая история reasoning / execution path |
| `Skill` | Версионируемая reusable процедура / способность |
| `PolicyDecision` | Зафиксированное governance-решение |
| `Evaluation` | Оценка качества, риска, успеха, регресса |
| `RuntimeVersion` | Версия поведения / конфигурации runtime |
| `User` | Человек или сервис-клиент |

---

## 9. Operating Loop

1. Interface получает запрос.
2. Workspace Resolver определяет контекст (`workspace`, `user`).
3. Task Service создаёт `TaskRecord`.
4. Context Assembler собирает `memory + artifacts + repo/web/file context`.
5. Planner / Router выбирает topology, model lane, tools и skills.
6. Execution Engine исполняет задачу через model plane и tool plane.
7. Evaluator оценивает результат (качество, риск, стоимость, регресс).
8. Artifact Service сохраняет output в `ArtifactStore`.
9. Memory Manager записывает continuity-информацию в `MemoryRecord`.
10. Trace + Policy Engine фиксируют decision path и governance signals.

**Принципы:** цикл логически event-driven, каждый шаг оставляет явный след, шаги по возможности идемпотентны.

**Current trace baseline:** на v5.1 минимальная task-level реализация уже существует через `TraceStore v1` (`task_traces` в `episodes.db`), поверх которой далее наращиваются per-LLM-call и per-agent spans.

---

## 10. Core vs Non-Core

| ✅ Core для Pith | ⚠️ Важно, но не identity |
|------------------|--------------------------|
| Workspaces, Tasks, Artifacts | Telegram UX, конкретные LLM-вендоры |
| Memory, Planner / Router | Dashboard polish |
| Evaluator / Policies | Persona-слои и стилистика |
| Observability, Traces | Отдельные каналы доставки |
| Governed execution runtime | Repo/web intelligence как capability layer expansion |

---

## 11. Phased Build

| Фаза | Цель | Ключевые deliverables |
|------|------|----------------------|
| **Phase 1 — Core Stabilization** | Управляемый runtime без хардкода | `model_registry`, secrets hygiene, canonical task lifecycle, TraceStore v1, чёткие границы router/planner/memory/evaluator |
| **Phase 2 — Workspace Substrate** | Работа живёт в workspace | `WorkspaceService`, `TaskService`, `ArtifactStore`, unified workspace/task state |
| **Phase 3 — Governance Baseline** | Наблюдаемость и контроль | Evaluation schema, `runtime_versions` / `patch_candidates`, rollback hooks, budget/risk policies, Dashboard v1 |
| **Phase 4 — Capability Accumulation** | Накопление способностей | `SkillRegistry`, mining успешных/провальных tasks, review pipeline → approve/reject → rollout |
| **Phase 5 — Intelligence Expansion** | Контекст без потери управляемости | `RepoIndexer`, `ContextRetriever`, WebResearch/WebMonitor, `DocumentIngestor`, autonomy boundaries |

**vNext direction** продолжает эти фазы, а не заменяет их:
- Kernel Hardening
- Workspace OS
- Governance Core
- Capability Engine
- Intelligence Fabric
- Experience & Modalities
- Governed Autonomy

---

## 12. Autonomy Boundaries & Draft Levels

**На v1 / v5.1 не отдаём без review:** runtime self-modification, automatic code patch rollout, unrestricted external actions, критичные prod-изменения, uncontrolled agent spawning.

Автономия растёт после observability и governance, а не раньше.

| Level | Название | Описание |
|-------|----------|----------|
| `L0` | Manual | Pith предлагает, человек исполняет |
| `L1` | Assisted | Безопасные действия без внешних side-effects (черновики, отчёты, локальные артефакты) |
| `L2` | Semi-auto / Safe Autopatch | Ограниченные внешние действия по approved policy (draft PR, задачи, обновление БД) |
| `L3` | Auto / Canary | Изменения внешних систем только через canary-rollout и жёсткий governance |

Текущий допустимый рабочий режим: **L0–L1**.

---

## 13. Mental Model

- `Chat` = interaction surface
- `Pith` = continuity substrate + orchestration runtime
- `Skills / tools` = execution capabilities
- `Governance` = safety, экономика, воспроизводимость
- `Workspace` = unit of reality

> Pith — не бот с памятью.  
> Pith — это **workspace-native orchestration runtime для continuity-driven работы**.