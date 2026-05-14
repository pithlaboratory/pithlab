# Pith Runtime Context Protocol v1

> **Purpose:** Defines how Pith assembles context for runtime execution: sources, ordering, priority, pruning rules, and mode-dependent behavior.  
> **Alignment:** Implements `PITH_KERNEL.md`, `ARCHITECTURE_NORTH_STAR (v2).md`, `PITH_AGENT_COMPANY_V1.md`, `PITH_OBSERVABILITY_V1.md` at the runtime behavior level.  
> **Status:** `ACTIVE`  
> **Last updated:** 2026-05-14  
> **Owner:** Core Runtime Engineering

---

## 1. Purpose & Link to Architecture

Этот протокол описывает, как Pith собирает контекст для runtime‑задач и LLM‑вызовов: из каких источников, в каком порядке, в зависимости от режима работы и budget / governance constraints.

**Цели:**

- Сделать поведение Pith стабильным, предсказуемым и контролируемым.
- Уменьшить persona drift и лишнюю саморефлексию в рабочих сценариях.
- Эффективно использовать контекстное окно: short‑term history, summaries, memory, artifacts, repo/docs/web context.
- Гарантировать, что каждый вызов соответствует North Star и Kernel: continuity, governability, task‑focus, workspace/tenant isolation.
- Привязать контекст к каноническим runtime‑сущностям, а не к “истории чата как таковой”.

---

## 2. Canonical Runtime Scope

Контекст в Pith всегда собирается **не вокруг чата**, а вокруг runtime‑единиц работы.

Канонические runtime‑объекты, к которым может быть привязан контекст:

- `Tenant`
- `Workspace`
- `User`
- `Task`
- `Workflow`
- `Artifact`
- `MemoryRecord`
- `Trace`
- `RuntimeConfig`
- `PolicyDecision`
- `Department` / `Agent Role` (Agent Company layer)

**Правило:** если информация должна пережить одну сессию и влиять на будущие решения, она должна существовать как сущность State Layer, а не как неструктурированная история сообщений.

---

## 3. Sources of Context

Для каждого runtime‑вызова Planner’а и/или LLM доступны следующие типы контекста:

| # | Источник | Назначение |
|---|----------|-----------|
| 1 | **System / Runtime Policy** | Kernel axioms, autonomy limits, budget rules, anti‑goals, role/mode constraints, deployment/gov settings |
| 2 | **Task / Workflow Intent** | Текущий запрос пользователя, business goal, task_type, explicit constraints, autonomy tier |
| 3 | **Short-Term Conversation** | Последние `N` сообщений текущего execution window |
| 4 | **Conversation Summary** | Компактное резюме старой истории, если она уже не влезает в short‑term window |
| 5 | **Memory Records** | Эпизодическая/семантическая память: прошлые задачи, решения, ошибки, lessons learned |
| 6 | **Task / Workflow / Artifact Context** | Файлы, артефакты, промежуточные результаты, task/workflow metadata |
| 7 | **Knowledge Context** | Repo/docs/web/file context, retrieved через tools / retrieval pipeline под политиками |
| 8 | **Trace / Governance Signals** | Предыдущие решения, applied policies, runtime_config_version, failure patterns, billable events |

---

## 4. Runtime Modes

Planner всегда работает в одном из трёх режимов. **Режим определяется RuntimePlanner** на основе текущего запроса, недавней истории, task_type и контекстных триггеров.

| Режим | Триггер | Цель |
|-------|---------|------|
| `NORMAL` | По умолчанию | Ответы, выполнение задач, планирование, стандартный рабочий поток |
| `DIAGNOSTICS` | Сигналы: `сломалось`, `ошибка`, `traceback`, `баг`, `fix`, `не работает`, incident‑like phrasing | Локальная диагностика, конкретные шаги фикса, structured troubleshooting |
| `VISION` | Явный запрос: `архитектура`, `roadmap`, `эволюция`, `north star`, `как работает Pith`, `self-analysis` | Архитектурные ответы, стратегическое планирование, допустимый deep self‑analysis |

**Правило:** режим `VISION` включается только по явному сигналу. Он не должен случайно срабатывать в обычной задаче.

---

## 5. Context Assembly by Mode

### 5.1 NORMAL

1. **System / Runtime Policy**
2. **Task / Workflow Intent**
3. **Последние `N` сообщений**
4. **Conversation Summary** — только если история длинная
5. **Top‑M Memory Records**
6. **Task / Workflow / Artifact Context**
7. **Knowledge Context** — только по необходимости или по запросу Planner’а
8. **Trace / Governance Signals** — только если влияют на execution path или autonomy/budget

