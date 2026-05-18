# Pith Governance v1

> Governance architecture for Pith v5 as a runtime‑native, continuity‑aware, multi‑agent operating system.

---

## 1. Purpose

Pith Governance v1 defines how Pith controls **authority, approvals, autonomy levels, action boundaries, policy enforcement, and accountability** across workspaces, agents, and departments.[web:338][web:342]

Governance in Pith is not a legal appendix.  
It is an **execution control layer** that determines:

- what the system is allowed to do,
- what requires approval,
- what must be denied,
- what must be logged,
- what must remain reversible,
- what level of autonomy is appropriate for each workflow.

This document exists because agent capability without governance becomes unsafe, untrustworthy, and commercially fragile.[web:339][web:342]

Governance is implemented as a **runtime control plane** — policies are enforced before и во время выполнения, а не только на этапе дизайна.[web:341]

---

## 2. Why Governance Is First‑Class

Pith эволюционирует в сторону:

- workspace‑native runtime,
- Agent Company OS,
- governed execution environment,
- монетизируемой multi‑agent системы.

В этом контексте главный продакшен‑вопрос — не только  
**«Can the system do this?»**

Но и:  
**«Should the system be allowed to do this now, in this context, at this autonomy level, under these constraints?»**[web:342][web:348]

Поэтому governance — часть архитектуры рантайма, а не внешний compliance‑wrapper: Planner/Orchestrator/Tools работают под управлением Governance Plane, а не независимо от него.[web:341]

---

## 3. Governance Principles

### 3.1 Policy before dispatch

Любой workflow или действие должно оцениваться против политики **до** выполнения, а не только пост‑фактум.[web:342]

Policy‑checks должны перехватывать high‑impact действия (tool calls, sends, publishes, mutations, spend) на уровне Runtime/Orchestrator.

### 3.2 Explicit authority boundaries

Каждый workflow, department, tool и класс действий работает в явных рамках authority:

- actor (user/agent/department),
- autonomy tier,
- action class,
- context (tenant/workspace, data sensitivity).[web:343][web:349]

### 3.3 Risk‑tiered autonomy

Не все действия заслуживают одинаковой автономии.  
Чем выше риск/невозвратимость, тем жёстче контуры контроля и approval.[web:341][web:351]

### 3.4 Human oversight where needed

Human‑in‑the‑loop — это **дизайн‑выбор**, а не «провал автоматизации».[web:340][web:348]  
Он нужен для:

- безопасного масштабирования,
- соответствия бизнес‑рискам и регуляторным ожиданиям,
- постепенного повышения автономии.

### 3.5 Auditability by default

Каждое важное решение/действие должно быть реконструируемо из traces и governance‑записей с понятным decision lineage.[web:342][web:351]

### 3.6 Reversibility awareness

Для необратимых или high‑blast‑radius действий governance должен:

- повышать требования к политикам и approvals,
- использовать canary/rollback, где возможно,
- ограничивать максимальный autonomy tier.

### 3.7 Workspace and tenant safety

Governance обязан сохранять workspace/tenant‑границы и не позволять обходить их:

- ни агентам / департаментам,
- ни внешним интеграциям,
- ни operator tools.[web:343][web:349]

---

## 4. Identity & Subject Model

Этот слой отвечает на вопрос: **кто действует?**

### 4.1 Subject Types

В Pith есть пять типов субъектов:[web:343][web:349]

- **User** — человек, инициирующий работу (owner workspace, collaborator).
- **Operator** — человек с правами управлять конфигами, лимитами, департаментами.
- **Agent** — программный актор в Runtime (Tera, Plex, Hex, Coda, департаментные агенты).
- **Department** — логическое объединение агентов и workflows (Sales, Marketing, Research, Delivery, Support/Ops).
- **External Service** — Git, CI/CD, CRM, календарь, внешние API.

### 4.2 Identifiers

Для governance любая операция описывается в разрезе:

- `tenant_id`
- `workspace_id`
- `user_id`
- `agent_id`
- `department_id`
- `runtime_config_id`
- `policy_id`

