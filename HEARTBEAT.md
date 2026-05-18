---
heartbeat:
  version: "2.1.0"
  last_updated: "2026-05-14"
  current_phase: "Phase 1 — Core stabilization / Runtime hardening baseline"
  active_objectives: [1, 2, 3]
  focus_areas: ["Стабильность", "Воспроизводимость", "Наблюдаемость", "Governance"]
---

# Pith Runtime Heartbeat

Динамические цели, текущий фокус и операционные приоритеты Pith Runtime.  
Файл обновляется по мере завершения фаз и появления новых задач.

Refer:
- `docs/PITH_KERNEL.md`
- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
- `docs/PITH_OBSERVABILITY_V1.md`
- `docs/PITH_EVALUATION_V1.md`
- `docs/PITH_GOVERNANCE_V1.md`
- `docs/PITH_ACTIVE_CONTEXT.md`
- `docs/PITH_DEV_CONTEXT.md`
- `docs/PITH_RUNTIME_CONTEXT_REVIEW_2026-05-14.md`

---

## 1. Текущие цели (Phase 1: Core stabilization + Runtime hardening baseline)

1. **[🟢] TraceStore v1 — task-level backbone + minimal hardening**

   - [x] Внедрён task‑level backbone (`task_traces` в `episodes.db`).
   - [x] Добавлены поля для базового trace contract:
     - `runtime_mode`, `task_type`, `failure_class`, `error_code`,
     - `cost_estimate_usd`, `runtime_config_ver`.
   - [x] Реализована безопасная миграция через `PRAGMA table_info` + `ALTER TABLE ... ADD COLUMN` (без ломки старых данных).
   - [x] `TaskService` пишет:
     - `task_started` → `task_id`, `workspace_id`, runtime metadata,
     - `task_finished` → `status='ok'`, `duration_ms`, `cost_estimate_usd`,
     - `task_failed` → `status='error'`, `error_type`, `failure_class`, `error_code`.
   - [x] Добавлен `FailureClass` enum и минимальная Failure taxonomy в `core/observability/failure_taxonomy.py`.
   - [ ] Гарантировать сквозной `trace_id` от интерфейса до результата (Telegram / CLI → Runtime → TraceStore).

2. **[🟡] Стабилизация TaskService / RuntimePlanner / Orchestrator**

   - [x] Минимальный аудит и hardening `TaskService`:
     - уточнены сигнатуры `update_status`,
     - передача `failure_class` / `error_code` в TraceStore,
     - фиксация `cost_usd` в completed trace.
   - [ ] Зафиксировать минимальный `ExecutionResult` для Orchestrator (DTO/словари, которые всегда пишутся в Trace/Artifacts).
   - [ ] Убедиться, что `RuntimeConfig` используется как версия поведения (не “магический глобал”) и фиксируется в trace / tasks / artifacts.
   - [ ] Проверить соответствие Planner/Orchestrator `PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`.

3. **[🟡] Governance baseline в коде (Tier 0–1)**

   - [ ] Зафиксировать autonomy envelope: только **L0–L1** (Tier 0–1 из `PITH_GOVERNANCE_V1.md`).
   - [ ] Сформировать минимальный `autonomy.yaml` (policy skeleton под Action Classes и Tiers).
   - [ ] Подготовить базу для PatchGate / RolloutManager / kill switch (структуры, но без включения auto‑rollout).

---

## 2. Ключевые метрики (KPI)

| Метрика                         | Текущее значение      | Цель (Phase 1)                          | Источник/комментарий                          |
|:--------------------------------|:----------------------|:----------------------------------------|:----------------------------------------------|
| Uptime Telegram runtime         | ~99%                  | >99.5%                                   | `systemctl status pith_v5.service`            |
| Uptime TraceStore (task_traces) | частично, v1.1 вкатан | ≥99% записей на рабочие задачи          | `episodes.db.task_traces`                     |
| Ошибки в `evolution.log`        | есть единичные        | 0 критических в неделю                  | `logs/evolution.log`                          |
| Время ответа бота (p95)         | ~2–5 сек              | <3 сек                                   | `llm_calls.latency_ms`                        |
| Количество `failure_cases`      | ~9 (`generic_error`)  | <5 новых в день, классифицированы       | `failure_cases` (с `failure_class`)           |
| Бюджет OpenRouter (месяц)       | ~$0.50 / $30          | <= $30                                   | `llm_calls.cost_usd`                          |
| Task success rate               | не измеряется явно    | начать считать (success/partial/failure)| PithEval v0.1 + runtime traces                |
| Human override rate             | не измеряется явно    | начать считать для приоритетных workflows | PithEval / operator feedback                 |

---

## 3. Ближайшие действия (Next Actions)

**Технические шаги (runtime hardening):**

- [ ] Добавить и проверить сквозной `trace_id`:
  - от интерфейса (Telegram/CLI) через Router/RuntimePlanner до TraceStore,
  - убедиться, что `trace_id` доступен в Evaluator/Diagnostics.
- [ ] Определить и зафиксировать минимальный `ExecutionResult`:
  - единый DTO/словарь для Orchestrator,
  - запись ExecutionResult → TraceStore / artifacts.
- [ ] Провести ContextAssembler audit:
  - сверить поведение с `PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`,
  - минимизировать persona drift и лишний self‑talk в NORMAL режиме.

**Governance / Evaluation:**

- [ ] Добавить базовую классификацию `failure_class` в Evaluator:
  - использовать taxonomy из `PITH_OBSERVABILITY_V1.md` / `PITH_EVALUATION_V1.md`,
  - начать считать распределение failure-class по workflow.
- [ ] Согласовать первые 3–5 `billable_event` типов с Agent Company (Sales/Marketing/Research):
  - привязать их к Trace/Task/llm_calls,
  - не запускать биллинг без прозрачного trace contract.

---

## 4. Предупреждения и блокеры (Warnings & Blockers)

- **Блокер:**  
  Если TraceStore не фиксирует `trace_id` / `task_status` / `failure_class` для рабочих задач, Observability/Evaluation не работают.  
  → Переход к L2 и Agent Company auto‑flows запрещён до исправления.

- **Внимание:**  
  Старые токены/секреты могут всё ещё встречаться в логах/конфиге.  
  Проверить `journalctl`, `.env`, `config.yaml` и очистить/заменить секреты.

- **Риск:**  
  RuntimePlanner и ContextAssembler пока не полностью соблюдают `PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`.  
  Любые расширения контекста или self‑analysis в NORMAL режиме повышают риск persona drift и должны фиксироваться Evaluator’ом.

---

## 5. Тон и состояние (Runtime Vibe Check)

Pith Runtime вышел из “реанимации” и находится в фазе **аккуратной стабилизации**.  
Фундамент ядра (Kernel / Observability / Evaluation / Governance) сформирован на уровне контрактов и документов, а кодовая база постепенно выравнивается под них.

Основные сигналы:

- **Состояние:** осторожный оптимизм, без права на самодовольство.
- **Фокус:** минимальные безопасные патчи в ядре, а не новые фичи.
- **Принцип:** “тихое давление” — архитектура и процессы мягко подталкивают к правильным решениям, не ломая разработчикам руки.

---

*Last updated: 2026‑05‑14 · Pith Runtime (operator: Pith Lab)*