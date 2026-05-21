Pith Runtime
Pith Runtime — self‑improving continuity runtime / workspace‑native orchestration runtime для long‑running когнитивных и операционных задач внутри workspace’ов.

Не:

чат‑бот,

AGI‑обещание,

“просто память”,

зоопарк агентов.

А:

runtime‑слой, который связывает задачи, контекст, память, навыки, модели, департаменты/desk’и и действия в управляемый цикл;

слой над моделями, памятью и инструментами: их можно менять без ломки continuity, governance и трассировки.

Tenant / Workspace / User
Tenant — верхнеуровневая граница клиента/организации. Обеспечивает изоляцию данных, политик, секретов и биллинга между организациями.

Workspace — контейнер рабочей реальности внутри tenant’а: проект, кодовая база, клиент, продукт, департамент.
Все Task, Workflow, Artifact, MemoryRecord, Trace, EvaluationRecord и BillableEvent привязаны к Workspace.

User — конкретный человек или интеграция, от имени которого ведётся работа (чаты, API‑ключи, сервис‑аккаунты).

Task / Workflow / Artifact / Skill / Policy / Trace / RuntimeConfig
Task — единица работы: вход (запрос, параметры), контекст, состояние, результат и оценка. Может быть одиночной задачей или частью workflow.

Workflow — цепочка связанных шагов/департаментов/agents для достижения бизнес‑цели. Имеет собственный идентификатор, состояние и связанный Task/Trace.

Artifact — результат работы: файл, отчёт, summary, патч, launch kit, решение. Всегда привязан к Task/Workflow и Workspace, имеет lineage (derived_from, approved_by, runtime_version).

Skill — оформленная reusable процедура (план/шаблон действий, код/конфиг), которую runtime может вызывать и версионировать. Живёт как явный артефакт, а не как скрытая “память модели”.

Policy — правило/ограничение поведения (budget, risk, autonomy, доступ к инструментам, data‑scoping). Применяется Policy Engine’ом к workflow/agent/action.

Trace — наблюдаемая история reasoning/execution: какие шаги были проделаны, какие модели/инструменты вызваны, какие решения и approvals приняты, какие расходы и ошибки произошли. Хранится в TraceStore (task_traces, episodes, events).

RuntimeConfig — версия настроек моделей, prompts, политик и лимитов для задач. Каждая задача исполняется под конкретной версией RuntimeConfig, которая фиксируется в трейсах и не меняется “по ходу”.

Runtime Planner / Cognition Graph / Orchestrator
Runtime Planner — компонент, который:

интерпретирует входящий запрос как Task + task_type + runtime_mode + приблизительный risk_level;

выбирает топологию выполнения (direct vs orchestrated, simple / tool‑use / multistep / delegation);

даёт подсказки Router’у по lane/модели;

помечает execution_path: "direct" | "orchestrated" для observability/eval. 

Cognition Graph — явное описание когнитивного контура Pith Runtime:

узлы: Task Interpretation → Planning → Tool/Model Calls → Evaluation → Memory Update;

рёбра: переходы в зависимости от task_type, режима, политики и результатов шагов;

топологии: simple, reflective, tool‑use, multistep, delegation.
Planner использует graph как карту возможных путей.

Orchestrator — часть Core Runtime, которая:

может распараллеливать работу нескольких модульных агентов/департаментов;

агрегирует результаты;

управляет таймаутами, fallback’ами и ошибками по policy.

Главное: Planner решает “как и по какому пути”, Orchestrator исполняет этот путь, Router/Model Plane отвечает за “на какой модели и с какими инструментами”.

Agent / Department / Desk / Agent Company
Agent (в Pith) — модуль с чётким контрактом (process / process_async + типизированный ввод/вывод), работающий:

в своём memory namespace,

с ограниченным набором tools/models,

под своим risk_tier и autonomy‑уровнем.
Управляется Orchestrator’ом и Policy Engine.

Department — логический отдел цифровой компании (Support/Ops, Back Office, Revenue, Research, Delivery), состоящий из связанных агентов/ролей.