Runtime Context Protocol обязан включать эти идентификаторы в контекст любого task/workflow.[web:346][web:349]

---

## 5. Permissions & Policy Model

Этот слой отвечает на вопрос: **что субъект может делать?**

### 5.1 Scopes

Scopes прав:

- **Tenant** — создание/удаление workspaces, глобальные лимиты.
- **Workspace** — доступ к задачам, артефактам, репозиториям.
- **Task / Workflow** — запуск, пауза, отмена, изменение конфигов.
- **Artifact** — чтение/редактирование/публикация/удаление.
- **Tool** — использование конкретных инструментов (shell, git, HTTP, внешние API).
- **Department** — запуск workflows департаментов, просмотр outcomes.[web:343]

### 5.2 Actions

Базовые действия:

- `read`
- `write`
- `execute`
- `approve`
- `publish`
- `override`
- `configure`

Пример:  
`agent_id=Sales.Outreach` может иметь `execute` на `lead_outreach_workflow` внутри конкретного `workspace_id`, но не иметь `execute` на `billing_refund_workflow` или `change_access`.[web:343][web:349]

### 5.3 Policy Representation

Policies задаются декларативно (YAML/JSON) и интерпретируются Policy Engine:

- `subject`: `user` / `agent` / `department`
- `scope`: `workspace` / `task` / `artifact` / `tool`
- `actions`: allow/deny
- `conditions`: лимиты по сумме, времени, типу данных, autonomy tier, risk‑классу.

Policy‑решения принимаются **до** опасных действий (см. Action Classes) и логируются в TraceStore/episodes как governance‑events.[web:342][web:351]

---

## 6. Action Classes

Чтобы governance был управляемым, Pith классифицирует действия по стабильноим типам, а не по конкретным tools.[web:342][web:351]

Рекомендуемые классы:

- `read`
- `retrieve`
- `analyze`
- `draft`
- `recommend`
- `write_internal`
- `write_external`
- `send`
- `publish`
- `mutate_system`
- `spend_money`
- `change_access`
- `delete`
- `export_sensitive`

Mapping tool→action_class хранится в tool registry: один tool может реализовывать несколько классов (например, CRM‑клиент — `read`, `write_internal`, `mutate_system`).

---

## 7. Autonomy Tiers

Этот слой отвечает на вопрос: **насколько самостоятельно субъект может действовать?**  
Он должен быть согласован с Kernel autonomy уровнями (L0–L4).[web:341][web:350]

### 7.1 Tier 0 — Advisory

- Разрешены: `read`, `retrieve`, `analyze`, `draft`, `recommend`.
- Запрещены: любые внешние side‑effects (`send`, `publish`, `mutate_system`, `spend_money`).

### 7.2 Tier 1 — Assisted Execution

- Агент может готовить действия и выполнять low‑risk `write_internal` и часть `mutate_system` в sandbox.
- Любые `send`/`publish`/`spend_money`/high‑impact `mutate_system` требуют approval.

### 7.3 Tier 2 — Supervised Autonomy

- Агент может автономно выполнять часть заранее одобренных workflow‑сегментов под budget/контекст‑ограничениями.
- High‑risk action classes всё ещё требуют approvals или escalation.

### 7.4 Tier 3 — Operational Autonomy

- Система может выполнять bounded operational actions автономно под жёсткими policy/OBS/EVAL‑контролями.[web:342]
- Используется только для хорошо оттестированных, обратимых сценариев.

### 7.5 Tier 4 — High‑Autonomy Restricted

- Только для крайне контролируемых, доказано стабильных workflows.
- Требует явного risk‑acceptance и усиленного мониторинга.

Для Pith v5–v6 целю является активное использование Tier 0–2, точечное Tier 3 и крайне ограниченный / почти отсутствующий Tier 4.[web:341][web:350]

---

## 8. Human‑in‑the‑Loop (Approval Model)

Этот слой отвечает на вопрос: **когда нужен человек?**

### 8.1 Approval States

Состояния approval:

- `pending_review`
- `approved`
- `rejected`
- `escalated`
- `expired`

