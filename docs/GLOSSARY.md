# Pith Glossary

Этот глоссарий фиксирует ключевые термины Pith Runtime в одном месте.  
Цель — чтобы код, доки и обсуждения использовали одни и те же слова.

---

## Pith Runtime (Pith v5+)

**Pith Runtime** — это **self‑improving continuity runtime / workspace‑native orchestration runtime** и ядро Agent Company OS для long‑running работы.

Не:

- чат‑бот,  
- AGI‑обещание,  
- “просто память”,  
- zoo агентов.

А:

- runtime‑слой, который связывает задачи, контекст, память, навыки, модели, департаменты и действия в управляемый цикл;  
- слой над моделями, памятью и инструментами (их можно менять без ломки continuity и governance).

---

## Tenant / Workspace / User

- **Tenant** — верхнеуровневая граница клиента/организации.  
  Отвечает за изоляцию данных, политик и биллинга между организациями.

- **Workspace** — контейнер рабочей реальности внутри tenant’а: проект, кодовая база, клиент, продукт.  
  Все `Task`, `Workflow`, `Artifact`, `MemoryRecord`, `Trace` и `BillableEvent` привязаны к Workspace.

- **User** — конкретный человек или интеграция, от имени которого ведётся работа (чаты, API‑ключи, сервис‑аккаунты).

---

## Task / Workflow / Artifact / Skill / Policy / Trace / RuntimeConfig

- **Task** — единица работы: вход (запрос, параметры), контекст, состояние и результат.  
  Может быть одиночной задачей или частью workflow.

- **Workflow** — цепочка связанных шагов/департаментов/агентов для достижения бизнес‑цели.  
  Имеет собственный идентификатор, состояние и связанный `Task`/`Trace`.

- **Artifact** — результат работы: файл, отчёт, summary, патч, launch kit, решение.  
  Всегда привязан к `Task`/`Workflow` и `Workspace`.

- **Skill** — оформленная reusable процедура (план/шаблон действий), которую Runtime может вызывать и версионировать.  
  Живёт как явный артефакт (код/конфиг/док), а не как “память модели”.

- **Policy** — правило/ограничение поведения (budget, risk, autonomy, доступ к инструментам, data‑scoping).  
  Применяется Policy Engine’ом к workflow/agent/action.

- **Trace** — наблюдаемая история reasoning/execution: какие шаги были проделаны, какие модели/инструменты вызваны, какие решения приняты, какие расходы и governance‑события произошли.

- **RuntimeConfig** — версия настроек моделей, prompts, политик и лимитов для задач.  
  Каждая задача исполняется под конкретной версией `RuntimeConfig`, которая не меняется “по ходу”.

---

## Pith Runtime Planner / Cognition Graph / Orchestrator

- **Runtime Planner** — компонент, который:
  - интерпретирует входящий запрос как `Task` + `task_type` + `risk_level`;  
  - выбирает топологию выполнения (simple / reflective / tool‑use / multistep / delegation);  
  - решает, идти ли через Orchestrator (мультиагентный/многошаговый сценарий) или через direct LLM;  
  - выдаёт план шагов для Execution Engine.

- **Cognition Graph** — явное описание когнитивного контура Pith Runtime:
  - узлы: шаги `Task Interpretation → Planning → Tool/Model Calls → Evaluation → Memory Update`;  
  - рёбра: переходы, зависящие от типа задачи, политики и результатов шагов;  
  - топологии: simple, reflective, tool‑use, multistep, delegation.  
  Planner использует graph для выбора маршрута выполнения.

- **Orchestrator** — часть Core Runtime, bridge‑слой, который:
  - распараллеливает работу нескольких модульных агентов/департаментов;  
  - агрегирует их результаты;  
  - управляет таймаутами, fallback’ами и ошибками.

Главное: Orchestrator — часть ядра, Planner решает “как”, Router/Model Plane — “на какой модели и с какими инструментами”.

---

## Agent / Department / Agent Company

- **Agent (в терминах Pith)** — не “магическая сущность”, а:
  - модуль с чётким контрактом (`process`/`process_async` + типизированный ввод/вывод);  
  - работающий в своём контексте (memory namespace, доступные tools, допустимые модели, autonomy tier);  
  - управляемый Orchestrator’ом и Policy Engine.

