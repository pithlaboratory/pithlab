Ниже полный черновик docs/PITH_SAFE_TOOL_RUNTIME_POLICY_V1.md, который можно вставить как отдельный файл. Он опирается только на уже зафиксированные тобой вещи (Governance v1, Action Classes, autonomy tiers, Telegram guards).

Pith Safe Tool Runtime Policy v1
Status: DRAFT / V1
File role: минимальный контракт безопасного использования tools/MCP в Pith Runtime v5.4
Scope: mapping tool→action_class, sandbox‑профили, deny‑by‑default, governance‑хуки, Tier 0–1 (L0–L1)

1. Purpose
Этот документ определяет Safe Tool Runtime Policy v1 для Pith:

как tools и MCP‑серверы мапятся на action classes из Governance v1;

какие sandbox‑профили и ограничения применяются к tool‑вызовам;

какие действия запрещены по умолчанию (deny‑by‑default);

как runtime должен логировать и проверять tool‑вызовы через Governance/TraceStore.

Цель: безопасное использование tools в рамках Tier 0–1 автономии без риска разрушения workspace/tenant и прод‑сред.

2. Action Classes (из Governance v1)
Safe Tool Runtime Policy опирается на stable action classes из docs/PITH_GOVERNANCE_V1.md:

read

retrieve

analyze

draft

recommend

write_internal

write_external

send

publish

mutate_system

spend_money

change_access

delete

export_sensitive

Один tool может реализовывать несколько классов (например, CRM‑клиент: read, write_internal, mutate_system).

3. Sandbox‑профили tool’ов
Каждый tool/MCP получает sandbox‑профиль. Профили задаются в tool registry / config.yaml и используются Governance/Tool Plane.

3.1. Базовые профили
read_only

Разрешены: read, retrieve, analyze.

Запрещены: write_internal, write_external, send, publish, mutate_system, spend_money, change_access, delete, export_sensitive.

Примеры: HTTP‑GET client, read‑only FS, read‑only CRM.

workspace_write

Разрешены: write_internal, draft, часть mutate_system в пределах workspace sandbox (локальные артефакты, черновики).

Запрещены: send, publish, spend_money, change_access, delete, export_sensitive без approval.

Примеры: редактор артефактов, локальный git‑patch в sandbox‑ветке.

networked

Разрешены: read/retrieve в внешние системы с ограничениями по доменам.

Требуют: явных domain allow‑lists; логирования всех запросов (url, action_class, workspace_id, trace_id).

Запрещены: произвольные POST/DELETE без явной политики.

privileged

Используется только для высокорисковых операций: mutate_system, spend_money, change_access, delete, export_sensitive.

Требует:

явной политики (policy_id) и action_class mapping;

require_approval или escalate по умолчанию;

dual control / HITL для особо критичных путей.

3.2. Привязка профиля к tool’у
Для каждого tool/MCP в registry указываются:

action_classes: список классов (из Governance v1),

sandbox_profile: read_only / workspace_write / networked / privileged,

allowed_workspaces / tenant_scope (если ограничено),

approval_policy: never | sometimes | always + условия (суммы, типы операций).

4. Deny‑by‑default правила
По умолчанию, для всех tools действуют следующие ограничения:

High‑impact classes (send, publish, mutate_system, spend_money, change_access, delete, export_sensitive) — deny‑by‑default при отсутствии явной политики.

Unknown tools (нет записи в registry или нет action_classes/sandbox профиля) — deny с failure_class=policy_failure и логированием в TraceStore.

Cross‑workspace/tenant операции без явного разрешения → deny.
Пример: tool пытается читать артефакты другого workspace без явного workspace_scope.

Outbound network без доменного allow‑list → deny.
Исключение: явно помеченные dev-only tools в dev‑режиме.

5. Integration with Governance v1
Safe Tool Runtime Policy реализует Governance v1 для tool‑уровня.

5.1. Governance outcomes для tools
Для каждого high‑impact вызова tool’а runtime должен получить governance‑решение:

