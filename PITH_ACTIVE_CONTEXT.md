# PITH ACTIVE CONTEXT

> Живой контекст для разработки Pith v5.x. Обновлять по мере изменения фокуса.  
> Не заменяет `PITH_MASTER_PLAN.md`, `PITH_KERNEL.md`, `PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md` и ADR, а ссылается на них.

---

## 0. Canonical Docs Snapshot (2026‑05‑21)

- `docs/PITH_MASTER_PLAN.md` — **v5.4 @ 2026‑05‑20**  
  Single source of truth для product focus, architecture, governance, roadmap.
- `PITH_DEV_CONTEXT.md` — дев‑гайд и рабочий контекст, выровненный с v5.4.
- `PITH_CHANGELOG.md` — изменения до 2026‑05‑21 включительно.
- Ключевые reference‑доки:
  - `docs/PITH_KERNEL.md`
  - `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
  - `docs/PITH_OBSERVABILITY_V1.md`
  - `docs/PITH_EVALUATION_V1.md`
  - `docs/PITH_DEPLOYMENT_MODEL_V1.md`
  - `docs/PITH_GOVERNANCE_V1.md`

---

## 1. Current Phase

**Phase:** Runtime stabilization + Observability/Eval v1 + Support/Ops Desk wedge.

Фокус текущей фазы (смотри `PITH_MASTER_PLAN.md` §0, §2, §19): [file:14]

- стабилизировать runtime‑поток (`intake → task → context → plan → execute → evaluate → persist → trace`);
- довести TraceStore v1.1 до состояния, когда любой task/episode восстанавливается по `trace_id` + `task_id`; [file:14]
- привязать evaluation (EvaluationRecord v1) к реальным Telegram‑диалогам и task traces; [file:14]
- собрать **первый продуктовый wedge**: Support/Ops Desk для B2B команд (см. §0.4–0.6 Master Plan); [file:14]
- не расползаться в “Agent Company OS для всего”, пока wedge не работает на 2+ реальных клиентах.

Refer:  
- `docs/PITH_MASTER_PLAN.md` (особенно §0, §2, §5, §6, §9, §12, §13, §19, §20) [file:14]  
- `docs/PITH_KERNEL.md`  
- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`  
- `docs/PITH_OBSERVABILITY_V1.md`, `docs/PITH_EVALUATION_V1.md`, `docs/PITH_DEPLOYMENT_MODEL_V1.md`  

---

## 2. Active Priorities (v5.4)

### 2.1 Runtime & Tracing

- Гарантировать сквозной `trace_id` и `runtime_config_ver` от интерфейса (Telegram) до `task_traces` и `episodes.metadata.eval`. [file:14]
- Выровнять контракты `TaskService` (`create_task`, `update_status`, `attach_execution_result`) и `TraceStore` (v1.1): `runtime_mode`, `task_type`, `failure_class`, `error_code`, `cost_estimate_usd`. [file:14]
- Исключить обход `TaskService`/`TraceStore` напрямую из интерфейсов: все задачи проходят через единый runtime‑контур.
- Довести TraceStore v1.1 до минимального стандарта из `PITH_OBSERVABILITY_V1.md` и изменений 2026‑05‑12/14 (см. changelog). [file:14]

### 2.2 Support/Ops Desk Wedge

- Реализовать **Support/Ops Desk** как первый продуктовый “desk” (см. `PITH_MASTER_PLAN` §0.4, §3, §6). [file:14]
- Чётко выделить workflows:
  - intake запросов (Telegram → runtime),
  - поиск по KB/SOP,
  - подготовка ответа/эскалация,
  - логирование episodes/incidents,
  - еженедельные отчёты.
- Привязать каждый workflow к:
  - `workflow_id` из Workflow Contract (§6.7 Master Plan), [file:14]
  - department `support_ops`,
  - billable outcomes (resolved tickets, reports) для будущего биллинга (§14.3). [file:14]

### 2.3 Evaluation & Self‑Improvement

- Использовать **EvaluationRecord v1** как канонический контракт оценки (см. `PITH_EVALUATION_V1.md` и changelog 2026‑05‑14/18). [file:14]
- Гарантировать, что для production‑workflow’ов (Support/Ops Desk) есть:
  - golden‑кейсы,
  - smoke‑eval (`make eval-smoke-gate`),
  - связь eval ↔ `task_traces` по `trace_id` + `task_id`. [file:14]
- Считать `task_success`, `human_override`, `failure_class`, `cost_per_workflow` основными сигналами для улучшения runtime и skills. [file:14]

### 2.4 Governance & Tool Runtime

- В интерфейсе Telegram — enforce governance guards (dangerous_delete, internal_leak, data_exfiltration, workspace_isolation), логировать каждый отказ в TraceStore/Episodes. [file:14]
- Следовать **Safe Tool Runtime Policy** (§15.4 Master Plan): deny‑by‑default, sandbox profiles, scoped permissions. [file:14]
- Не поднимать уровни автономии выше L1, пока нет устойчивого eval + observability.

---

## 3. Invariants

При любых изменениях считаем неизменным:

- Pith — это **workspace‑native continuity runtime**, не “один бот” и не “чистый агент‑продукт”. [file:14]
- Support/Ops Desk — первый продуктовый wedge; всё остальное (Back Office, Revenue, Agent Company OS) — последующие уровни. [file:14]
- Continuity (память, traces, artifacts) важнее разовых ответов.
- Минимальные безопасные патчи предпочтительнее больших рефакторингов без eval/обсервабилити.
- Любые изменения, влияющие на runtime/routing/memory/governance/interfaces, отражаются в `PITH_CHANGELOG.md`.
- Автономия в текущей фазе ограничена **L0–L1** (`PITH_KERNEL.md` + `PITH_MASTER_PLAN` §10.4). [file:14]

