# PITH_SYSTEM_MAP_V1

## Purpose

This document defines the minimal runtime system map for Pith v5.2.
It is intended for internal observability, dashboard integration, and architectural alignment.

## System Map

```mermaid
flowchart TD
    U[User]
    TG[Telegram Interface]
    API[Future REST API]
    UI[Future Dashboard UI]

    RP[RuntimePlanner]
    GOV[Governance Guards]
    ROUTER[Model Router / Provider Layer]

    TASK[TaskService]
    ART[ArtifactService]
    MEM[MemoryManager]

    TRACE[TraceService]
    EVAL[Evaluation / PithEval]
    TRACES[(output/traces)]
    EVALRUNS[(output/eval_runs)]

    U --> TG
    U -.-> UI
    U -.-> API

    TG --> GOV
    GOV --> RP
    API --> RP
    UI --> RP

    RP --> TASK
    RP --> ART
    RP --> MEM
    RP --> ROUTER

    RP --> TRACE
    RP --> EVAL

    TRACE --> TRACES
    EVAL --> EVALRUNS

    TASK --> TRACE
    ART --> TRACE
    MEM --> TRACE
```

## Request Flow

```mermaid
sequenceDiagram
    participant User
    participant Interface
    participant Governance
    participant Planner
    participant Services
    participant Trace
    participant Eval

    User->>Interface: Send task / request
    Interface->>Governance: Pre-check risky requests
    Governance-->>Interface: Refusal or allow
    Interface->>Planner: Forward valid request
    Planner->>Services: Use memory / tasks / artifacts / router
    Services-->>Planner: Context + execution results
    Planner-->>Interface: Final response
    Planner->>Trace: Record trace event(s)
    Planner->>Eval: Record evaluation data
```

## Notes

- Telegram is the current primary interface, but not the final product surface.
- Dashboard UI and REST API are future interfaces over the same runtime core.
- Governance is enforced before risky execution paths.
- Trace and Evaluation form the observability spine of the system.
- `output/traces` and `output/eval_runs` are the current local evidence stores.