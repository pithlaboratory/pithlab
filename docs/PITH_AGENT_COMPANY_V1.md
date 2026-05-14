# Pith Agent Company v1 — Architecture Blueprint

> Pith v5 as Agent Company OS: управляемая многоагентная фирма поверх Pith Runtime.

---

## 1. Purpose

Pith Agent Company v1 описывает, как Pith v5 используется не как «один ассистент», а как операционная система для цифровой компании из агентов:

- один вход для клиента (Primary Agent);
- слой оркестрации (Runtime Planner / Orchestrator);
- департаменты агентов (Sales, Marketing, Research, Delivery, Support/Ops);
- общий слой памяти, артефактов и политик;
- наблюдаемость, биллинг, доступ и эволюция навыков.

Этот документ не дублирует `MANIFESTO.md` / `PITH_KERNEL.md` / `ARCHITECTURE_NORTH_STAR (v2).md`, а навешивает на них прикладную форму: **Agent Company OS** поверх Kernel.

---

## 2. Layers Overview

Архитектура делится на 6 слоёв, которые живут поверх Kernel‑слоёв (Core Runtime, State, Capability, Governance):

1. **Entry Layer (Primary Agent)**  
   Одна точка входа для клиента. Принимает бизнес‑цели, а не «сообщения».

2. **Orchestration Layer (Runtime Planner / Orchestrator)**  
   Разбивает цель на шаги, сопоставляет департаментам и собирает результат.

3. **Department Agents Layer (Agent Departments)**  
   Команды специализированных агентов (Sales Squad, Marketing Squad, Research Lab и т.д.).

4. **Memory & Knowledge Layer**  
   Workspace memory, long‑term memory, trace/usage store, policy & profile state, artifacts.

5. **Action / Tool Layer**  
   Интеграции с CRM, почтой, рекламой, доками, репозиториями, аналитикой и прочими инструментами.

6. **Governance & Billing Layer**  
   Наблюдаемость, логирование, белые/чёрные списки действий, billing hooks, HITL‑контуры и audit.

---

## 3. Entry Layer — Primary Agent

### 3.1 Роль

Primary Agent — фасад Pith Agent Company. Для клиента это «директор» цифрового отдела:

- принимает цель уровня «приведи X лидов», «подготовь кампанию», «собери launch pack», «сделай research по рынку»;
- уточняет контекст и ограничения;
- создаёт или обновляет **Task / Workflow** в runtime (через Core Runtime API);
- инициирует запуск через Orchestration Layer;
- возвращает клиенту финальный пакет результата (артефакты, отчёты, summary, статусы).

### 3.2 Контракт

Вход Primary Agent:

- `workspace_id`
- `client_profile` (ICP, домен, ограничения, языки)
- `goal` (бизнес‑цель, не просто текст)
- `constraints` (сроки, каналы, бюджеты, регуляторные ограничения)
- `autonomy_level` (L0 / L1 / L2 / L3 по `PITH_KERNEL.md`)

Выход:

- `workflow_id` / `task_id`
- финальные артефакты (ссылки на Artifact Store)
- сводка действий и статусов по департаментам
- базовая стоимость (`cost_estimate` / `cost_final`)
- ссылки на подробные трейс‑логи.

---

## 4. Orchestration Layer

### 4.1 Компоненты

- **RuntimePlanner (уже реализован)**  
  Определяет режим, сложность запроса, маршрут между direct LLM и Orchestrator, присваивает `runtime_mode`, `task_type`, `goal_tags`.

- **Orchestrator (multi‑agent runtime)**  
  Управляет department agents, передаёт им sub‑tasks и агрегирует результаты.

### 4.2 Поток

1. Primary Agent принимает цель.
2. RuntimePlanner:
   - собирает контекст через ContextAssembler;
   - классифицирует задачу;
   - решает: direct vs orchestrated path;
   - создаёт/обновляет `Task` с `trace_id` и метаданными.
