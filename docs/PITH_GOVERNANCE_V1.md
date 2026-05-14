# Pith Governance v1

> Governance architecture for Pith v5 as a runtime-native, continuity-aware, multi-agent operating system.

---

## 1. Purpose

Pith Governance v1 defines how Pith controls authority, approvals, action boundaries, policy enforcement, and accountability.

Governance in Pith is not a legal appendix.
It is an execution control layer that determines:

- what the system is allowed to do,
- what requires approval,
- what must be denied,
- what must be logged,
- what must remain reversible,
- what level of autonomy is appropriate for each workflow.

This document exists because agent capability without governance becomes unsafe, untrustworthy, and commercially fragile.[web:2104][web:2107]

Governance is implemented as a **runtime control plane** — policies are enforced before and during execution, not only at design time.

---

## 2. Why Governance Is First-Class

Pith is evolving toward:

- a workspace-native runtime,
- an Agent Company OS,
- a governed execution environment,
- a monetizable multi-agent system.

In this context, the main production question is not only:
**“Can the system do this?”**

It is also:
**“Should the system be allowed to do this now, in this context, at this autonomy level, under these constraints?”**[web:2104][web:2109]

Governance is therefore part of runtime architecture, not an external compliance wrapper.

---

## 3. Governance Principles

### 3.1 Policy before dispatch

A workflow or action should be evaluated against policy **before** execution, not only after the fact.[web:2113]

Policy checks must intercept high‑impact actions (tool calls, sends, publishes, mutations, spend) at runtime.

### 3.2 Explicit authority boundaries

Each workflow, department, tool, and action type must operate within declared authority.
Authority is a function of:

- actor (user/agent/department),
- autonomy tier,
- action class,
- context (tenant/workspace, data sensitivity).

### 3.3 Risk-tiered autonomy

Not all actions deserve the same level of autonomy.
Higher-risk actions require stronger controls and higher‑tier approvals.[web:2108][web:2111]

### 3.4 Human oversight where needed

Human approval is not a weakness.
It is a mechanism for scaling safely and for satisfying regulatory and business risk constraints.

### 3.5 Auditability by default

Every important decision and action should be reconstructible from traces and governance records with clear decision lineage.[web:2108][web:2112]

### 3.6 Reversibility awareness

If an action is irreversible or high-blast-radius, governance must treat it differently from low-risk drafting work:

- stricter policies,
- more approvals,
- canary and rollback where possible.

### 3.7 Workspace and tenant safety

Governance must preserve workspace boundaries and prevent cross-tenant misuse.

No agent or department should be able to bypass tenant/workspace isolation or policy engine via “hidden tools” or direct integrations.

---

## 4. Governance Layers

Pith Governance should operate across five layers.

### 4.1 Decision Governance

Controls planner/orchestrator choices such as:

- allowed runtime modes,
- allowed autonomy level,
- department eligibility,
- route restrictions,
- confidence/risk thresholds for automatic decisions.[web:2112]

### 4.2 Context Governance

Controls what memory, artifacts, and context can be accessed:

- workspace scoping,
- role-based context visibility,
- sensitive data restrictions,
- retrieval boundaries.

### 4.3 Action Governance

Controls whether a proposed action may execute:

- tool usage permissions,
- budget caps,
- publish/send/mutate/delete restrictions,
- spending thresholds,
- escalation triggers.

Policy engine should sit **before** external side effects (APIs, sends, writes) and return explicit outcomes.

### 4.4 Output Governance

Controls what may be emitted externally:

- public communication,
- customer-facing content,
- regulated outputs,
- sensitive summaries,
- export behavior (reports, logs).

### 4.5 Audit & Accountability Governance

Controls:

- logging requirements,
- ownership tracking,
- approval records,
- policy evidence,
- postmortem compatibility.

Audit artifacts should be compatible with external regulatory/audit expectations (decision lineage, timestamps, actors).[web:2108]

---

## 5. Governance Outcomes

Every action or workflow policy check should produce one of a small set of outcomes:

- `allow`
- `allow_with_constraints`
- `require_approval`
- `deny`
- `escalate`

These outcomes should be explicit, inspectable, and logged with rule/policy identifiers.[web:2110][web:2113]

### 5.1 allow

The action is permitted without additional gates.

### 5.2 allow_with_constraints

The action is allowed, but only with enforced limits.

Examples:

- read-only mode,
- cost cap,
- depth limit,
- restricted tool subset,
- draft-only output.

### 5.3 require_approval

A human gate is required before dispatch or completion.
Governance must record who approved, under what policy snapshot, and with what justification.

### 5.4 deny

The action is blocked.
Denials should be explicit, explainable, and auditable.[web:2110]

### 5.5 escalate

The action is too ambiguous, high-risk, or policy-sensitive for normal routing and should move to a higher-trust human/operator path (e.g. security, compliance, executive).

---

## 6. Action Classes

Pith should classify actions into stable categories because governance becomes clearer when actions are typed.[web:2113]

Suggested action classes:

- `read`
- `retrieve`
- `analyze`
- `draft`
- `recommend`
- `write_internal`
- `write_external`
- `send`
- `publish`
- `mutate_system`
- `spend_money`
- `change_access`
- `delete`
- `export_sensitive`

These categories are more important than specific tool names.
Tool governance should map tools and endpoints to action classes.

---

## 7. Autonomy Tiers

Pith should define stable autonomy tiers (aligned with Kernel autonomy levels).

### 7.1 Tier 0 — Advisory

The system can analyze, summarize, recommend, and draft.
No external action (`read` / `analyze` / `draft` / `recommend` only).

