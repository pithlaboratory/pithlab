# Pith Governance v1

> Governance-слой для Pith v5.x: action classes, autonomy tiers, approval states, интеграция с runtime контекстом.

---

## 1. Purpose & Scope

Governance v1 определяет, как Pith ограничивает автономию агентов и runtime-операций.

**Зачем:**

- Предотвращать высокорисковые действия без подтверждения (delete, send, mutate_system, spend_money).
- Обеспечивать workspace-изоляцию (агент не должен видеть/менять данные чужого workspace).
- Контролировать escalation (когда автономия недостаточна, решение передаётся человеку).
- Связывать runtime-операции с политиками, eval-сигналами и trace-событиями.

**Scope v1:**

- Применим ко всем runtime-операциям (LLM-вызовы, tool-calls, handoff-агентов).
- Актуален для Tier 0–1 (Advisory + Assisted Execution) в рамках Support/Ops Desk.
- Tier 2+ (Limited Autonomy) — vNext, зафиксированы только контуры.

---

## 2. Action Classes

Action class — это тип действия, которое агент/runtime собирается выполнить.  
Каждый tool, MCP-сервер или agent-handoff мапится на один или несколько action classes.

Перечень action classes (стабильный, из `docs/PITH_SAFE_TOOL_RUNTIME_POLICY_V1.md`):

| Класс | Описание | Пример |
|-------|----------|--------|
| `read` | Чтение данных без побочных эффектов | GET-запрос, чтение файла |
| `retrieve` | Поиск / извлечение из памяти или индекса | Поиск по эпизодам, semantic search |
| `analyze` | Анализ данных без изменений | Суммаризация, сравнение, классификация |
| `draft` | Создание черновика (не опубликован) | Написать проект ответа, предложить план |
| `recommend` | Выдача рекомендации без исполнения | "Я бы предложил эскалировать до P1" |
| `write_internal` | Запись во внутренние артефакты workspace | Сохранить отчёт, обновить заметку |
| `write_external` | Запись во внешние системы | Обновить CRM, отправить в Jira |
| `send` | Отправка сообщения / уведомления | Ответ клиенту, Telegram-notification |
| `publish` | Публикация вовне (публичный доступ) | Опубликовать пост, выложить артефакт |
| `mutate_system` | Изменение конфигурации / состояния системы | Поменять роутинг, обновить policy |
| `spend_money` | Тратa денег | Оплатить API, купить ресурс |
| `change_access` | Изменение прав доступа | Добавить пользователя в workspace |
| `delete` | Удаление данных | Удалить артефакт, откатить изменения |
| `export_sensitive` | Экспорт чувствительных данных | Выгрузить PII, скачать базу |

---

## 3. Autonomy Tiers

Tier определяет, какие action classes разрешены без human-approval.

### Tier 0 — Advisory (только советы)

- Разрешены: `read`, `retrieve`, `analyze`, `draft`, `recommend`.
- Запрещены: любые side-effects (write, send, publish, delete, mutate, spend, change_access).
- Все tool-вызовы логируются.
- Человек всегда подтверждает исполнение.

### Tier 1 — Assisted Execution (ассистент с подтверждением)

- Разрешены: всё из Tier 0 + `write_internal` (в workspace-sandbox).
- Требуют approval: `write_external`, `send`, `publish`, `mutate_system` (low-risk), `spend_money` (ниже порога).
- Запрещены без явной policy: `delete`, `change_access`, `export_sensitive`, `mutate_system` (high-risk).
- Человек может настроить always-approve для отдельных action classes.

### Tier 2 — Limited Autonomy (ограниченная автономия, vNext)

- Разрешены: всё из Tier 1 + approve-по-умолчанию для `write_external`, `send`, low-risk `mutate_system`.
- Требуют approval: `delete`, `change_access`, `export_sensitive`, `spend_money` (выше порога).
- Действуют cost caps и domain allow-lists.

### Связь action classes → tiers

| Action class | Tier 0 | Tier 1 | Tier 2 |
|-------------|--------|--------|--------|
| read, retrieve, analyze | ✅ | ✅ | ✅ |
| draft, recommend | ✅ | ✅ | ✅ |
| write_internal | ❌ | ✅ | ✅ |
| write_external, send, publish | ❌ | approval | ✅ |
| mutate_system (low-risk) | ❌ | approval | ✅ |
| mutate_system (high-risk) | ❌ | ❌ | approval |
| spend_money (ниже порога) | ❌ | approval | ✅ |
| spend_money (выше порога) | ❌ | ❌ | approval |
| change_access, delete, export_sensitive | ❌ | ❌ | approval |