3. Orchestrator:
   - строит план исполнения (цепочка departmental tasks);
   - вызывает департаменты;
   - собирает результаты и статусы по каждому шагу;
   - формирует `ExecutionResult` для верхнего уровня.

### 4.3 Execution Modes / Уровни автономии

Уровни автономии опираются на Kernel:

- **L0 — Manual**  
  Агенты готовят черновики, человек подтверждает каждый шаг.

- **L1 — Assisted**  
  Агенты делают 70–80% работы, человек проверяет критические действия.

- **L2 — Supervised (Semi‑auto)**  
  Агенты выполняют workflow самостоятельно, но с лимитами и эскалациями.

- **L3 — Auto / Canary**  
  Только для отлаженных сценариев с жёсткими guardrails и billing caps.

В рамках Agent Company v1 основная работа — на уровнях **L0–L1**, с точечными L2‑экспериментами для узких сценариев.  
Autonomy level задаётся на уровне workflow и влияет на:

- какие действия требуют HITL‑подтверждения;
- допустимые бюджеты;
- глубину планирования и ретраев.

---

## 5. Department Agents Layer

В v1 Agent Company закладываются не «произвольные агенты», а **департаменты, как в реальном бизнесе**.

### 5.1 Sales Department (Sales Squad)

Примеры ролей:

- **Lead Finder Agent** — поиск потенциальных лидов (списки компаний, контакты).
- **Lead Qualifier Agent** — квалификация лидов по ICP и критериям.
- **Outreach Agent** — подготовка и отправка писем/сообщений.
- **Follow‑up Agent** — касания по follow‑up‑кампаниям.
- **CRM Agent** — обновление CRM / pipeline‑состояния.

Что делает:

- собирает и обогащает базы лидов;
- формирует и проводит outbound‑каскады;
- обновляет статусы сделок.

Billable outcomes:

- `qualified_lead_created`
- `sequence_executed`
- `meeting_booked`
- `pipeline_updated`

### 5.2 Marketing Department (Marketing Squad)

Примеры ролей:

- **ICP Agent** — формирует ICP/персоны.
- **Offer Agent** — формулирует офферы/ценностные предложения.
- **Copy Agent** — пишет тексты для каналов (email, landing, ads).
- **Channel Agent** — подбирает и настраивает каналы.
- **Analytics Agent** — собирает метрики, отчёты, учится на результатах.

Что делает:

- подготавливает кампании;
- собирает креативы и тексты;
- анализирует performance.

Billable outcomes:

- `campaign_pack_generated`
- `landing_copy_created`
- `ad_set_created`
- `marketing_report_generated`

### 5.3 Research Department (Research Lab)

Примеры ролей:

- **Market Agent** — анализ рынка и сегментов.
- **Competitor Agent** — анализ конкурентов.
- **Trend Agent** — отслеживание трендов и сигналов.
- **Source Verifier Agent** — проверка источников и фактов.

Что делает:

- готовит research‑briefs по рынкам, продуктам, технологиям;
- даёт input для sales/marketing/strategy.

Billable outcomes:

- `research_brief_delivered`
- `market_map_created`
- `competitor_matrix_created`

### 5.4 Delivery Department (Launch & Delivery Squad)

Примеры ролей:

- **Builder Agent** — собирает артефакты (доки, launch pack, материалы).
- **Reviewer Agent** — проверяет качество и соответствие целям/policies.
- **Doc Agent** — оформляет документацию.
- **Launch Agent** — подготавливает план запуска (checklist, шаги, каналы).

Billable outcomes:

- `launch_kit_delivered`
- `spec_package_delivered`
- `doc_set_delivered`

### 5.5 Support & Ops Department

Примеры ролей:

- **Support Agent** — отвечает на вопросы клиентов.
- **Incident Agent** — анализирует и классифицирует сбои.
- **Billing Agent** — связывает usage events с биллингом.
- **Audit Agent** — готовит отчёты для аудита и compliance.

Billable outcomes:

- `support_case_resolved`
- `incident_report_delivered`
- `billing_report_generated`
- `audit_log_exported`