allow

allow_with_constraints

require_approval

deny

escalate

И записать GovernanceDecision v1 (см. TraceStore/governance_events) с:

trace_id, task_id, workspace_id,

action_class, subject_type, subject_id (agent/user),

policy_id, policy_version,

outcome, approval_state,

constraints (если allow_with_constraints),

reason, autonomy_tier, runtime_mode, actor.

5.2. Поведение по действиям
allow → tool вызывается как есть.

allow_with_constraints → runtime обязан применить ограничения:

read‑only режим,

cost cap,

depth limit (например, глубина обхода репозитория),

ограниченный список методов/endpoints,

draft‑only вывод.

require_approval → вызов tool’а блокируется до human‑approval; создаётся approval‑task в Operator Console/Telegram, после чего:

при approve → tool вызывается;

при reject → действие не выполняется, trace помечается как rejected_after_review.

deny → tool не вызывается; trace и governance_events фиксируют отказ.

escalate → действие отправляется в усиленный канал (security/compliance/owner).

6. Autonomy Tiers и tools (Tier 0–1)
Для v5.4 активны только Tier 0–1 (L0–L1) из Governance v1.

6.1. Tier 0 — Advisory
Разрешены: read, retrieve, analyze, draft, recommend.

Запрещены: любые внешние side‑effects (send, publish, mutate_system, spend_money, change_access, delete, export_sensitive).

Tools с sandbox_profile=read_only допустимы без HITL, но с логированием.

6.2. Tier 1 — Assisted Execution
Разрешены:

write_internal в workspace‑sandbox (черновики, внутренние артефакты),

low‑risk mutate_system в sandbox (например, PR‑патч в dev‑ветку).

Требуют approval/strict policy:

любые send/publish (особенно клиентам),

spend_money выше порогов,

high‑impact mutate_system (деплой, миграции, конфиг‑смена),

change_access, delete, export_sensitive в prod‑контекстах.

7. Telegram governance guards (v5.4)
В Telegram‑интерфейсе уже включены 4 guard’а, которые реализуют часть Safe Tool Runtime Policy:

dangerous_delete — блокирует/эскалирует потенциально опасные delete‑операции;

internal_leak — предотвращает утечку внутренних артефактов наружу;

data_exfiltration — блокирует массовый export чувствительных данных;

workspace_isolation — следит за соблюдением границ workspace/tenant.

Требования:

каждый срабатывающий guard:

логируется в TraceStore с failure_class=policy_failure и error_code,

по возможности отражается в EvaluationRecord (policy_violation=true, failure_class=policy_failure),

не обходит Safe Tool Runtime Policy (guard — не замена governance, а дополнительный слой).

8. Logging & Observability
Любой tool‑вызов, особенно high‑impact, должен быть наблюдаемым:

Log‑строки (по уровню: info/warn/error) с:

tool_id, action_class, sandbox_profile, workspace_id, trace_id;

TraceStore:

при успехе/ошибке tool‑вызова — обновление task_traces (status, failure_class, error_code);

governance_events для gated действий (allow_with_constraints, require_approval, deny, escalate);

Evaluation:

для важных workflows — сигналы policy_violation, failure_class, task_success, human_override.

9. Minimum v1 Controls (recap)
Для Safe Tool Runtime Policy v1 достаточно реализовать:

Mapping tool→action_class + sandbox_profile в registry/config.

Deny‑by‑default для high‑impact action classes без явной политики.

Governance outcomes (allow, allow_with_constraints, require_approval, deny, escalate) для gated действий.

Логирование governance решений в governance_events (TraceStore v1.1).

Применение 4 Telegram guards (dangerous_delete, internal_leak, data_exfiltration, workspace_isolation).

Привязку к autonomy tiers (Tier 0–1) с запретом Tier 2+ в runtime по умолчанию.

Этого достаточно, чтобы Pith мог безопасно использовать tools в рамке Tier 0–1, не претендуя на “полный enterprise IAM”, но не создавая ложного ощущения отсутствия рисков.