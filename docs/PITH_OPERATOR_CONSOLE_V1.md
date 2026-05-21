Ниже полный черновик docs/PITH_OPERATOR_CONSOLE_V1.md, который можно вставить как отдельный файл. Он описывает минимальный функциональный контракт операторской консоли (CLI/Web/Telegram‑оверлей) под твой текущий Governance/Trace/Eval.

Pith Operator Console v1 (Spec)
Status: DRAFT / V1
File role: минимальный функциональный контракт операторской консоли для Pith Runtime v5.4
Scope: approvals, governance‑events, traces, eval, billing hooks, kill‑switch — в рамках Tier 0–1 (L0–L1) и Support/Ops Desk wedge

1. Purpose
Operator Console v1 — это операторский интерфейс (CLI/Web/Telegram‑оверлей) для управления и наблюдения за Pith Runtime:

просмотр и управление approval‑очередью;

просмотр и разбор governance‑событий, traces и eval;

ручное вмешательство в критичные workflows (approve/reject/escalate/rollback);

наблюдение за cost/usage/billing‑событиями.

Цель: дать людям управляемый HITL‑слой поверх runtime и governance, без которого безопасная автономия невозможна.

2. Surfaces & Modes
Operator Console v1 может существовать в нескольких поверхностях:

CLI‑инструмент (pithctl или аналог) — базовый и обязательный;

Telegram‑оверлей (inline‑approvals / ссылки на trace);

Web‑консоль v0.1 (минимальные экраны, необязательно в Phase 1).

Этот документ описывает функции, а не конкретный UI; любой surface должен реализовать минимальное подмножество.

3. Core Entities
Консоль работает с несколькими типами сущностей:

Task — единица работы (см. Kernel / TaskService).

Trace — запись в task_traces + связанные episodes/eval.

GovernanceDecision — событие из governance_events.

Approval — операторское решение по gated действиям.

BillableEvent — бизнес‑событие для биллинга (лид, релиз, отчёт и т.п.).

Все операции в консоли строятся на этих сущностях.

4. Approval Queue
4.1. Что показывать
Approval‑очередь отображает ожидающие решения gated действия:

approval_id / decision_id

created_at

trace_id, task_id, workspace_id

action_class (send, publish, mutate_system, spend_money, change_access, delete, export_sensitive)

summary действия (краткое описание, включая target/recipient/объект)

autonomy_tier, runtime_mode

requested_by (agent/user/department)

policy_id, policy_version (если есть)

4.2. Действия оператора
Для каждого элемента очереди:

Approve — подтвердить действие:

обновить governance_events (approval_state=approved);

разрешить выполнение tool/операции;

логировать оператора (approver_id) и timestamp.

Reject — отклонить действие:

обновить governance_events (approval_state=rejected);

блокировать действие;

опционально указать причину (комментарий).

Escalate — отправить в повышенный канал (security/owner):

обновить governance_events (outcome=escalate);

пометить approval как escalated;

отправить уведомление в соответствующий канал.

Timeout / Auto‑expire (опционально):

при истечении срока без решения → approval_state=expired;

действие не выполняется.

5. Trace & Eval Viewer
5.1. Trace viewer (per task)
Функциональность:

Найти trace по:

trace_id, task_id, workspace_id, user/времени.

Показать:

базовые поля task_traces (status, runtime_mode, task_type, duration_ms, failure_class, error_code, cost_estimate_usd, runtime_config_ver);

связанные governance‑events (GovernanceDecision v1);

связанные eval‑записи (EvaluationRecord v1);

основных участников (агенты, департаменты, tools).

UI‑уровень: табличный список задач + детальный просмотр одного trace.

5.2. Eval viewer
Функциональность:

Показать EvaluationRecord v1 для выбранного trace/task:

task_success, human_override, quality_score, eval_source, eval_version,

failure_class, workflow_type, runtime_mode,

trace_id, workspace_id, task_id, cost_per_workflow.

Фильтры:

по task_success (success/partial/failure),

по failure_class,

по workflow_type (особенно Support/Ops Desk).

Цель: поддержка ручного анализа качества и failure mining.

6. Governance Events View
6.1. Список governance‑событий
Функциональность:

Показать список governance‑events (из таблицы governance_events) с фильтрами:

по outcome (allow, allow_with_constraints, require_approval, deny, escalate);

по action_class;

по policy_id;

по workspace_id, autonomy_tier.

Основные поля для вывода:

created_at

trace_id, task_id, workspace_id

subject_type, subject_id

action_class, outcome, approval_state

policy_id, policy_version

reason (если есть)

6.2. Drill‑down
Для каждого события можно:

перейти к связанному trace (см. Trace viewer);

увидеть применённые constraints при allow_with_constraints;

увидеть approver при require_approval.

7. Billing / Cost Signals (v1)
Operator Console должна иметь хотя бы базовый cost‑экран:

агрегированные метрики:

суммарный cost_usd за период (день/неделя/месяц),

cost per workspace,

top workflows по стоимости (trace‑linked);

детали:

возможность перейти от cost‑метрики к конкретным trace/tasks,

отображение потенциальных billable_event записей (как только они будут введены).

Цель на v1: видимость затрат и подготовка к будущему биллингу, а не полный billing‑движок.

8. Kill‑Switch / Runtime Controls
Минимальный набор управляющих действий:

Runtime kill‑switch (per interface или глобально):

временно блокировать новые задачи;

остановить выполнение high‑risk tools;

прописывать статус в RuntimeConfig и отражать в Heartbeat.

Mode toggles:

включение/выключение DIAGNOSTICS режима (например, для более подробных traces);

временное снижение автономии (например, форсировать Tier 0 только).

Все такие действия должны:

логироваться в TraceStore / governance_events;

быть видимыми в Operator Console (история конфигурационных решений).

9. CLI / Telegram минимальный контракт
9.1. CLI (примерный интерфейс)
Команды‑кандидаты:

pithctl approvals list

pithctl approvals approve <approval_id>

pithctl approvals reject <approval_id> --reason "..."

pithctl trace show <trace_id>

pithctl eval show <trace_id>

pithctl governance events --action_class send --outcome deny

pithctl runtime kill-switch on/off

pithctl runtime mode set --tier 0 (пример, если надо временно отпилить Tier 1)

9.2. Telegram
Минимальный функционал:

inline‑кнопки/команды для:

approve/reject/escalate по конкретному запросу;

ссылки на trace/eval (например, короткий summary + ссылка в dashboard/CLI‑hint).

Telegram‑слой не заменяет полноценную консоль, но должен позволять быстро подтверждать/отклонять наиболее частые approvals.

10. Phase 1 Exit Criteria для Operator Console
Operator Console v1 считается минимально реализованной, если:

Есть хотя бы CLI‑инструмент, который умеет:

смотреть approval‑очередь и принимать решения;

открывать trace/task/eval по trace_id/task_id;

смотреть governance‑events с базовыми фильтрами.

Telegram‑guards при срабатывании дают оператору минимум информации и/или ссылку на trace, а не просто “ошибка”.

Есть базовый экран/команда с cost‑метриками (даже в текстовом виде).

Все действия оператора (approve/reject/escalate/kill‑switch) логируются через GovernanceDecision/TraceStore и могут быть восстановлены.