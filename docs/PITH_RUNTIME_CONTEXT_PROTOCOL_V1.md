# PITH_RUNTIME_CONTEXT_PROTOCOL_V1

> Runtime‑native context envelope for Pith v5: identity, state, governance, artifacts, billing, and trace.

---

## 1. Purpose

Этот протокол определяет **единый формат runtime‑контекста** (context envelope) для задач и workflows в Pith.[cite:358]

Он отвечает на вопросы:

- кто действует (identity & subjects),
- что именно сейчас делается (task / workflow),
- в каком окружении (tenant / workspace / repo / memory),
- под какими ограничениями (policies, autonomy, budget),
- какие артефакты участвуют (inputs / outputs),
- как всё это трассируется и биллится (trace, billing scope).[cite:361][cite:365]

Все Runtime‑компоненты (Planner, Orchestrator, Agents, Tools, Evolution, Observability) должны использовать этот протокол как **single source of truth** о контексте.

---

## 2. Context Envelope Overview

Базовая сущность — **Runtime Context Envelope**:

- создаётся при старте `task` / `workflow` (по `task_id`),
- сопровождает все LLM‑вызовы, agent‑handoff, tool‑calls,
- сериализуется в TraceStore / episodes для реконструкции.[cite:359][cite:362]

В терминах JSON это объект вида:

```json
{
  "envelope_version": "1",
  "trace_id": "uuid-or-hex",
  "task": { ... },
  "subject": { ... },
  "workspace": { ... },
  "governance": { ... },
  "context": { ... },
  "artifacts": { ... },
  "billing": { ... },
  "runtime": { ... }
}
```

Далее описаны требования к каждому блоку.

---

## 3. Identity & Subject Block

### 3.1 subject

```json
"subject": {
  "tenant_id": "tenant-123",
  "workspace_id": "ws-repo-x",
  "user_id": "user-viktor",
  "acting_agent_id": "agent.Tera",
  "department_id": "dept.Research",
  "origin_interface": "telegram|cli|web"
}
```

- `tenant_id`, `workspace_id` — из State Plane (Workspace Substrate).
- `user_id` — инициатор работы (или `system` для внутренних задач).
- `acting_agent_id` — текущий агент, от имени которого выполняется шаг.
- `department_id` — департамент Agent Company (если применимо).
- `origin_interface` — интерфейс, откуда пришёл запрос (для UX/limits).[cite:343][cite:349]

### 3.2 identity snapshot

Опционально: инлайн‑снимок ключевых Identity‑атрибутов (roles, groups) для уменьшения числа round‑trips к IAM.

---

## 4. Task & Workspace Block

### 4.1 task

```json
"task": {
  "task_id": "task-uuid",
  "parent_task_id": null,
  "workflow_id": "wf.sales.outreach.v1",
  "task_type": "general_work|code_edit|research|workflow_run",
  "intent": "short natural language description",
  "created_at": "2026-05-18T13:40:00Z",
  "mode": "NORMAL|DIAGNOSTICS|VISION"
}
```

- `task_id` — ключевая сущность для TraceStore.
- `workflow_id` — для департаментных workflows.
- `task_type` — классификация Planner’а.
- `mode` — режим (`NORMAL`, `DIAGNOSTICS`, `VISION`, и др. — см. Kernel).[cite:361]

### 4.2 workspace

```json
"workspace": {
  "workspace_id": "ws-repo-x",
  "tenant_id": "tenant-123",
  "name": "Repo X",
  "repo_bindings": [
    {
      "repo_id": "repo-backend",
      "path": "/srv/repos/backend",
      "branch": "main"
    }
  ],
  "tags": ["engineering", "internal"]
}
```

Workspace‑блок служит для:

- правильной работы Memory/Artifacts,
- ограничений по данным (governance),
- привязки к billing scope.[cite:361][cite:366]

---

## 5. Governance Block

Этот блок соединяет **Governance v1** с runtime:

```json
"governance": {
  "policy_id": "policy-default-2026-05",
  "autonomy_tier": 1,
  "requested_autonomy_tier": 1,
  "action_class": "draft|send|mutate_system|spend_money",
  "approval_state": "none|pending_review|approved|rejected|escalated|expired",
  "approval_required": false,
  "approval_checkpoint_id": null,
  "permissions_snapshot": {
    "subjects": ["user:user-viktor", "agent:agent.Tera"],
    "allowed_actions": ["read", "draft", "write_internal"],
    "denied_actions": ["change_access", "delete"],
    "tool_permissions": {
      "tool.git": ["read", "write_internal"],
      "tool.crm": ["read"]
    }
  }
}
```