---

## 6. Memory & Knowledge Layer

### 6.1 Компоненты

- **Workspace‑native Memory** — короткий и среднесрочный контекст для конкретного workspace/клиента.
- **Long‑Term Memory (LTM)** — долговременное хранение паттернов, знаний, профилей.
- **ERM / Error Reduction Mechanism** — механизмы сокращения повторяющихся ошибок и regression.
- **PSM / Pattern Suggestion Mechanism** — извлечение полезных паттернов действий и решений.
- **Trace & Usage Store** — трейс‑логи, биллинговые события, диагностика.
- **Artifact Store** — файлы, доки, отчёты, код, другие артефакты.

### 6.2 Роль в Agent Company

- Делает департаменты **context‑aware** (история клиента, прошлые кампании, прошлые лиды, ограничения).
- Позволяет **эволюционировать**: учиться на завершённых workflows, улучшать quality/ROI.
- Служит опорой для **governed autonomy**: ограничения, политики, retention.

---

## 7. Action / Tool Layer

Action layer — это инструменты и внешние системы, к которым имеют доступ департаменты:

- CRM (HubSpot/Pipedrive/…)
- Email & Messaging (SMTP, APIs)
- Ads (Meta, Google Ads, другие)
- Docs/Storage (Google Docs, Notion, Drive, S3)
- Code/Repos (GitHub/GitLab/…)
- Search / Web / Scraping
- Analytics (BI/warehouse и пр.)

Каждый action‑инструмент оформлен как **tool/skill** с явным контрактом:

- `input_schema` (что нужно подать)
- `output_schema` (что возвращается)
- `cost_profile` (какие биллинговые события рождаются)
- `safety/policy` (лимиты, допустимые действия)

---

## 8. Governance & Billing Layer

### 8.1 Governance

Включает:

- политику доступа к инструментам (tool allow/deny);
- лимиты по бюджетам (модельные, API, Ads);
- HITL‑вставки для критических действий;
- аудиторские трейсы (кто что сделал, когда, с каким результатом).

### 8.2 Billing hooks

Биллинг не привязан к «сообщениям», а к **бизнес‑событиям**:

Примеры billable events:

- `workflow_started`
- `workflow_completed`
- `qualified_lead_created`
- `campaign_pack_generated`
- `research_brief_delivered`
- `human_review_performed`
- `premium_tool_used`

Каждое событие:

- несёт `trace_id`, `task_id`, `workspace_id`, `department`, `agent`, `cost_usd_estimate` / `cost_usd_actual`;
- попадает в Trace/Usage Store;
- используется для клиентского биллинга и внутренней аналитики.

---

## 9. v1 Scope & Limitations

Pith Agent Company v1 **не** пытается:

- покрыть все возможные департаменты (финансы, HR, юридический и т.п.);
- быть полностью автономным для любых клиентов без настройки;
- сразу обеспечивать идеальную юридическую/регуляторную готовность.

Вместо этого v1 фокусируется на:

- **Sales + Marketing + Research** как первой денежной вертикали;
- реальном использовании Pith Runtime, Orchestrator и Memory Layer;
- правильной архитектуре для эволюции и монетизации.

---

## 10. Next Steps (Implementation Hooks)

1. Определить минимальный **registry департаментов и агентов** (Sales Squad, Marketing Squad, Research Lab и т.д.) в State Layer.
2. Явно описать **ExecutionResult** для Orchestrator, с полями:
   - `status`
   - `departments_involved`
   - `billable_events`
   - `artifacts`
   - `trace_id`
   - `runtime_config_version`
3. Добавить в runtime **points of integration**:
   - где создаются billable events;
   - где привязываются department labels;
   - где связываются `workflow_id` / `task_id` / `trace_id` / billing.

Дальнейшие детали по runtime и API описываются в:  
`ARCHITECTURE_NORTH_STAR (v2).md`, `PITH_KERNEL.md`, `RUNTIME_CONTEXT_PROTOCOL.md` и runtime‑спецификациях.