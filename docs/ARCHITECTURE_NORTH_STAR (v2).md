# Pith Architecture North Star v2

> **Purpose:** Single source of truth for Pith's architectural vision, product boundaries, and 6-month roadmap.  
> **Status:** `ACTIVE` — supersedes all previous North Star drafts.  
> **Last updated:** 2026-04-28  
> **Owner:** Pith Lab (Internal)

---

## 1. Purpose & Core Identity

Pith — это **self‑improving continuity engine / workspace‑native orchestration runtime** для длинных когнитивных и инженерных задач.

Его задача — не отвечать на единичные промпты, а вести работу во времени: задачи, контекст, память, артефакты, навыки и решения внутри одного управляемого контура.

Pith не привязан к одной модели или вендору. Это **слой над моделями, памятью и инструментами**; их можно менять, не ломая continuity и архитектуру.

---

## 2. 6‑Month North Star Goal

К концу текущего квартала/полугода Pith v5 должен стать устойчивым **agent runtime**, на котором:

1. Можно запускать несколько типов агентов (кодер, исследователь, оператор задач) через один Core Runtime и общую память.
2. Любая работа живёт в `Workspace / Task / Artifact / MemoryRecord`, а не «где‑то в чате».
3. Система умеет читать внешние источники (репозитории, документы, веб), превращать их в навыки и знания, а не просто в разовые ответы.
4. Эволюция (изменения моделей, промптов, навыков, политик) идёт через **governance**: версии, метрики, canary, rollback.
5. Есть минимум один специализированный агент, которого можно доверенно отправить на реальные задачи (код/контент/ресёрч/операции) и ожидать воспроизводимый результат.

---

## 3. Core Promise

Pith делает сложную работу **continuous, accumulative и governable**.

| Принцип | Значение |
|---------|----------|
| **Continuous** | Работа не обнуляется между сессиями, интерфейсами и моделями. Контекст не нужно проговаривать заново. |
| **Accumulative** | Каждый запуск оставляет след: артефакт, память, навык, улучшенную политику или знание. |
| **Governable** | Поведение системы наблюдаемо и под контролем: трассировка, версии, политики, budget‑лимиты и понятные границы автономии. |

---

## 4. Product Test & One‑Liner

**Product Test:**  
Любая часть системы проходит проверку: *Усиливает ли она continuity, reusable execution, workspace state, artifact flow или control over long‑running work?* Если нет — это полезный модуль, но не ядро.

**Guiding One‑Liner:**  
> `Chat решает промпт. Pith решает continuity.`

---

## 5. Anti‑Goals

Pith **не должен** становиться:

- ❌ Ещё одним LLM‑чатом (даже «с хорошей памятью»).
- ❌ Telegram‑ботом как продуктом (Telegram — только один из интерфейсов).
- ❌ «Зоопарком» агентов, где ценность — количество ролей, а не их качество и воспроизводимость.
- ❌ Системой неконтролируемой автоэволюции (изменения без observability и rollback).
- ❌ Декоративной AI‑надстройкой к Notion/Jira/Slack.

Pith — это ядро, вокруг которого живут боты, UI, API и интеграции, а не наоборот.

---

## 6. System Layers

| Слой | Назначение | Ключевые компоненты |
|------|-----------|-------------------|
| **1. Core Runtime** | Оркестрация, планирование, маршрутизация, память, оценка | Task Orchestrator, Cognition Graph, Runtime Planner, Router, Memory Manager, Evaluator, Policy Engine |
| **2. State Layer** | Реальность и continuity. Канонические сущности | Workspace, Task, Artifact, MemoryRecord, Trace, Skill, RuntimeVersion, PolicyDecision, User, Tenant |
| **3. Capability Layer** | Расширяемые операции | Web research, repo reading, coding/refactor, planning, tool/action integrations |
| **4. Interface Layer** | Точки входа (не сущность Pith) | Telegram, REST API / FastAPI, Dashboard, CLI, IDE‑плагины |
| **5. Governance Layer** | Контроль, безопасность, экономика | Observability, Evaluation metrics, Rollout/Canary/Revert, Autonomy gates, Budget/Risk policies |

---

## 7. Bounded Contexts

| Контекст | Фокус |
|----------|-------|
| **Execution** | Запуск задачи, orchestration, routing, вызовы tools/skills, lifecycle |
| **Workspace** | Проекты, tenant/user границы, файлы, репозитории, artifacts, task history |
| **Memory** | Эпизодическая память, semantic recall, continuity пользователя и workspace |
| **Capability** | Skills, tools, repo/web intelligence, процедуры |
| **Governance** | Evaluator, policies, review/approval, rollout/rollback |
| **Delivery** | Telegram‑бот, API adapters, dashboard UI, нотификации, entrypoints |

