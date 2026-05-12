# Pith Glossary

Этот глоссарий фиксирует ключевые термины Pith Runtime в одном месте.  
Цель — чтобы код, доки и обсуждения использовали одни и те же слова.

---

## Pith Runtime (Pith v5+)

**Pith Runtime** — это **self‑improving continuity engine / workspace‑native orchestration runtime** для long‑running работы.[file:1219]

Не:

- чат‑бот,  
- AGI‑обещание,  
- “просто память”,  
- zoo агентов.

А:

- runtime‑слой, который связывает задачи, контекст, память, навыки, модели и действия в управляемый цикл;  
- слой над моделями, памятью и инструментами (их можно менять без ломки continuity).

---

## Cognition Graph

**Cognition Graph** — явное описание когнитивного контура Pith Runtime:

- узлы: шаги `Task Interpretation → Planning → Tool/Model Calls → Evaluation → Memory Update`;  
- рёбра: переходы, зависящие от типа задачи, политики и результатов шагов;  
- топологии: simple, reflective, tool‑use, multistep, delegation.[file:1219]

Graph используется Planner/Router для выбора маршрута выполнения.

---

## Runtime Planner

**Runtime Planner** — компонент, который:

- интерпретирует входящий запрос как `Task` + `task_type` + `risk_level`;  
- выбирает топологию в Cognition Graph (simple / reflective / tool‑use / multistep / delegation);  
- решает, идти ли через Orchestrator (мультиагентный/многошаговый сценарий) или через direct LLM;  
- выдаёт план шагов для Execution Engine.[file:1219]

Planner — мозг “как” делать работу, Router — “на какой модели и с какими инструментами”.

---

## Evaluator / Coherence Φ

**Evaluator** — модуль оценки качества и согласованности:

- `score.final` — агрегированная оценка качества ответа;  
- `persona_coherence` — насколько интерфейсная персона (например, Viktor) ведёт себя в рамках заданной личности;  
- `context_use` — насколько хорошо был использован доступный контекст/память;  
- `hallucination_suspicion` — эвристика на возможные галлюцинации.[file:1219]

**Coherence Φ** — сводный индикатор “насколько поведение Pith Runtime в заданном периоде похоже на самого себя” (coherence по persona, стилю, структуре ответов и отношению к риску).

Evaluator и Coherence Φ — основа для:

- self‑evolution (evaluator → miner → patch planner);  
- governance (block/rollback при падении метрик).[file:1238]

---

## Workspace / Task / Artifact / Skill / Policy / Trace

- **Workspace** — контейнер рабочей реальности: проект, кодовая база, клиент, продукт. Все Tasks и Artifacts привязаны к Workspace.[file:1219]  
- **Task** — единица работы: вход (запрос, параметры), контекст, состояние и результат.  
- **Artifact** — любой результат работы: файл, отчёт, summary, patch, decision.  
- **Skill** — оформленная reusable процедура (план/шаблон действий), которую Runtime может вызывать и версионировать.  
- **Policy** — правило/ограничение поведения (budget, risk, autonomy, доступ к инструментам).  
- **Trace** — наблюдаемая история reasoning/execution: какие шаги были проделаны, какие модели/инструменты вызваны, какие решения приняты.[file:1219]

---

## Orchestrator vs Agent

- **Orchestrator** — часть Core Runtime, bridge‑слой, который:
  - распараллеливает работу нескольких модульных агентов (`tera`, `hex`, `coda` и т.п.);  
  - агрегирует их результаты (`synthesize`);  
  - управляет таймаутами, fallback’ами и ошибками.[file:1219]

- **Agent** (в терминологии Pith) — не “магическая сущность”, а:
  - модуль с чётким контрактом: `process`/`process_async` + типизированный ввод/вывод;  
  - работающий в своём контексте (memory namespace, доступные tools, допустимые модели);  
  - управляемый Orchestrator’ом и Policy Engine.

Главное: Orchestrator — часть ядра, агенты — расширяемые модули поверх него.

---

## Continuity / Memory / Autonomy / Governance (в терминах Pith)

- **Continuity** — способность Pith вести работу через время, интерфейсы и задачи: помнить решения, причины, артефакты и состояние workspace.[file:1219]  
- **Memory** — слой, который хранит:
  - short‑term контекст сессии;  
  - episodic историю;  
  - semantic знания и документы;  
  - профиль пользователя/команды.[file:1219]  
- **Autonomy** — степень, в которой Pith имеет право:
  - сам выбирать модели/инструменты;  
  - сам применять изменения (патчи, PR, обновления БД) без подтверждения человека.  
  Уровни автономии описаны в `MASTER_PLAN.md` / `EVOLUTION.md` (L0–L3).[file:1238]  
- **Governance** — слой, который делает автономию управляемой:
  - `RuntimeConfig`, политики, лимиты;  
  - Traces и PolicyDecision;  
  - PatchGate, RolloutManager, kill switches;  
  - метрики и алерты.[file:1238]

В сумме: **continuity + memory + orchestrated execution + governed autonomy** — это и есть Pith Runtime.