Approval‑события должны быть частью trace/event‑потока и храниться в episodes/TraceStore.[web:338][web:351]

### 8.2 Checkpoints

Checkpoints — места, где Runtime обязан остановиться и ждать решения человека:

- customer‑facing `send` и `publish`,
- high‑impact `mutate_system` (деплой, конфиг‑смена, миграции),
- `spend_money` выше порогов,
- `change_access` и другие IAM‑чувствительные операции,
- `delete` и `export_sensitive` в production контекстах.[web:344][web:347]

### 8.3 Approval Patterns

Паттерны approval:[web:344][web:347]

- **Single approver:** один оператор подтверждает действие (минимум для большинства бизнес‑действий).
- **Two‑step:** reviewer → maintainer (например, код‑ревью → merge).
- **PR‑centered:** агент создаёт PR/черновик, люди ревьюят, отдельный gate мержит/публикует.
- **Timeout & fallback:** при отсутствии ответа до дедлайна действие отменяется или уходит в safe fallback.
- **Dual control:** для особо высоких рисков требуется два независимых approver’а.

Approval‑требования настраиваются per workflow/department/policy: `approval_required: never | sometimes | always` + условия (action_class, impact, сумма, tenant/workspace).

---

## 9. Governance Outcomes

Каждая policy‑проверка должна возвращать один из стабильных outcomes:[web:342]

- `allow`
- `allow_with_constraints`
- `require_approval`
- `deny`
- `escalate`

Outcomes должны быть:

- явными,
- сериализуемыми в TraceStore/episodes,
- снабжёнными ссылкой на policy/rule id.

### 9.1 allow

Действие разрешено без дополнительных ворот, при текущем autonomy tier и policy.

### 9.2 allow_with_constraints

Действие разрешено, но только с жёсткими лимитами:

- read‑only режим,
- cost cap,
- depth limit (например, глубина обхода репозитория),
- ограниченный набор tools,
- draft‑only output.[web:342][web:351]

### 9.3 require_approval

Нужен human gate перед dispatch или completion.

Governance обязан фиксировать:

- кто одобрил,
- при каком policy snapshot,
- какой был контекст (trace_id, workspace_id, autonomy tier).[web:338][web:340]

### 9.4 deny

Действие блокируется.  
Denials должны быть:

- явно артикулированы (reason, policy_id),
- объяснимы,
- логированы.

### 9.5 escalate

Действие слишком амбивалентно/рискованно для обычного approval‑пути и уходит в повышенный канал (security, compliance, owner).

---

## 10. Approval Matrix

Pith должен иметь матрицу approval, завязанную на action_class и blast radius, реализованную в policy engine.[web:342][web:350]

### 10.1 Typical approval‑required actions

Чаще всего требуют approval:

- customer‑facing `send`,
- публичный `publish`,
- pricing/offer commitments,
- CRM‑мутации с бизнес‑последствиями,
- `change_access` и другие IAM‑операции,
- prod‑impacting `mutate_system`,
- `spend_money` выше порогов,
- `export_sensitive` в проде,
- необратимые `delete` операций.

### 10.2 Typical allow‑with‑constraints actions

Можно разрешать с ограничениями:

- internal drafting,
- internal analysis,
- low‑risk research,
- read‑only retrieval,
- создание артефактов в sandbox‑пространствах.

Эта матрица должна жить не только в документации, но и в конфиге, откуда её читает Policy Engine.

---

## 11. Governance Objects

Governance‑решения применяются к нескольким типам объектов:

### 11.1 Workflow

- какой департаментный flow разрешён,
- какой autonomy tier допустим,
- какие budget‑лимиты применяются,
- нужны ли дополнительные approvals.

### 11.2 Action

- можно ли выполнить данный `send`/`publish`/`delete`,
- может ли конкретный tool быть вызван сейчас,
- нужен ли approval.

### 11.3 Context Access

- может ли агент читать этот memory/artifact,
- соблюдаются ли workspace‑границы,
- можно ли включать чувствительные документы в контекст.[web:343][web:349]

