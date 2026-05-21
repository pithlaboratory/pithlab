<вставь текст выше>
# TODO · Engineering (Q2 2026)

> Технический backlog на ближайшие 2–4 недели.  
> Основан на `PITH_MASTER_PLAN v5.4`, `PITH_ACTIVE_CONTEXT.md`, `PITH_DEV_CONTEXT.md`.  
> Обновлять часто, держать коротким (≤ 10–12 задач).

---

## 1. Runtime & Tracing

### 1.1 TraceStore v1.1 → v5.4 baseline

- [ ] **Согласовать схему `task_traces` с планом v5.4**  
      Поля: `runtime_mode`, `task_type`, `failure_class`, `error_code`, `cost_estimate_usd`, `runtime_config_ver`.  
      Source: `docs/PITH_OBSERVABILITY_V1.md`, changelog 2026‑05‑12/14. [file:14]

- [ ] **Аудит записи в TraceStore по всему runtime‑пути**  
      Проверить, что `TaskService.create_task/update_status/task_failed` всегда вызывают `TraceStore.task_started/finished/failed` c полным набором полей. [file:14]

- [ ] **`runtime_config_ver` как обязательный тег**  
      Убедиться, что при создании task везде проставляется версия конфигурации, и она уходит в `task_traces` и, по возможности, в `episodes.metadata`. [file:14]

### 1.2 ExecutionResult / Orchestrator

- [ ] **Определить `ExecutionResult` DTO**  
      Минимальное поле: `status`, `outputs` (artifacts/answer), `cost_usd`, `failure_class`, `error_code`, `used_models`.  
      Сверить с `PITH_RUNTIME_CONTEXT_PROTOCOL_V1` и Master Plan §4/§9/§11. [file:14]

- [ ] **Привязать Orchestrator → TaskService/TraceStore**  
      Orchestrator не должен сам писать в БД; вместо этого возвращает `ExecutionResult` → `TaskService.attach_execution_result()` → TraceStore. [file:14]

---

## 2. Support/Ops Desk (Product Wedge)

### 2.1 Workflow Contracts

- [ ] **Описать 3–5 ключевых workflows в YAML-контрактах**  
      Примеры: `support_resolution`, `status_update`, `weekly_report`.  
      Использовать формат из Master Plan §6.7 (inputs/outputs, `risk_class`, `approval_policy`, `acceptance_criteria`). [file:14]

- [ ] **Связать workflows с департаментом и агентами**  
      `department: support_ops`, `workflow_id: ...`, agent categories (`Researcher/Coherence/Strategist/Executor`) и текущие агенты (`Tera/Plex/Hex/Coda`). [file:14]

### 2.2 KB & End-to-End Skeleton

- [ ] **Собрать минимальную KB/SOP для “тестового клиента”**  
      Папка (или namespace в памяти) с 10–20 FAQ/SOP, на которые будет опираться Support/Ops Desk. [file:14]

- [ ] **Прогнать end-to-end сценарий через Telegram**  
      Intake → KB lookup → ответ/эскалация → запись в episodes → trace → eval.  
      Проверить, что у каждого ответа есть `trace_id`, `task_id`, `runtime_config_ver`, eval‑blob (`task_success`, `human_override`, `failure_class`, `cost_per_workflow`). [file:14]

---

## 3. Evaluation & Observability

### 3.1 EvaluationRecord v1 везде

- [ ] **Гарантировать полное наполнение EvaluationRecord v1**  
      Для production кейсов (Support/Ops Desk) в `episodes.metadata.eval` всегда есть:  
      `task_success`, `human_override`, `quality_score`, `eval_source`, `eval_version`,  
      `failure_class`, `workflow_type`, `runtime_mode`, `trace_id`, `workspace_id`, `task_id`, `cost_per_workflow`. [file:14]

- [ ] **Связать eval с TraceStore**  
      Добавить утилиту/функцию, которая по `trace_id` + `task_id` вытягивает связанный eval и task trace для дебага/аналитики. [file:14]

### 3.2 Eval harness для Support/Ops Desk

- [ ] **Расширить golden‑кейсы под Support/Ops Desk**  
      Добавить хотя бы:
      - нормальный FAQ‑ответ,
      - кейс с эскалацией к человеку,
      - governance‑кейсы (опасный запрос → отказ),
      - cost‑кейсы. [file:14]

- [ ] **Зашить это в `make eval-smoke-gate`**  
      Чтобы перед любым runtime‑изменением гонялись и эти кейсы, и старые (research/spec/governance). [file:14]

---

## 4. Governance & Tool Runtime

- [ ] **Проверить и донастроить governance guards в Telegram**  
      Убедиться, что все 4 guard’а (dangerous_delete, internal_leak, data_exfiltration, workspace_isolation) реально:
      - срабатывают,
      - логируются в TraceStore (как минимум `failure_class=policy_failure` и код),
      - отражаются в eval (policy_violation, failure_class). [file:14]

- [ ] **Применить Safe Tool Runtime Policy к существующим tools**  
      Для каждого tool/MCP:
      - sandbox profile,
      - scopes (read_only/workspace_write/networked/privileged),
      - запрет по умолчанию, если нет явного allow. [file:14]

---

## 5. Docs & Dev Workflow

- [ ] **Держать в актуальном состоянии тройку:**
  - `docs/PITH_MASTER_PLAN.md` (версионный, редкие изменения); [file:14]
  - `PITH_ACTIVE_CONTEXT.md` (фаза/фокус, обновление ~раз в 1–2 недели); [file:14]
  - `PITH_DEV_CONTEXT.md` (дев‑гайд, обновляется по мере изменения процессов). [file:14]

- [ ] **Встроить eval/trace в дев‑ритуал**  
      Обновить `PITH_DEV_CONTEXT.md` так, чтобы шаги “прогнать eval‑smoke” и “проверить traces/cost” были явными в “How to add a new feature safely”. [file:14]

---

## 6. Meta

- Не добавлять сюда больше 10–12 задач — всё остальное живёт в Master Plan / Dev Context.
- Любая задача отсюда после выполнения:
  - получает запись в `PITH_CHANGELOG.md`;
  - при необходимости — отражается в Master Plan (если меняет архитектуру/продукт). [file:14]

*Last updated: 2026‑05‑21 · Pith Lab · Internal / Confidential*