**Ограничение:** в `NORMAL` режиме Planner не инициирует длинный AGI/self‑analysis без прямого запроса.

### 5.2 DIAGNOSTICS

1. **System / Policy + diagnostics mode block**
2. **Task / Incident Intent**
3. **Последние сообщения**, особенно error logs / stack traces
4. **Summary** — только если относится к предыдущим сбоям
5. **Memory** — только прошлые инциденты того же класса
6. **Artifacts** — логи, конфиги, схемы, failing outputs
7. **Trace / Governance** — последние relevant decisions, runtime_config_version, failure patterns
8. **Knowledge Context** — только если нужен для root cause analysis

**Запреты:**

- нет длинных AGI‑эссе;
- нет расплывчатых roadmap‑ответов вместо root cause / next fix steps;
- нет подмешивания нерелевантной философии Pith.

### 5.3 VISION

1. **System / Policy + `mode=vision`**
2. **Task Intent (vision/meta‑запрос)**
3. **Architectural Summary**
4. **Memory** — только records, относящиеся к `projects.pith.*` и ключевым постмортемам
5. **Artifacts** — `PITH_KERNEL`, `ARCHITECTURE_NORTH_STAR`, `PITH_AGENT_COMPANY`, ADR, roadmaps, docs по OBS/EVAL/GOV/DEPLOYMENT
6. **Trace / Governance Signals** — если нужны для анализа состояния системы и эволюции
7. **Knowledge Context** — repo/docs/архитектурные материалы

**Допустимо:**

- длинные структурированные ответы;
- системный self‑analysis;
- обсуждение roadmap, architecture debt, gaps, future phases.

---

## 6. Priority Rules & Conflict Resolution

При построении контекста RuntimePlanner соблюдает строгий приоритет:

1. `System / Runtime Policy`
2. `Runtime Mode`
3. `Task / Workflow Intent`
4. `Short-Term Conversation`
5. `Conversation Summary`
6. `Memory Records`
7. `Task / Workflow / Artifact Context`
8. `Knowledge Context`
9. `Trace / Governance Signals` как override only when execution‑critical

**При конфликте:**

- system policy сильнее memory;
- mode сильнее старых разговоров;
- текущий запрос сильнее summary;
- memory не имеет права переписывать policy;
- retrieved knowledge не имеет права ломать autonomy/budget constraints.

---

## 7. Self-Reflection Policy

Чтобы не превращаться в “болтливую AGI‑персону”, Pith придерживается правил:

- **Один большой self‑analysis на сессию**, только в `VISION` и только по явному запросу.
- В `NORMAL` и `DIAGNOSTICS` самоанализ ограничен: максимум 2–3 коротких наблюдения, только если это полезно задаче.
- Старые self‑analysis blocks могут учитываться как background, но не становятся директивой к текущему ответу.
- Любая попытка модели развернуть manifesto‑like output в рабочем режиме фиксируется Evaluator’ом как `persona_drift`.

---

## 8. Summary & Memory Update Policy

После значимого шага или завершения задачи:

1. **Summary Update**
   - Краткое резюме сессии обновляется инкрементально.
   - Оно должно быть background‑only, а не скрытым system prompt.

2. **Memory Record Update**
   - Сохраняются только:
     - успешные/провальные задачи,
     - root causes,
     - устойчивые решения,
     - reusable procedures,
     - важные артефакты,
     - lessons learned.
   - Теги: `tenant_id`, `workspace_id`, `task_type`, `risk_level`, `topic`, `source_task`.

3. **Trace / Governance Update**
   - Важные runtime‑шаги фиксируют `Trace`.
   - При необходимости фиксируются `PolicyDecision`, `RuntimeConfig` / `runtime_version`, billable events.

---

## 9. Token Budget & Pruning Rules

Контекст собирается не “целиком”, а под budget.

### 9.1 Budget Order

При нехватке окна context pruning идёт в таком порядке:

1. Урезать `Short-Term Conversation` до релевантного окна.
2. Сжать `Conversation Summary`.
3. Сократить количество `Memory Records`.
4. Оставить только наиболее релевантные `Artifacts`.
5. Отложить `Knowledge Context`, если он не execution‑critical.
6. Никогда не выбрасывать:
   - system/runtime policy,
   - current task/workflow intent,
   - mode block.

### 9.2 Relevance Rules

Каждый memory/artifact/context block должен оцениваться хотя бы по:

- semantic relevance to current task/workflow,
- workspace / tenant match,
- recency,
- trust / importance,
- incident similarity (для diagnostics).