### 11.4 Output

- можно ли показать контент внешне,
- содержит ли артефакт ограниченные данные,
- требуется ли human‑review перед export/publish.

---

## 12. Policy Dimensions

Со временем Pith‑политики должны покрывать хотя бы такие измерения:[web:342]

- workspace / tenant boundary,
- роль / identity субъекта,
- action class,
- department,
- autonomy tier,
- budget / spend,
- data sensitivity,
- tool permissions,
- destination / recipient,
- reversibility,
- business criticality,
- compliance / risk категория.

Из этого должен вырасти формальный policy‑лексикон, который будет исполняться в runtime.

---

## 13. Governance & Observability

Governance опирается на observability.

Каждое важное governance‑решение должно быть трассируемо по:

- `trace_id`
- `tenant_id`
- `workspace_id`
- `task_id`
- `workflow_id`
- policy outcome (`allow` / `deny` / `require_approval` / `allow_with_constraints` / `escalate`)
- approval state и approver
- acting department / agent
- action class
- budget state
- dispatch result (success/fail/rollback).[web:342][web:351]

Если workflow не может объяснить, почему действие было разрешено, заблокировано или эскалировано, governance считается слабым.

---

## 14. Governance & Evaluation

Governance тоже должен измеряться.[web:342][web:345]

Примеры метрик:

- approval frequency,
- denial rate,
- policy violation attempts,
- action class distribution,
- autonomy tier distribution,
- high‑risk workflow completion rate,
- false‑positive approvals (over‑blocking),
- false‑negative approvals (under‑blocking),
- operator correction после approval.

Слишком слабый governance опасен, слишком шумный — непрактичен.

---

## 15. Governance & Agent Company

Так как Pith становится Agent Company OS, governance должен работать **междепартаментно**.[web:341][web:342]

Примеры:

- Sales‑агенты могут draft‑ить outreach, но отправка клиентам требует approval.
- Marketing‑агенты могут генерить кампании, но внешнее publish требует review.
- Research‑агенты могут собирать и синтезировать информацию, но sensitive отчёты требуют gating перед external share.
- Delivery‑агенты могут собирать артефакты, но prod‑release/launch требует повышенного доверия.
- Support/Ops‑агенты могут автономно закрывать low‑risk тикеты, но эскалации и финансовые корректировки требуют approvals.

Governance должен понимать **бизнес‑операции**, а не только технич. действия.

---

## 16. Minimum v1 Controls

Для Pith Governance v1 достаточно реализовать:

1. Классификацию действий (Action Classes).
2. Autonomy tiers (Tier 0–2 в активном использовании).
3. Список approval‑required действий.
4. Deny‑list для заведомо запрещённых действий.
5. `allow_with_constraints` режим.
6. Budget / spend ceilings per workspace/tenant.
7. Workspace‑scoped access control (identity + permissions).
8. Audit logging для всех gated действий.[web:342][web:351]

Это даёт практичный контур безопасности без иллюзии «идеального governance».

---

## 17. Out of Scope for v1

Не требуется немедленно:

- полный regulatory‑mapping по юрисдикциям,
- advanced policy DSL,
- формальная верификация политик,
- адаптивный risk engine,
- полный enterprise IAM (SCIM/SAML/OAuth) для всех сценариев.

Цель v1 — **practical runtime governance**, а не governance‑maximalism.

---

## 18. Next Integration Points

Этот документ должен повлиять на:

- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
- `docs/PITH_OBSERVABILITY_V1.md`
- `docs/PITH_EVALUATION_V1.md`
- `docs/PITH_AGENT_COMPANY_V1.md`
- `docs/PITH_BILLING_V1.md`
- planner/orchestrator routing logic
- tool registry contracts
- execution result schemas
- approval queue / operator console (CLI/Web/Telegram hooks)

Pith не должен увеличивать автономию, расширять монетизируемые workflows или открывать high‑impact tools без governance, которое:

- явно описано,
- прозрачно для оператора,
- enforce‑ится в Runtime.[web:342][web:351]