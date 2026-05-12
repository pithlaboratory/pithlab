# Pith ADR Index

Этот файл — входная точка в архитектурные решения Pith.  
Если есть конфликт между кодом и ADR/доктриной, приоритет у ADR и canonical docs.

---

## Canonical documents

### Product / identity

- `docs/MANIFESTO.md`
- `docs/PRODUCT_DOCTRINE.md`
- `docs/PITH_ARCHITECTURE_NORTH_STAR_V2.md`
- `docs/PITH_KERNEL.md`
- `docs/PITH_MASTER_PLAN.md`

### Delivery / planning

- `docs/IMPLEMENTATION_ROADMAP_V1.md`  *(если файл ещё не заведён — указать как TODO)*
- `docs/GLOSSARY.md`  *(если используется в онбординге)*

### Working runtime context

- `PITH_DEV_CONTEXT.md`
- `PITH_CHANGELOG.md`
- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`

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
3. `docs/PITH_ARCHITECTURE_NORTH_STAR_V2.md`
4. `docs/PITH_MASTER_PLAN.md`
5. `docs/PITH_KERNEL.md`
6. `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
7. `PITH_DEV_CONTEXT.md`
8. `PITH_CHANGELOG.md`

---

## Rules

- Любое изменение identity, operating loop, guarantees, autonomy model или system layers требует ADR update.
- Любое нетривиальное изменение runtime должно быть отражено в `PITH_CHANGELOG.md`.
- Если naming в коде расходится с canonical docs, фиксируем это как tech debt или отдельный ADR.
- Если новый документ фактически становится canonical (например, новый North Star, новый Kernel ADR), он должен быть добавлен сюда явно.
