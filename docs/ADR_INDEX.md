# Pith ADR Index

Этот файл — входная точка в архитектурные решения Pith.  
Если есть конфликт между кодом и ADR/доктриной, приоритет у ADR и canonical docs.

---

## Canonical documents

### Product / identity
- `docs/MANIFESTO.md`
- `docs/PRODUCTDOCTRINE.md`
- `docs/ARCHITECTURENORTHSTAR.md`
- `docs/PITH_KERNEL.md`

### Delivery / planning
- `docs/IMPLEMENTATIONROADMAPV1.md`
- `docs/GLOSSARY.md`

### Working runtime context
- `.PITHDEVCONTEXT.md`
- `.PITHCHANGELOG.md`

---

## ADRs

### ADR-Kernel-001
**File:** `docs/PITH_KERNEL.md`  
**Status:** Accepted  
**Purpose:** Identity, operating model, guarantees, layers, event-driven loop, autonomy boundaries.

---

## Reading order for assistants

1. `docs/MANIFESTO.md`
2. `docs/PRODUCTDOCTRINE.md`
3. `docs/ARCHITECTURENORTHSTAR.md`
4. `docs/PITH_KERNEL.md`
5. `docs/IMPLEMENTATIONROADMAPV1.md`
6. `.PITHDEVCONTEXT.md`
7. `.PITHCHANGELOG.md`

---

## Rules

- Любое изменение identity, operating loop, guarantees, autonomy model или system layers требует ADR update.
- Любое нетривиальное изменение runtime должно быть отражено в `.PITHCHANGELOG.md`.
- Если naming в коде расходится с canonical docs, фиксируем это как tech debt или отдельный ADR.