# PITH_DOCS_INDEX

Status: ACTIVE / CANONICAL INDEX  
Role: entry point and document map for Pith v5.x  
Audience: developers, operators, reviewers, AI assistants

---

## 1. What this file is

This file is the **documentation map** for Pith.

It does not replace the core specs.
It exists to answer three questions quickly:

1. What documents are canonical?
2. What is the current active phase?
3. What should be read first for a given task?

Use this file as the first entry point before opening deeper docs.

---

## 2. Current project state

Pith is a **workspace-native continuity runtime** for long-running cognitive and operational work.

Current practical focus:
- runtime stabilization,
- observability and evaluation v1,
- governance baseline,
- Support/Ops Desk as the first product wedge.

Current phase:
- Runtime stabilization + Observability/Eval v1 + Support/Ops Desk wedge.

This means:
- runtime integrity matters more than feature expansion;
- traceability matters more than stylistic polish;
- governed execution matters more than autonomy growth;
- Support/Ops Desk matters more than broad Agent Company expansion.

---

## 3. Reading order

If you are new to the repo, read in this order:

1. `PITH_ACTIVE_CONTEXT.md`
2. `PITH_DEV_CONTEXT.md`
3. `docs/PITH_MASTER_PLAN.md`
4. `docs/PITH_KERNEL.md`
5. `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
6. `docs/PITH_OBSERVABILITY_V1.md`
7. `docs/PITH_EVALUATION_V1.md`
8. `docs/PITH_GOVERNANCE_V1.md`

If you are working on runtime behavior, also read:
- `docs/PITH_RUNTIME_CONTEXT_REVIEW_2026-05-14.md`
- `docs/PITH_SAFE_TOOL_RUNTIME_POLICY_V1.md`

If you are working on operators / HITL / runtime controls, also read:
- `docs/PITH_OPERATOR_CONSOLE_V1.md`

If you are working on memory / context retrieval, also read:
- `docs/PITH_MEMORY_V2_DESIGN.md`
- `docs/PITH_MEMORY_API_V1.md`

---

## 4. Canonical documents

These documents define the current source of truth for Pith v5.x.

| Document | Status | Role |
|---|---|---|
| `docs/PITH_MASTER_PLAN.md` | Canonical | Main product + architecture + governance + roadmap document |
| `docs/PITH_KERNEL.md` | Canonical | Kernel contract and runtime identity |
| `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md` | Canonical | Context assembly, priorities, pruning, runtime modes |
| `docs/PITH_OBSERVABILITY_V1.md` | Canonical | TraceStore, traces, metrics, observability baseline |
| `docs/PITH_EVALUATION_V1.md` | Canonical | EvaluationRecord, eval architecture, quality measurement |
| `docs/PITH_GOVERNANCE_V1.md` | Canonical | Autonomy envelope, governance baseline |
| `docs/PITH_DEPLOYMENT_MODEL_V1.md` | Canonical | Deployment/runtime environment model |
| `docs/PITH_MEMORY_V2_DESIGN.md` | Canonical | Memory v2 architecture and behavior |
| `docs/PITH_MEMORY_API_V1.md` | Canonical | Memory v2 read/write API (ContextRetriever, MemoryManager) |

Rule:
- if implementation conflicts with canonical docs, call it out explicitly;
- do not assume docs are automatically correct;
- do not silently resolve divergence without marking it.

---

## 5. Active operational documents

These documents define the **current working phase** and near-term execution priorities.

| Document | Status | Role |
|---|---|---|
| `PITH_ACTIVE_CONTEXT.md` | Active | Current phase, focus, priorities, invariants |
| `PITH_DEV_CONTEXT.md` | Active | Developer operating context and safe change workflow |
| `PITH_CHANGELOG.md` | Active | Human-readable history of meaningful changes |
| `docs/ROADMAP_6M.md` | Active | 6-month capability roadmap for continuity/evolution runtime |
| `TODO` / engineering backlog doc | Active | Short-term 2–4 week execution backlog |

These files should stay aligned with the canonical layer above.

---

## 6. Product and identity documents

These documents explain what Pith is and how it should be framed.

| Document | Status | Role |
|---|---|---|
| `docs/PITH_SYSTEM_VISION.md` | Active | Product/system vision |
| `docs/PRODUCT_DOCTRINE.md` | Reference | Product identity and framing |
| `docs/MANIFESTO.md` | Reference | Foundational narrative / philosophy |
| `docs/AGI_POSITION.md` | Reference | Explicit boundaries against AGI-myth framing |
| `docs/GLOSSARY.md` | Reference | Terms and definitions |

These docs help with alignment, but they do not replace runtime contracts.

---

## 7. Runtime extension and governance documents

These documents extend the runtime contract into operational control.

| Document | Status | Role |
|---|---|---|
| `docs/PITH_SAFE_TOOL_RUNTIME_POLICY_V1.md` | Active | Tool runtime policy, scopes, sandboxing, deny-by-default |
| `docs/PITH_OPERATOR_CONSOLE_V1.md` | Active | Operator console / approval queue / runtime control surface |
| `docs/PITH_RUNTIME_GOVERNANCE_V1.md` | Active | Governance decision flow and runtime policy enforcement |
| `docs/PITH_RUNTIME_CONTEXT_REVIEW_2026-05-14.md` | Active | Runtime hardening audit and patch plan |
| `docs/observability-smoke-checklist.md` | Active | Deploy / smoke / operational validation checklist |

---

## 8. Agent Company and future-layer documents

These documents describe upper layers of Pith, but should not override current runtime priorities.

| Document | Status | Role |
|---|---|---|
| `docs/PITH_AGENT_COMPANY_V1.md` | Secondary | Agent Company OS blueprint |
| `docs/PITH_CAPABILITIES_MODEL.md` | Secondary | Capability model and system abilities |
| `docs/PITH_OPERATING_STANDARD.md` | Secondary | Operating standard / expected discipline |

Interpretation rule:
- these docs describe the direction of the platform,
- they do not justify breaking runtime discipline in the current phase.

---

## 9. Environment and deployment notes

These documents are environment-specific or operations-specific.

| Document | Status | Role |
|---|---|---|
| `PITH v5 Environment` | Active | VM-specific environment note for `msk-1-vm-ngf0` |
| systemd unit files / deploy notes | Active | Runtime process and deployment operations |

These files are operational references, not architecture definitions.

---

## 10. Legacy and deprecated documents

Legacy files may contain useful history, but should not be used as current architectural truth.

Examples:
- deprecated runtime context stubs,
- old persona-centric memory files,
- superseded drafts.

Rule:
- mark legacy files explicitly with `DEPRECATED` or move them to `archive/`;
- add a pointer to the canonical replacement;
- do not include legacy files in assistant default context.

---

## 11. Update discipline

When a meaningful change happens:

1. Update code.
2. Update the relevant canonical or active doc.
3. Add a factual record to `PITH_CHANGELOG.md`.
4. If the change affects current priorities, update `PITH_ACTIVE_CONTEXT.md`.
5. If the change affects developer workflow, update `PITH_DEV_CONTEXT.md`.
6. If the change alters architecture or product direction, update `docs/PITH_MASTER_PLAN.md` and/or ADR notes.

---

## 12. Practical routing

Use this section as a quick router.

### If changing runtime behavior
Read:
- `docs/PITH_KERNEL.md`
- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
- `docs/PITH_OBSERVABILITY_V1.md`
- `docs/PITH_EVALUATION_V1.md`
- `docs/PITH_GOVERNANCE_V1.md`

### If changing tracing / observability
Read:
- `docs/PITH_OBSERVABILITY_V1.md`
- `PITH_CHANGELOG.md`
- `PITH_ACTIVE_CONTEXT.md`

### If changing Telegram / live interface behavior
Read:
- `PITH_ACTIVE_CONTEXT.md`
- `PITH_DEV_CONTEXT.md`
- `docs/PITH_GOVERNANCE_V1.md`
- `docs/PITH_SAFE_TOOL_RUNTIME_POLICY_V1.md`

### If changing memory / context retrieval
Read:
- `docs/PITH_MEMORY_V2_DESIGN.md`
- `docs/PITH_MEMORY_API_V1.md`
- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`

### If changing product direction or priorities
Read:
- `docs/PITH_MASTER_PLAN.md`
- `docs/PITH_SYSTEM_VISION.md`
- `docs/ROADMAP_6M.md`
- `PITH_ACTIVE_CONTEXT.md`

### If reviewing whether something is in scope now
Read:
- `PITH_ACTIVE_CONTEXT.md`
- `PITH_DEV_CONTEXT.md`
- current engineering TODO/backlog

---

## 13. Default rule

When in doubt:

- trust the canonical runtime docs over narrative docs;
- trust the active-context docs over old plans;
- trust the current phase over attractive future ideas;
- prefer small safe progress over broad redesign.

Pith is built as a governed continuity runtime first.
Everything else is layered on top of that.

---

*Last updated: 2026-06-02 · Pith Lab · Internal / Working document*