- `policy_id` — активная политика (из Governance).
- `autonomy_tier` — текущий уровень автономии (Tier 0–4).
- `requested_autonomy_tier` — уровень, который хочет runtime (для контроля повышения).
- `action_class` — текущий тип действия (см. Governance).
- `approval_state` / `approval_required` / `approval_checkpoint_id` — связь с HITL.[cite:338][cite:344]
- `permissions_snapshot` — минимальный снимок прав на момент шага (опционально).

Все решения Policy Engine должны ссылаться на этот блок и обновлять его по мере изменения состояния (approval, escalation, deny).

---

## 6. Context Block (Memory, Session, External)

### 6.1 Общая структура

```json
"context": {
  "session": {
    "history": [...],
    "summary": "short rolling summary"
  },
  "memory": {
    "short_term": [...],
    "episodic_refs": [...],
    "semantic_refs": [...],
    "profile_refs": [...]
  },
  "external": {
    "repo_fragments": [...],
    "docs_fragments": [...],
    "web_snippets": [...]
  },
  "working_set": {
    "system_instructions": "...",
    "agent_identity_prompt": "...",
    "selected_items": [...],
    "few_shots": [...]
  }
}
```

### 6.2 session

- `history` — последние n turn’ов (не обязательно полный диалог).
- `summary` — rolling summary для continuity.[cite:361]

### 6.3 memory.*

Здесь **ссылки**, а не весь payload:

```json
"memory": {
  "short_term": [
    { "episode_id": 1234 }
  ],
  "episodic_refs": [
    { "episode_id": 5678, "reason": "same topic" }
  ],
  "semantic_refs": [
    { "doc_id": "doc-abc", "chunk_id": "chunk-1" }
  ],
  "profile_refs": [
    { "profile_id": "user-viktor.pref-general" }
  ]
}
```

Реальные данные вытягиваются Retrieval‑слоем; ContextAssembler лишь решает, что **включать** в working_set.

### 6.4 external

Фрагменты из:

- репозитория (RepoIndexer),
- docs/notes,
- web‑ресёрча.[cite:355][cite:361]

### 6.5 working_set

То, что реально попадает в prompt текущей LLM‑операции:

- `system_instructions` — Kernel/Agent system message.
- `agent_identity_prompt` — persona/role агента.
- `selected_items` — куски истории, memory, external.
- `few_shots` — демонстрации.

ContextAssembler отвечает за сбор и pruning working_set.[cite:358][cite:361]

---

## 7. Artifact Block

Артефакты — first‑class layer (см. MASTER_PLAN).

```json
"artifacts": {
  "inputs": [
    { "artifact_id": "art-plan-123", "type": "plan", "role": "reference" }
  ],
  "outputs": [
    { "artifact_id": "art-report-456", "type": "report", "role": "draft" }
  ],
  "lineage": {
    "created_from_task_ids": ["task-uuid"],
    "derived_from_artifact_ids": ["art-plan-123"]
  }
}
```

- `inputs` — артефакты, которые используются как контекст.
- `outputs` — артефакты, создаваемые/обновляемые этим task.
- `lineage` — связи для последующего анализа и governance.[cite:357][cite:360]

Runtime обязан обновлять artifact block после создания/изменения артефактов.

---

## 8. Billing Block

Этот блок связывает runtime‑операции с billing model.

```json
"billing": {
  "tenant_id": "tenant-123",
  "workspace_id": "ws-repo-x",
  "billing_unit": "task|workflow|artifact|outcome",
  "billing_context": {
    "department_id": "dept.Sales",
    "workflow_id": "wf.sales.outreach.v1",
    "plan": "self_hosted|managed|vertical_pack",
    "tags": ["sales", "outreach"]
  },
  "cost_caps": {
    "task_usd_limit": 0.50,
    "workspace_monthly_usd_limit": 30.0,
    "premium_hops_limit": 8
  },
  "runtime_cost_estimate": {
    "input_tokens": 1234,
    "output_tokens": 567,
    "estimated_usd": 0.023
  }
}
```