Desk — конкретный productized пакет департамента (например, Support/Ops Desk как v5.4 wedge для B2B команд).

Pith Agent Company — прикладной слой поверх Runtime: набор департаментов/desk’ов и workflows, которые реализуют бизнес‑функции (support, ops, back office, revenue) и монетизируются через billable events.

Continuity / Memory / Observability / Evaluation / Governance
Continuity — способность Pith вести работу через время, интерфейсы и задачи: помнить решения, причины, артефакты и состояние workspace/tenant. Опирается на State Layer (Tasks, Workflows, Artifacts, MemoryRecords, Traces).

Memory — слой, который хранит:

short‑term контекст сессии,

episodic историю (episodes),

semantic знания и документы,

профиль пользователя/команды.
Управляется Memory Manager’ом и подчиняется политикам workspace/tenant; retrieval ограничен relevance‑floor и token‑budget.

Observability — возможность реконструировать, как система приняла решения и что сделала: TraceStore (task_traces), episodes, metrics, failure taxonomy, cost.

Evaluation — измерение качества, надёжности, стоимости и полезности workflows через EvaluationRecord v1 (task_success, human_override, quality_score, cost_per_workflow, policy_violation, failure_class и др.).

Governance — слой, который делает автономию управляемой:

RuntimeConfig, политики и лимиты,

PolicyDecision, approvals/HITL,

PatchGate, RolloutManager, kill switches,

метрики, алерты, canary/rollback.

В сумме: continuity + memory + orchestrated execution + observability + evaluation + governed autonomy = Pith Runtime как Kernel.

Autonomy Levels (L0–L4)
Autonomy — степень, в которой Pith имеет право:

сам выбирать модели/инструменты/маршруты внутри заданных политик;

сам применять изменения (патчи, PR, обновления БД, внешние действия) без подтверждения человека.

Уровни:

L0 — Manual / Advisory: думает, рекомендует, делает черновики; внешние действия делает человек.

L1 — Assisted: может выполнять низкорисковые внутренние действия; человек подтверждает важное и всё внешнее.

L2 — Supervised / Semi‑auto: может выполнять ограниченные внешние действия по approved policy и с review/эскалацией.

L3 — Auto / Canary: выполняет определённые прод‑действия автономно через canary‑роллауты и строгие метрики.

L4 — High Autonomy: только для узких, полностью проверенных workflows под жёсткими ограничениями.

Текущий допустимый режим v5.x: L0–L1 + точечный L2 для узких, хорошо наблюдаемых сценариев; L3–L4 — будущее, требующее сильного governance/eval.

Billable Event / Cost
BillableEvent — бизнес‑событие, по которому считается стоимость и монетизация:
support_case_resolved, workflow_completed, qualified_lead_created, campaign_pack_generated, research_brief_delivered, human_review_performed и др.

Cost — совокупные расходы по моделям/инструментам/инфре для задачи/воркфлоу. В Pith cost атрибутируется по tenant, workspace, workflow, department, tool/model и связывается с BillableEvents и EvaluationRecord.

Pith & AGI / Self‑Evolution Runtime
AGI (в контексте Pith) — не “человечность”, а набор свойств: трансфер между доменами, самообучение без дообучения весов, причинное понимание и целеполагание/адаптивное планирование. Pith сам по себе не AGI, а runtime‑слой поверх LLM, который может эволюционировать и накапливать能力.

PITH_SELF_EVOLUTION_RUNTIME_V1 — архитектурный контракт того, как Pith улучшает собственный runtime:

собирает сигналы из Observability и Evaluation,

через evaluator → failure_miner → patch_planner формирует патчи (skills, prompts, policies, routing),

пропускает их через PatchGate и RolloutManager,

измеряет эффект и откатывает деградирующие изменения.

Self‑evolution:

не меняет ядро runtime без участия человека;

не обучает базовые модели;

не выходит за рамки autonomy.yaml и governance‑политик;

служит для того, чтобы runtime становился умнее, дешевле и безопаснее, а не неконтролируемо автономным.