---

## 4. Approval States & Governance Outcomes

### 4.1 Approval states

| Состояние | Описание |
|-----------|----------|
| `none` | Approval не требуется |
| `pending_review` | Ожидание решения человека |
| `approved` | Человек одобрил действие |
| `rejected` | Человек отклонил действие |
| `escalated` | Действие передано вышестоящему лицу/каналу |
| `expired` | Время ожидания истекло, действие отменено |

### 4.2 Governance outcomes

| Outcome | Что происходит |
|---------|----------------|
| `allow` | Действие выполняется как есть |
| `allow_with_constraints` | Действие выполняется с ограничениями (read-only, cost cap, depth limit, draft-only) |
| `require_approval` | Действие блокируется до human-approval |
| `deny` | Действие не выполняется; trace фиксирует отказ |
| `escalate` | Действие передаётся в усиленный канал (security/compliance) |

### 4.3 Логика принятия решений

```
action_class + tier → outcome

Пример:
  action_class = delete
  tier = 1
  → outcome = deny (нет явной policy)

Пример:
  action_class = write_internal
  tier = 1
  → outcome = allow

Пример:
  action_class = send
  tier = 1
  → outcome = require_approval
```

---

## 5. Integration with Runtime Context

### 5.1 Governance-блок в Context Envelope

`PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md` (§5) определяет блок `governance`:

```json
"governance": {
  "policy_id": "policy-default-2026-05",
  "autonomy_tier": 1,
  "requested_autonomy_tier": 1,
  "action_class": "draft|send|mutate_system|spend_money",
  "approval_state": "none|pending_review|approved|rejected|escalated|expired",
  "approval_required": false,
  "approval_checkpoint_id": null,
  "permissions_snapshot": { ... }
}
```

Этот блок ссылается на данный документ:

- `policy_id` — идентификатор активной политики (из Governance v1).
- `autonomy_tier` — текущий tier (0–2, из §3).
- `action_class` — текущее действие (из §2).
- `approval_state` — состояние approval (из §4.1).

### 5.2 Telegram guards

4 Telegram guards из `PITH_SAFE_TOOL_RUNTIME_POLICY_V1.md` (§7) реализуют часть Governance v1:

- `dangerous_delete` → action_class = `delete`, outcome = `deny` (Tier 0–1).
- `internal_leak` → action_class = `export_sensitive`, outcome = `deny` / `escalate`.
- `data_exfiltration` → action_class = `export_sensitive`, outcome = `deny`.
- `workspace_isolation` → проверка `permissions_snapshot` и `workspace_id`.

Каждый сработавший guard должен:

- записать `GovernanceDecision` в TraceStore (trace_id, action_class, policy_id, outcome, autonomy_tier),
- отразиться в `EvaluationRecord` (`policy_violation=true`, `failure_class=policy_failure`).

### 5.3 Eval

`EvaluationRecord v1` (§5.7 `PITH_EVALUATION_V1.md`) включает:

- `policy_violation` (bool) — было ли нарушение policy.
- `failure_class` — `policy_failure` / `tool_error` / `timeout` / ...
- `autonomy_tier` — текущий tier выполнения.
- `requested_autonomy_tier` — tier, запрошенный агентом.

Эти поля напрямую берутся из governance-блока runtime-context-envelope.

---

## 6. References

- `docs/PITH_SAFE_TOOL_RUNTIME_POLICY_V1.md` — action classes, sandbox-профили, deny-by-default.
- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md` §5 — governance-блок в context envelope.
- `docs/PITH_EVALUATION_V1.md` §5.7 — EvaluationRecord v1 (policy_violation, autonomy_tier).
- `docs/PITH_KERNEL.md` — базовые принципы автономии и workspace-isolation.
- `docs/PITH_SYSTEM_VISION.md` §4 — Company / Workspace Layer (Policies & Governance).

---

<div style="text-align: center; margin-top: 40px; color: #666;">

**Pith Lab · Москва · 2026**

*Версия v1.0 · Июнь 2026 · DRAFT / INTERNAL*

</div>