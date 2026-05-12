# Pith ADR Index

Этот файл — входная точка в архитектурные решения Pith.  
Если есть конфликт между кодом и ADR/доктриной, приоритет у ADR и canonical docs.

---

## Canonical documents

### Core architecture & runtime

| File | Role | Status |
| --- | --- | --- |
| `docs/PITH_ARCHITECTURE_NORTH_STAR_V2.md` | Архитектурный North Star Pith v5: целевое состояние системы, границы, принципы эволюции | ACTIVE |
| `docs/PITH_KERNEL.md` | Canonical kernel contract (ADR-Kernel-001): уровни автономии, гарантии, safety rails, runtime-axioms | ACTIVE |
| `docs/PITH_MASTER_PLAN.md` | Master plan v5.1: эволюция продукта и runtime, фазы внедрения, vNext framing | ACTIVE |
| `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md` | Runtime context protocol: источники контекста, порядок сборки, режимы NORMAL / DIAGNOSTICS / VISION | ACTIVE |
| `docs/RUNTIME_CONTEXT_PROTOCOL_V1.md` | Старое имя runtime context протокола, оставлено как совместимый redirect на PITH\_* версию | DEPRECATED |
| `docs/RUNTIME_REFACTOR_CHECKLIST_V1.md` | Практический чеклист для стабилизации и рефакторинга runtime-слоя (Phase 1–2 roadmap) | ACTIVE |

### Product / identity

| File | Role | Status |
| --- | --- | --- |
| `docs/MANIFESTO.md` | Высокоуровневое видение Pith, зачем система существует и какой тип работы она должна уметь держать | ACTIVE |
| `docs/PRODUCT_DOCTRINE.md` | Product doctrine: ценности, принципы продукта, trade-offs, anti-goals, UX-скрепы | ACTIVE |
| `docs/AGI_POSITION.md` | Позиция Pith относительно AGI: scope, границы ответственности, отношение к “общему” интеллектy | ACTIVE |
| `docs/IDENTITY.md` | Детализация identity / persona Pith, голос, стиль взаимодействия | ACTIVE |

### Evolution / roadmap

| File | Role | Status |
| --- | --- | --- |
| `docs/IMPLEMENTATION_ROADMAP_V1.md` | Implementation roadmap v1: фазы внедрения, Phase 1–2 (runtime стабилизация), Phase 3+ | ACTIVE |
| `docs/EVOLUTION.md` | Долгосрочная эволюция Pith: направления развития, Memory v2, TraceStore vNext, provider-agnostic routing | ACTIVE |
| `docs/ROADMAP_6M.md` | Среднесрочный (6M) roadmap, выровненный с Master Plan и Implementation Roadmap | ACTIVE |
| `docs/PITH_EXEC_PLAN_WEEKS_1_6.md` | Детализированный execution plan на первые 6 недель (итеративное приближение к Master Plan) | ACTIVE |

### Glossary / onboarding

| File | Role | Status |
| --- | --- | --- |
| `docs/GLOSSARY.md` | Глоссарий терминов Pith (runtime entities, services, roles), используется в онбординге | ACTIVE |
| `docs/ADR_INDEX.md` | Этот файл. Входная точка в ADR и canonical docs | ACTIVE |

### Working runtime context

| File | Role | Status |
| --- | --- | --- |
| `PITH_DEV_CONTEXT.md` | Dev-context для ассистентов и runtime: текущий stack, провайдеры, флаги, активные куски системы | ACTIVE |
| `PITH_CHANGELOG.md` | История значимых изменений системы, привязка фич/рефакторинга к датам и ADR | ACTIVE |
| `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md` | (см. выше, core runtime) | ACTIVE |

---

## ADRs

### ADR-Kernel-001

**File:** `docs/PITH_KERNEL.md`  
**Status:** Accepted  
**Purpose:** Identity, operating model, guarantees, layers, event-driven loop, autonomy boundaries.

*(Новые существенные ADR сюда добавляются по мере принятия, с указанием id, файла, статуса и краткого описания.)*

---

## Reading order for assistants

1. `docs/MANIFESTO.md`
2. `docs/PRODUCT_DOCTRINE.md`
3. `docs/AGI_POSITION.md`
4. `docs/PITH_ARCHITECTURE_NORTH_STAR_V2.md`
5. `docs/PITH_MASTER_PLAN.md`
6. `docs/PITH_KERNEL.md`
7. `docs/EVOLUTION.md`
8. `docs/IMPLEMENTATION_ROADMAP_V1.md`
9. `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
10. `PITH_DEV_CONTEXT.md`
11. `PITH_CHANGELOG.md`
12. `docs/GLOSSARY.md` (по мере необходимости)

---

## Rules

- Любое изменение identity, operating loop, guarantees, autonomy model или system layers требует ADR update.
- Любое нетривиальное изменение runtime должно быть отражено в `PITH_CHANGELOG.md`.
- Если naming в коде расходится с canonical docs, фиксируем это как tech debt или отдельный ADR.
- Если новый документ фактически становится canonical (например, новый North Star, новый Kernel ADR), он должен быть явно добавлен в этот индекс.
- Если документ переводится в состояние `DEPRECATED` или `SUPERSEDED`, статус должен быть обновлён как в самом файле, так и в этой таблице.