---

## 8. Canonical Entities

| Entity | Role |
|--------|------|
| `Workspace` | Контейнер долгоживущей рабочей реальности |
| `Task` | Единица исполнения и прогресса |
| `Artifact` | Результат: файл, summary, patch, отчёт, решение |
| `MemoryRecord` | Сохраняемый контекст и continuity‑substrate |
| `Trace` | Наблюдаемая история reasoning / execution path |
| `Skill` | Версионируемая reusable процедура / способность |
| `Policy` | Ограничения и правила поведения системы |
| `Evaluation` | Оценка качества, риска, успеха, регресса |
| `RuntimeVersion` | Версия поведения / конфигурации runtime |
| `User` | Человек или сервис‑клиент |
| `Tenant` | Организация / пространство, объединяющее workspaces/users |

---

## 9. Operating Loop

1. Interface получает запрос.
2. Workspace Resolver определяет контекст (workspace, user, tenant).
3. Task Service создаёт `TaskRecord`.
4. Context Assembler собирает `memory + artifacts + repo/web/file context`.
5. Planner / Router выбирает topology, model lane, tools и skills.
6. Execution Engine исполняет задачу через model plane и tool/action plane.
7. Evaluator оценивает результат (качество, риск, стоимость, регресс).
8. Artifact Service сохраняет output в `ArtifactStore`.
9. Memory Manager записывает continuity‑информацию в `MemoryRecord`.
10. Trace + Policy Engine фиксируют decision path и governance signals.

**Принципы:** цикл логически event‑driven, каждый шаг оставляет явный след, шаги по возможности идемпотентны.

---

## 10. Core vs Non‑Core

| ✅ Core для Pith | ⚠️ Важно, но не identity |
|------------------|--------------------------|
| Workspaces, Tasks, Artifacts | Telegram UX, конкретные LLM‑вендоры |
| Memory, Planner / Router | Web search / repo indexing |
| Evaluator / Policies | Persona‑слои и стилистика |
| Observability, Traces | «Фансишные» агенты, UI‑паттерны дашборда |

---

## 11. Phased Build (6‑Month Horizon)

| Фаза | Цель | Ключевые deliverables |
|------|------|----------------------|
| **Phase 1 — Core Stabilization** | Управляемый runtime без хардкода | `model_registry`, secrets hygiene, structured traces, canonical task lifecycle, чёткие границы router/planner/memory/evaluator |
| **Phase 2 — Workspace Substrate** | Работа живёт в workspace | `WorkspaceService`, `TaskService`, `ArtifactStore`, FastAPI `/v1/workspaces`, `/v1/tasks` |
| **Phase 3 — Governance Baseline** | Наблюдаемость и контроль | Evaluation schema, `runtime_versions`/`patch_candidates`, rollback hooks, budget/risk policies, Dashboard v1 |
| **Phase 4 — Capability Accumulation** | Накопление способностей | `SkillRegistry`, mining успешных/провальных тасков, review pipeline → approve/reject → rollout |
| **Phase 5 — Intelligence Expansion** | Контекст без потери управляемости | `RepoIndexer`, `ContextRetriever`, WebResearch/WebMonitor, `DocumentIngestor`, autonomy boundaries |

---

## 12. Autonomy Boundaries & Draft Levels

**На v1 не отдаём без review:** runtime self‑modification, automatic code patch rollout, unrestricted external actions, критичные prod‑изменения, uncontrolled agent spawning. Автономия растёт после observability и governance, а не раньше.

| Level | Название | Описание |
|-------|----------|----------|
| `L0` | Manual | Pith предлагает, человек исполняет |
| `L1` | Assisted | Безопасные действия без внешних side‑effects (черновики, отчёты, локальные артефакты) |
| `L2` | Semi‑auto / Safe Autopatch | Ограниченные внешние действия по approved policy (draft PR, задачи, обновление БД) |
| `L3` | Auto / Canary | Изменения прод/внешних систем только через canary‑rollout и жёсткий governance |

---

## 13. Mental Model

- `Chat` = interaction surface  
- `Pith` = continuity substrate + orchestration runtime  
- `Skills / tools` = execution capabilities  
- `Governance` = safety, экономика, воспроизводимость  
- `Workspace` = unit of reality  

> Pith — не бот с памятью.  
> Pith — это **workspace‑native orchestration runtime для continuity‑driven работы**.