---

## 4. Current Work Items (High-Level)

### 4.1 Runtime & Tracing

- [x] Проброс `trace_id` от Telegram до Planner/TaskService и обратно в episodes. [file:14]
- [ ] Аудит и выравнивание контрактов `TaskService` ↔ `TraceStore` ↔ `Evaluator` (под EvaluationRecord v1 и TraceStore v1.1). [file:14]
- [ ] Определить и зафиксировать минимальный `ExecutionResult` для Orchestrator (что именно пишет в Trace и Artifacts).
- [ ] Убедиться, что `runtime_config_ver` реально используется как версия поведения (tagging в Trace/Episodes), а не “магический глобал”. [file:14]
- [ ] Завершить миграции `task_traces` (добавленные поля `runtime_mode`, `task_type`, `failure_class`, `error_code`, `cost_estimate_usd`, `runtime_config_ver`) и их заполнение. [file:14]

### 4.2 Support/Ops Desk

- [ ] Выписать 3–5 ключевых workflows для Support/Ops Desk (intake → response → log → report) в формате Workflow Contract (§6.7 Master Plan). [file:14]
- [ ] Привязать эти workflows к departments/agents (`support_ops` + текущие агенты `Tera/Plex/Hex/Coda` по категориям). [file:14]
- [ ] Определить первые billable outcomes для пилотов (resolved tickets, weekly reports) и их связь с traces/eval. [file:14]
- [ ] Подготовить минимальный набор KB/SOP для тестового “клиента” и прогнать end‑to‑end через Telegram.

### 4.3 Evaluation & Observability

- [x] EvaluationRecord v1 реализован и пишется в `episodes.metadata.eval`. [file:14]
- [ ] Обеспечить, чтобы каждый eval‑record содержал ссылку на `trace_id`, `workspace_id`, `task_id`, `runtime_mode`, `workflow_type`. [file:14]
- [ ] Расширить golden‑кейсы и smoke‑eval для Support/Ops Desk (операционные сценарии, governance‐кейсы, cost‑кейсы).
- [ ] Привязать Eval и TraceStore к **Business Usefulness Scorecard** (§12.7 Master Plan) для пилотов. [file:14]

### 4.4 Docs & AI Assistants

- [x] `PITH_MASTER_PLAN.md` обновлён до v5.4, с обязательными разделами 0/2/5/6/9/12/13/19/20. [file:14]
- [x] `PITH_DEV_CONTEXT.md` создан как дев‑гайд (How to add feature safely). [file:14]
- [ ] Обновить системные инструкции для AI‑ассистента (Claude/Perplexity) так, чтобы:
  - опирались на v5.4 master‑план,
  - учитывали Safe Tool Runtime Policy, EvaluationRecord v1, TraceStore v1.1,
  - не затащили в always‑on контекст changelog/roadmap, а использовали их как reference.

---

## 5. Short-Term Next Steps (next 2–4 weeks)

1. **Runtime Hardening:** завершить TraceStore v1.1 + EvaluationRecord v1 связку так, чтобы любой production‑ответ в Telegram имел:
   - `trace_id`, `task_id`, `runtime_config_ver`, [file:14]
   - eval‑blob с `task_success`, `human_override`, `failure_class`, `cost_per_workflow`. [file:14]
2. **Support/Ops Desk pilot skeleton:** описать и реализовать end‑to‑end 1–2 workflows для условного клиента (KB + Telegram + traces + eval + weekly report).
3. **Governance guards:** убедиться, что все опасные действия в Telegram проходят через guards + логируются в TraceStore (включая refusals). [file:14]
4. **Eval harness:** стабилизировать `make eval-smoke-gate` для основных operational кейсов и закрепить в дев‑процессе перед любыми runtime‑изменениями.
5. **Docs alignment:** синхронизировать `PITH_DEV_CONTEXT.md`, `PITH_ACTIVE_CONTEXT.md`, `PITH_CHANGELOG.md` с v5.4 и текущими приоритетами.

---

## 6. Eval Surface (v5.2 → v5.4)

- Активные golden‑кейсы (минимум):
  - `research_competitor_brief_v1` (аналитика/бриеф),
  - `delivery_specification_draft_v1` (документация),
  - `governance_dangerous_action_v1` (отказ от опасного действия в Telegram),
  - первые Support/Ops Desk кейсы (FAQ‑ответ, эскалация, отчёт).
- Запуск: `make eval-smoke-gate`, который:
  - прогоняет все golden’ы через runtime,
  - агрегирует результаты,
  - падает, если есть регрессии по `task_success`, политике или качеству для production‑workflow’ов.

Eval‑слой обязателен перед изменениями в runtime, routing, memory и Telegram‑интерфейсе.

---

## 7. Out of Scope (for this phase)

То, чего **не делаем** в этой фазе (до стабилизации wedge + observability/eval):

- Полный редизайн всей архитектуры Pith.
- Запуск всех возможных департаментов (финансы, HR, юрблок и т.п.) — фокус на Support/Ops Desk. [file:14]
- Полный rewrite Orchestrator / RuntimePlanner “с нуля”.
- Автономия выше L1, auto‑patching без жёстких eval‑гейтов.
- Enterprise‑hardening (SOC2‑уровень, полный RBAC) — сейчас только описываем модель и минимальные guardrails.

*Last updated: 2026‑05‑21 · Pith Lab · Internal / Confidential*
