# Pith Deployment Model v1

> Deployment and isolation model for Pith v5 as a runtime-native, continuity-aware, multi-agent operating system.

## 1. Purpose

Pith Deployment Model v1 describes how Pith is intended to run in real environments:

- isolation boundaries,
- workspace and tenant model,
- data flow and retention expectations,
- secrets and configuration boundaries,
- cloud vs self-hosting orientation,
- constraints relevant for enterprise-grade usage.

This is not a detailed infra spec, but a conceptual deployment blueprint that should guide architectural decisions.

---

## 2. Deployment Goals

Pith is designed to be:

- **workspace-native** — everything happens in the context of a workspace,
- **multi-tenant capable** — but with strong isolation,
- **runtime-centric** — one runtime, many agent departments and workflows,
- **deployment-flexible** — cloud-friendly, but not locked into a single shape,
- **enterprise-aware** — able to evolve toward stricter isolation and compliance.

The deployment model must make it realistic to:

- run Pith as a managed cloud service,
- host Pith closer to enterprise data when needed,
- maintain clear separation between tenants/workspaces,
- add stronger controls over time.

---

## 3. Core Deployment Concepts

### 3.1 Tenant

A tenant represents a high-level customer boundary (e.g., a company).

Tenants own workspaces, data, and configuration within their boundary.

### 3.2 Workspace

A workspace is the primary unit of:

- runtime context,
- memory,
- workflows,
- artifacts,
- agent company operations.

Workspaces belong to tenants and must be isolated from each other.

### 3.3 Runtime Instance

A runtime instance is a deployed Pith core:

- orchestrator,
- planner,
- services,
- memory,
- observability,
- governance.

A single runtime instance may serve multiple tenants and workspaces, subject to isolation rules.

### 3.4 Control Plane vs Data Plane

Over time, Pith should conceptually separate:

- **Control Plane** — configuration, policies, tenant/workspace management, billing, centralized observability.
- **Data Plane** — actual runtime execution, memory, and workflows for tenants/workspaces.

v1 does not need a full separation, but should be architected with this evolution in mind.

---

## 4. Deployment Modes (Conceptual)

Pith should be able to support three conceptual deployment modes over time.

### 4.1 Managed Multi-Tenant Cloud

Baseline mode:

- Pith runs as a managed service,
- multiple tenants/workspaces share one or more runtime clusters,
- strict logical isolation and policy boundaries,
- shared infrastructure with per-tenant configuration.

### 4.2 Dedicated Single-Tenant

For higher sensitivity:

- a single tenant has a dedicated Pith deployment,
- workspaces still exist within that tenant,
- infra resources are not shared with other tenants,
- easier compliance and risk posture.

### 4.3 Hybrid / On-Prem Friendly

For enterprises with strong data and security requirements:

- Pith runtime (or parts of it) can run closer to the enterprise environment,
- data stays under enterprise control,
- control plane can be cloud-based or hybrid,
- integration with internal identity and policy systems.

v1 does not need full on-prem readiness, but must avoid design choices that block this path.

---

## 5. Workspace Isolation Model

Pith should treat workspace isolation as:

- a correctness requirement,
- a privacy requirement,
- a governance requirement.

Key aspects:

- workspace_id must be present and enforced in:
  - requests,
  - tasks,
  - traces,
  - memory reads/writes,
  - artifact references,
  - evaluation and observability,
  - billing and reporting.

- cross-workspace access should be disallowed by default,
  unless explicitly designed and governed (e.g., shared knowledge packs).

- logs and traces must be filterable and scoped by workspace.

---

## 6. Data Categories

Pith should conceptually separate data into categories:

- **Runtime State** — ephemeral state for in-flight tasks and workflows.
- **Traces** — structured execution logs, actions, decisions, cost signals.
- **Memory** — workspace-specific context and long-term knowledge.
- **Artifacts** — generated files, documents, reports, code, etc.
- **Configuration** — policies, routing rules, department registry.
- **Secrets** — API keys, credentials, connection configs.
- **Billing & Usage** — cost and usage events.

Each category may have different retention and storage requirements.

---

## 7. Retention & Deletion (Conceptual)

Pith should be able to support:

- configurable retention for traces and memory,
- deletion of workspace data on request,
- potential soft-delete vs hard-delete distinctions,
- compliance-friendly audit exports.

v1 does not need a full retention engine, but:

- must not hard-wire assumptions that “data lives forever,”
- should keep deletion and export in mind when designing data models.

---

## 8. Secrets and External Integrations

Pith will interact with external systems:

- CRMs,
- email providers,
- ad platforms,
- document stores,
- code repositories,
- analytics systems.

Secrets for these integrations should be:

- scoped (by tenant/workspace),
- not persisted in cleartext in traces,
- usable by runtime only within allowed contexts and policies,
- eventually manageable via a proper secret management story.

v1 can use minimal secret storage, but must not leak secrets into:

- logs,
- traces,
- artifacts.

---

## 9. Model / Tool Providers

Pith will likely rely on:

- external LLM providers,
- vector / search systems,
- external tools/APIs.

Deployment model considerations:

- model/tool selection may vary by tenant/workspace,
- cost attribution must respect tenant/workspace boundaries,
- model and tool usage must be observable and governable,
- fallback and routing decisions must be traceable.

---

## 10. Network and Security (Conceptual)

Pith’s deployment model should be compatible with:

- API entrypoints secured by authentication/authorization,
- rate limiting and abuse protection,
- internal network separation for critical components,
- eventual VPC/peering and IP allowlists for enterprise.

v1 may run in a simpler environment, but:

- should keep components modular enough to later separate internal from external surfaces,
- should not tightly couple everything into a monolithic service that is impossible to segment.

---

## 11. Operator and Admin Surfaces

Deployment model implies the need for at least:

- an operator/admin view (even if via CLI or simple UI),
- workspace and tenant management flows,
- configuration and policy management,
- observability dashboards,
- incident and postmortem tooling hooks.

These do not need to be fully built for v1, but should be anticipated.

---

## 12. Deployment Constraints

Design constraints implied by this model:

- avoid hard-coded assumptions that only one tenant/workspace exists,
- avoid embedding tenant-specific logic deep into core runtime,
- keep workspace/tenant IDs as first-class parameters at service boundaries,
- avoid storing cross-tenant data in shared, unpartitioned structures,
- keep logs/traces partitionable and filterable by workspace/tenant.

---

## 13. v1 Deployment Priorities

For Pith Deployment Model v1, focus on:

1. clear workspace_id handling and enforcement,
2. data category separation in models and interfaces,
3. safe handling of secrets and sensitive payloads,
4. simple but meaningful retention expectations,
5. tenant/workspace-awareness in traces and billing events,
6. modularity sufficient to evolve into multi-tenant and dedicated deployments.

---

## 14. Out of Scope for v1

Not required immediately:

- full multi-region routing,
- cross-region data replication strategies,
- complete zero-trust networking,
- deep enterprise IAM integration,
- detailed compliance mapping.

These can be added when Pith grows into stricter enterprise environments.

---

## 15. Integration Points

This document should influence:

- `PITH_ACTIVE_CONTEXT.md`
- `docs/PITH_OBSERVABILITY_V1.md`
- `docs/PITH_EVALUATION_V1.md`
- `docs/PITH_GOVERNANCE_V1.md`
- `docs/PITH_RUNTIME_CONTEXT_PROTOCOL_V1.md`
- memory and storage design,
- tool/secret handling,
- billing and usage event models.

Pith should not scale into heavier enterprise usage or Agent Company operations without a deployment model that respects isolation, data categories, and realistic hosting constraints.