- `billing_unit` — способ биллинга для данного task/workflow.
- `billing_context` — связи с департаментами/пакетами (Agent Company).
- `cost_caps` — лимиты (из budget policy).
- `runtime_cost_estimate` — живые оценки cost (для pre‑flight checks).[cite:365]

Policy Engine и Budget Guard читают/обновляют этот блок.

---

## 9. Runtime Block

Технические детали выполнения:

```json
"runtime": {
  "runtime_version": "5.2.0",
  "runtime_config_id": "rt-config-2026-05",
  "router_mode": "core|coder|agent|free|long_context|premium",
  "model_lane": "chat_default|code_paid|reasoner_free",
  "model_id": "deepseek/deepseek-v4-flash",
  "tool_plane": {
    "mcp_sessions": [
      { "server": "git-server", "session_id": "..." }
    ],
    "a2a_sessions": [
      { "peer_agent_id": "agent.Scheduler", "session_id": "..." }
    ]
  },
  "diagnostics": {
    "debug_flags": ["trace_context", "log_prompts"],
    "correlation_id": "optional-operator-defined"
  }
}
```

Здесь важно:

- `runtime_config_id` — чтобы можно было восстановить состояние конфигурации.
- `router_mode` / `model_lane` / `model_id` — для observability и eval.
- `tool_plane` — ссылочная информация о MCP/A2A‑сессиях.[cite:354][cite:356][cite:357]

---

## 10. Trace & Correlation

`trace_id` — ключевой корреляционный идентификатор:

- создаётся на старте `task`,
- общий для всех spans (LLM‑вызовы, tools, агенты, approvals),
- используется для связи логов, метрик, billing‑events и governance‑решений.[cite:359][cite:362][cite:365]

Рекомендуется:

- использовать W3C Trace Context/совместимый формат, чтобы легко сквозить через внешние системы;
- различать `trace_id` (операция) и `correlation_id` (батч, кампания, инцидент).[cite:362][cite:365]

---

## 11. Context Assembly & Pruning

### 11.1 Sources

ContextAssembler собирает working context из:

- session history,
- memory (short‑term, episodic, semantic, profile),
- artifacts,
- external sources (repo/docs/web),
- governance/billing/identity блоков (для system‑prompt).[cite:358][cite:361]

### 11.2 Heuristics

Для v1 достаточно:

- лимиты по токенам;
- приоритеты: свежий контекст и явно привязанные артефакты > старый history;
- фильтрация по workspace/tenant/permissions;
- маркировка чувствительных данных, чтобы governance мог принять решение.[cite:358][cite:361][cite:364]

---

## 12. Modes & Diagnostics

Протокол должен поддерживать режимы:

- `NORMAL` — обычный рабочий контекст.
- `DIAGNOSTICS` — расширенный логгинг, больше метаданных, включён `log_prompts` (для dev).
- `VISION` — контекст, включающий визуальные/мультимодальные поля (картинки, схемы).

Поле `task.mode` и `runtime.diagnostics.debug_flags` должны управлять объёмом данных и тем, что уходит в traces.[cite:361]

---

## 13. Backwards Compatibility

Старый `Runtime Context Protocol v1 (Deprecated)` остаётся только как шима/редирект:

- любые новые компоненты обязаны использовать `PITH_RUNTIME_CONTEXT_PROTOCOL_V1` как канон;
- изменения должны быть **backwards‑compatible**, пока `envelope_version` не поднимется (например, до `"2"`).

---

## 14. Invariants & Guarantees

Для любого валидного envelope Pith гарантирует:

1. `trace_id`, `task.task_id`, `subject.workspace_id`, `subject.tenant_id` **всегда присутствуют**.
2. Любая внешняя операция (tool/API/LLM) может быть связана с envelope через `trace_id`.
3. Governance/Billing/Eval могут восстановить контекст задачи **из одной записи** envelope + событий trace.[cite:359][cite:365]
4. Ни один агент не может получить контекст вне своих прав: ContextAssembler обязан учитывать `governance.permissions_snapshot`.

---

## 15. Integration Points

Этот протокол обязателен для:

- Planner / Orchestrator,
- Agent Company workflows,
- Runtime Evaluator (Eval Ops),
- Governance Engine,
- TraceStore / Observability,
- Billing Event pipeline,
- MCP/A2A bridging (tool plane).

Любая новая фича, меняющая контекст (новые поля/блоки), должна **сначала** приземляться в `PITH_RUNTIME_CONTEXT_PROTOCOL_V1`, и только потом — в реализацию.