### 9.3 Hard Constraints

- Не подмешивать больше context, чем реально может быть использовано.
- Если retrieval weak/noisy, лучше меньше, но чище.
- Context assembly должен уменьшать entropy, а не увеличивать её.

---

## 10. Mode Detection Rules

`RuntimePlanner` или будущий `ModeDetector` определяет режим на основе:

- keywords,
- intent classification,
- task_type,
- history slice,
- explicit user request.

### Minimal heuristic baseline

- `DIAGNOSTICS`: error‑like markers, bug/fix phrasing, logs, traceback, “не работает”.
- `VISION`: architecture/roadmap/evolution/governance/meta‑analysis requests.
- иначе `NORMAL`.

### Override rules

- Explicit user ask сильнее heuristic.
- Если есть ambiguity между `NORMAL` и `VISION`, предпочитать `NORMAL`.
- Если есть ambiguity между `NORMAL` и `DIAGNOSTICS` и присутствуют реальные error signals, предпочитать `DIAGNOSTICS`.

---

## 11. Implementation Contract

`RuntimePlanner` использует `ContextAssembler` примерно в такой форме:

```python
context = context_assembler.build(
    mode=RuntimeMode.NORMAL | RuntimeMode.DIAGNOSTICS | RuntimeMode.VISION,
    tenant_id=tenant_id,
    workspace_id=workspace_id,
    user_id=user_id,
    task_id=task_id,
    workflow_id=workflow_id,
    autonomy_level=autonomy_level,
    runtime_config_version=runtime_config_version,
    query=user_query,
    recent_history=history_slice,
)
```

### Expected output shape

```python
{
    "system_policy": "...",
    "mode_block": "...",
    "task_intent": "...",
    "recent_history": [...],
    "summary": "...",
    "memory_records": [...],
    "artifacts": [...],
    "knowledge_context": [...],
    "trace_signals": [...],
    "token_estimate": 0,
    "pruning_applied": [...],
}
```

### RuntimePlanner responsibilities

- определить mode;
- установить autonomy_level и runtime_config_version;
- запросить контекст у `ContextAssembler`;
- при необходимости сократить/очистить его;
- передать финальный assembled context в execution path;
- записать trace signal о том, какой context profile был использован.

### ContextAssembler responsibilities

- собрать контекст из state/memory/artifacts/retrieval;
- соблюдать порядок приоритетов;
- не нарушать budget / policy constraints;
- не смешивать нерелевантный background с task‑critical context;
- возвращать структурированный context package, а не один сырой prompt string.

---

## 12. Trace & Observability Alignment

Context assembly само по себе должно быть наблюдаемым.

Минимально фиксируемые сигналы:

- mode chosen,
- autonomy_level,
- runtime_config_version,
- memory blocks count,
- artifact blocks count,
- retrieval used / not used,
- pruning applied / not applied,
- token estimate.

На текущем этапе task‑level observability обеспечивается через **TraceStore v1** (`task_traces` в `episodes.db`). Далее поверх него наращиваются:

- per‑LLM‑call spans,
- per‑agent/department spans,
- evaluator linkage,
- trace query/read surfaces.

---

## 13. Failure & Fallback Behavior

Если один из источников контекста недоступен:

- отсутствие memory не должно ломать task execution;
- отсутствие summary не должно ломать runtime;
- retrieval failure не должен ломать базовый task path;
- planner должен деградировать gracefully к меньшему, но чистому context package.

**Правило:** плохой или шумный context хуже, чем неполный, но надёжный context.

---

## 14. Guarantees of the Protocol

Этот протокол должен обеспечивать:

1. **Task‑focus by default** — обычные задачи не деградируют в meta‑manifesto.
2. **Mode‑aware behavior** — diagnostics и vision реально ведут себя по‑разному.
3. **Policy‑first context** — memory и retrieval не переписывают runtime constraints.
4. **Continuity without overload** — контекст сохраняется, но не превращается в шум.
5. **Governable assembly** — можно объяснить, почему именно такой context был собран.
6. **Graceful degradation** — отсутствие части context sources не ломает весь pipeline.

---

## 15. Non-Goals

Этот протокол **не описывает**:

- конкретный prompt wording для каждой модели;
- формат всех tool contracts;
- полный Memory v2 schema;
- внутреннее устройство repo indexing / web research pipeline;
- policy engine во всей полноте.

Он определяет именно **runtime contract контекстной сборки**, а не всю архитектуру Pith.

---

## 16. One-Line Rule

> **Context in Pith is assembled around work, not around chat.**