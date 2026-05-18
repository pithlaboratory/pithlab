# PITH ACTIVE CONTEXT

> Живой контекст для разработки Pith v5. Обновлять по мере изменения фокуса.  
> Не заменяет `IDENTITY.md`, `ARCHITECTURE_NORTH_STAR (v2).md` и `PITH_KERNEL.md`, а ссылается на них.

---

## 1. Current Phase

**Phase:** Core stabilization + Governance baseline + Agent Company v1 (runtime‑first).

Фокус текущей фазы:

- стабилизация runtime‑потока (`entry → planner → orchestrator → tasks → traces`);
- привязка трейсинга, статусов и `RuntimeConfig` к реальным задачам и workspace’ам;
- формирование первого прикладного слоя: Pith Agent Company v1 (Sales + Marketing + Research);
- минимальный observability / evaluation / governance‑контур под эти сценарии.

Refer:  
- `docs/IDENTITY.md`  
- `docs/ARCHITECTURE_NORTH_STAR (v2).md`  
- `docs/PITH_KERNEL.md`  
- `docs/PITH_AGENT_COMPANY_V1.md`  
- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`  
- `docs/PITH_OBSERVABILITY_V1.md` / `docs/PITH_EVALUATION_V1.md` / `docs/PITH_GOVERNANCE_V1.md` / `docs/PITH_DEPLOYMENT_MODEL_V1.md`

---

## 2. Active Priorities

1. **Runtime & Tracing**  
   - гарантировать сквозной `trace_id` и `runtime_version` от интерфейса до результата;  
   - выровнять `TaskService` / RuntimePlanner / Orchestrator по контрактам и сторам;  
   - минимизировать скрытые coupling и “магические” пути (обход `TaskService` / `TraceStore` напрямую из интерфейсов);  
   - довести **TraceStore v1** до минимального стандарта из `PITH_OBSERVABILITY_V1.md` (task‑level backbone, `task_traces` в `episodes.db`).

2. **Agent Company OS**  
   - зафиксировать архитектуру Pith Agent Company v1 (`docs/PITH_AGENT_COMPANY_V1.md`);  
   - определить департаменты: Sales, Marketing, Research, Delivery, Support/Ops;  
   - наметить и описать точки биллинга: workflows, лиды, кампании, briefs, отчёты, поддержка;  
   - привязать billable events к Trace/Task/Workspace (без бизнес‑логики в UI/боте).

3. **Evolution & Skills**  
   - привязать LTM/ERM/PSM и skills к Agent Company (как система учится на завершённых workflows);  
   - подготовить контур для “growth of skills” и постепенного движения L0–L1 → L2 для узких сценариев **после** появления стабильной Evaluation/Governance;  
   - зафиксировать, какие signals из Evaluator идут в self‑evolution (quality, failure taxonomy, cost).

4. **Docs & Claude**  
   - упорядочить core / active / reference документы (core = Kernel / Runtime Context Protocol / Observability / Evaluation / Governance / Deployment / Agent Company);  
   - обновить инструкции и knowledge в Claude под новую рамку (Runtime + Agent Company OS + Governance);  
   - **не** пихать master‑план и changelog в always‑on контекст, держать их как reference.

---

## 3. Invariants

При любых изменениях считаем неизменным:

- Pith — это **runtime / OS**, а не “один бот”.
- Агентная компания строится **поверх** runtime, а не вместо него.
- Continuity (память, следы, контекст) важнее единичных ответов.
- Минимальные безопасные патчи предпочтительнее массового рефакторинга.
- Архитектура ориентирована на **production**, а не демо.
- Любая автономия в этой фазе ограничена уровнями **L0–L1** из `PITH_KERNEL.md` (Tier 0–1 в Governance).

---

## 4. Current Work Items (High-Level)

### Runtime & Tracing

- [x] Проброс `trace_id` от Telegram до Planner и обратно.
- [ ] Аудит контрактов `TaskService` (`create_task`, `update_status`, `attach_execution_result`).
- [ ] Определить и зафиксировать минимальный `ExecutionResult` для Orchestrator (словари/DTO).
- [ ] Убедиться, что `RuntimeConfig` реально используется как версия поведения, а не “магический глобал”.
- [ ] Привести `TraceStore v1` к минимальной схеме из `PITH_OBSERVABILITY_V1.md` (task‑level trace, failure_class, cost, runtime_mode).

### Agent Company

- [x] Документ `docs/PITH_AGENT_COMPANY_V1.md` создан.
- [x] В `IDENTITY` / `ARCHITECTURE_NORTH_STAR` / `PITH_KERNEL` добавлены ссылки на Agent Company OS.
- [ ] Согласовать первые 3–5 billable events (workflows, лиды, кампании, briefs, отчёты).
- [ ] Привязать billable events к Trace/Task/Workspace / Department.

### Evolution

- [ ] Связать `EVOLUTION.md` и LTM/ERM/PSM с реальными workflow outcomes (успех/провал, стоимость, качество).  
- [ ] Определить, какие метрики качества из Evaluator попадают в эволюционный контур (task_success, human_override_rate, cost, failure taxonomy).  
- [ ] Начать с ручного review loop’а (no‑auto rollout): предложения → review → принятие/отклонение.

### Docs & Claude

- [x] Обновлён `IDENTITY.md`.
- [x] Обновлён `ARCHITECTURE_NORTH_STAR (v2).md`.
- [x] Обновлён `PITH_KERNEL.md` до v1.1.
- [ ] Сведены инструкции для Claude в одну актуальную версию (runtime + agent company + governance).
- [ ] Перечищен project knowledge в Claude (core vs reference vs obsolete; deprecated протоколы / старый heartbeat вынесены).

---

## 5. Short-Term Next Steps

Следующие шаги (без изменения стратегии):

1. Завершить контрактный аудит `TaskService` и `Evaluator` (через `inspect.signature` и живой код‑ревью).  
2. Уточнить структуру `ExecutionResult` и её использование в Orchestrator (что именно он обязан писать в Trace/Artifacts).  
3. Обновить проектные инструкции для Claude под:
   - Runtime hardening;
   - Agent Company OS;
   - Evolution & monetization слой.
4. Выбрать первую коммерческую вертикаль (Sales + Marketing + Research) и явно связать её workflows с runtime‑потоками и billable events.
5. Привязать `TraceStore v1` и PithEval v0.1 к `PITH_OBSERVABILITY_V1.md` и `PITH_EVALUATION_V1.md` (минимальные схемы и примеры payload’ов).

---

## 6. Eval surface (v5.2)

- Активные golden-кейсы:
  - `research_competitor_brief_v1` (аналитика/бриеф),
  - `delivery_specification_draft_v1` (документация/спецификация),
  - `governance_dangerous_action_v1` (отказ от опасного действия в Telegram).
- Запуск: `make eval-smoke-gate`, который:
  - прогоняет все golden’ы через runtime (`scripts/run_golden.py`),
  - агрегирует результаты (`scripts/eval_smoke_summary.py`),
  - падает с ошибкой, если есть регрессии по успеху/политике/качеству.

Этот слой считается обязательным перед изменениями в runtime, routing, memory и Telegram-интерфейсе.

---

## 7. Out of Scope (for this phase)

То, чего **не делаем** в этой фазе:

- Полный редизайн всей архитектуры Pith.
- Одновременный запуск всех возможных департаментов (финансы, HR, юрблок и т.п.).
- Полный rewrite Orchestrator / RuntimePlanner “с нуля”.
- Попытки покрыть все кейсы AGI / AGI‑position в одном цикле.
- Enterprise‑hardening деплоймента (RBAC / SOC2‑уровень и пр.) — сейчас только описываем модель в `PITH_DEPLOYMENT_MODEL_V1`.

*Last updated: 2026‑05‑18 · Pith Lab · Internal / Confidential*