### 7.2 Tier 1 — Assisted Execution

The system may prepare actions and perform low-risk internal actions.
Human review is expected for important outcomes, especially `send`, `publish`, `spend_money`, `mutate_system`.

### 7.3 Tier 2 — Supervised Autonomy

The system may execute pre-approved workflow segments under constraints.
Critical actions still require human approval or escalation.

### 7.4 Tier 3 — Operational Autonomy

The system may perform bounded operational actions autonomously under strong policy, observability, and evaluation controls.[web:2111]

### 7.5 Tier 4 — High-Autonomy Restricted

Only for highly controlled, proven workflows with explicit governance, evaluation, and rollback confidence.

Pith v1 should mostly target Tier 0–2.
Tier 3 should be selective.
Tier 4 should be exceptional and require explicit executive‑level risk acceptance.[web:2111]

---

## 8. Approval Matrix

Pith should maintain a human approval matrix tied to action class and blast radius.

### Typical approval-required actions

These usually require approval:

- customer-facing `send` actions,
- public `publish` actions,
- pricing or offer commitments,
- CRM mutations with business consequences,
- permission changes (`change_access`),
- production-impacting `mutate_system` actions,
- `spend_money` above budget thresholds,
- regulated or sensitive data export (`export_sensitive`),
- irreversible `delete` operations.

### Typical allow-with-constraints actions

These may be allowed with limits:

- internal drafting,
- internal analysis,
- low-risk research,
- read-only retrieval,
- creating artifacts in sandboxed spaces.

The approval matrix should eventually exist as executable policy (policy engine / config), not only as prose.[web:2107][web:2109]

---

## 9. Governance Objects

Governance should evaluate several object types:

### 9.1 Workflow

Examples:

- what department flow is permitted,
- which autonomy tier is allowed,
- whether budget limits apply,
- whether additional approvals are required.

### 9.2 Action

Examples:

- whether `send`/`publish`/`delete` is admissible,
- whether a specific tool can be used now,
- whether approval is required.

### 9.3 Context Access

Examples:

- whether this agent can read this memory,
- whether this workspace boundary is enforced,
- whether sensitive documents can be included.

### 9.4 Output

Examples:

- whether content can be shown externally,
- whether the artifact contains restricted data,
- whether a report requires human review.

---

## 10. Policy Dimensions

Pith policies should eventually cover at least these dimensions:

- workspace / tenant boundary,
- role / actor identity,
- action class,
- department,
- autonomy tier,
- budget / spend,
- data sensitivity,
- tool permissions,
- destination / recipient,
- reversibility,
- business criticality,
- compliance/risk category.

This should become a formal policy vocabulary over time and be enforced by a runtime policy engine.[web:2107][web:2109]

---

## 11. Governance and Observability

Governance depends on observability.

Every important governance decision should be traceable through:

- `trace_id`
- `tenant_id`
- `workspace_id`
- `task_id`
- `workflow_id`
- policy outcome (`allow` / `deny` / `require_approval` / `allow_with_constraints` / `escalate`)
- approval state and approver
- acting department / agent
- action class
- budget state
- final dispatch result

If a workflow cannot explain why an action was allowed, denied, or escalated, governance is weak.[web:2108][web:2112]

---

## 12. Governance and Evaluation

Governance should also be measured.

Examples of governance evaluation signals:

- approval frequency,
- denial rate,
- policy violation attempts,
- action class distribution,
- autonomy tier distribution,
- high-risk workflow completion rate,
- false-positive approvals (over‑blocking),
- false-negative approvals (under‑blocking),
- operator correction after approval.

This matters because governance that is too weak is dangerous, and governance that is too noisy becomes unusable.[web:2106][web:2109]

---

## 13. Governance and Agent Company

Because Pith is becoming an Agent Company OS, governance must operate across departments.[web:2108][web:2112]

Examples:

- Sales agents may draft outreach, but sending customer-facing sequences may require approval.
- Marketing agents may generate campaigns, but publishing externally may require review.
- Research agents may collect and synthesize information, but external distribution of sensitive reports may be gated.
- Delivery agents may build artifacts, but production release or external dispatch may require higher trust.
- Support/Ops agents may resolve low-risk tickets autonomously, but escalations or financial adjustments may require approvals.

Governance must understand business operations, not only technical actions.

---

## 14. Minimum v1 Controls

Pith Governance v1 should start with these minimum controls:

1. Action classification.
2. Autonomy tiers (Tier 0–2 in active use).
3. Approval-required action list.
4. Deny-list for prohibited actions.
5. Allow-with-constraints mode.
6. Budget / spend ceilings per workspace/tenant.
7. Workspace-scoped access control.
8. Audit logging for all gated actions.

This is enough to begin safely without pretending to have perfect governance.[web:2107][web:2113]

---

## 15. Out of Scope for v1

Not required immediately:

- full regulatory mapping for every jurisdiction,
- advanced policy DSL,
- complete formal verification,
- full adaptive risk engine,
- universal enterprise IAM integration.

The v1 goal is **practical runtime governance**, not governance maximalism.

---

## 16. Next Integration Points

This document should influence:

- `docs/PITH_OBSERVABILITY_V1.md`
- `docs/PITH_EVALUATION_V1.md`
- `docs/PITH_AGENT_COMPANY_V1.md`
- `PITH_ACTIVE_CONTEXT.md`
- planner/orchestrator routing logic
- tool registry contracts
- execution result schemas
- future approval queue / operator console

Pith should not increase autonomy, expand monetized workflows, or expose high-impact tools without governance that is explicit, inspectable, and enforceable.[web:2107][web:2108][web:2111]