- **Department** — логический отдел цифровой компании (Sales, Marketing, Research, Delivery, Support/Ops), состоящий из связанных агентов/ролей.  
  Пример: Sales Squad = Lead Finder, Lead Qualifier, Outreach, Follow‑up, CRM Agent.

- **Pith Agent Company** — прикладной слой поверх Runtime: набор департаментов и workflows, которые реализуют бизнес‑функции (лиды, кампании, ресёрчи, релизы, саппорт) и монетизируются через billable events.

---

## Continuity / Memory / Observability / Evaluation / Governance

- **Continuity** — способность Pith вести работу через время, интерфейсы и задачи: помнить решения, причины, артефакты и состояние workspace/tenant.  
  Continuity опирается на State Layer (Tasks, Workflows, Artifacts, MemoryRecords, Traces).

- **Memory** — слой, который хранит:
  - short‑term контекст сессии;  
  - episodic историю;  
  - semantic знания и документы;  
  - профиль пользователя/команды.  
  Memory управляется Memory Manager’ом и подчиняется политикам workspace/tenant.

- **Observability** — возможность реконструировать, как система приняла решения и что сделала: traces, events, metrics, cost, failure taxonomy.  
  Это основа для дебага, доверия, биллинга и eval.

- **Evaluation** — измерение качества, надёжности, стоимости и полезности workflows (task success, human override, quality score, cost per workflow, policy violations).  
  Используется для self‑evolution и governance.

- **Governance** — слой, который делает автономию управляемой:
  - `RuntimeConfig`, политики, лимиты;  
  - `PolicyDecision`, approvals;  
  - PatchGate, RolloutManager, kill switches;  
  - метрики и алерты.

В сумме: **continuity + memory + orchestrated execution + observability + evaluation + governed autonomy** — это и есть Pith Runtime как Kernel.

---

## Autonomy Levels (L0–L4)

**Autonomy** — степень, в которой Pith имеет право:

- сам выбирать модели/инструменты/маршруты;  
- сам применять изменения (патчи, PR, обновления БД, внешние действия) без подтверждения человека.

Уровни:

- **L0 — Manual / Advisory**: думает, рекомендует, черновики; внешние действия делает человек.  
- **L1 — Assisted**: готовит и может выполнять низкорисковые внутренние действия; человек подтверждает важное.  
- **L2 — Supervised / Semi‑auto**: может выполнять ограниченные внешние действия под политиками и с review/эскалацией.  
- **L3 — Auto / Canary**: выполняет определённые прод‑действия автономно через canary‑роллауты и строгие метрики.  
- **L4 — High Autonomy**: только для узких, полностью проверенных workflows, под жёсткими ограничениями.

В Pith v1.1 основная работа — на L0–L1 с точечным L2 для узких сценариев; L3–L4 — будущее и требуют сильного governance/eval.

---

## Billable Event / Cost

- **BillableEvent** — бизнес‑событие, по которому считается стоимость и монетизация:  
  примеры — `qualified_lead_created`, `campaign_pack_generated`, `research_brief_delivered`, `launch_kit_delivered`, `support_case_resolved`, `workflow_completed`, `human_review_performed`.

- **Cost** — совокупные расходы по моделям/инструментам/инфре для задачи/воркфлоу.  
  В Pith cost всегда атрибутируется по `tenant`, `workspace`, `workflow`, `department`, `tool/model` и связывается с BillableEvents.

---

## Pith Self‑Evolution Runtime

**PITH_SELF_EVOLUTION_RUNTIME_V1** — архитектурный контракт того, как Pith улучшает собственный runtime:

- собирает сигналы из Observability и Evaluation;  
- через evaluator → failure miner → patch planner предлагает патчи (skills, prompts, policies, routing);  
- пропускает их через PatchGate и RolloutManager;  
- измеряет эффект и откатывает деградирующие изменения.

Self‑evolution:

- не меняет ядро runtime без участия человека;  
- не обучает базовые модели;  
- не выходит за рамки `autonomy.yaml` и governance‑политик;  
- служит для того, чтобы OS становилась умнее и дешевле, а не неконтролируемо автономной.