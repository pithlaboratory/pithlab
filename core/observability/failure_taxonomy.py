from enum import Enum

class FailureClass(str, Enum):
    ROUTING_FAILURE = "routing_failure"
    PLANNER_FAILURE = "planner_failure"
    ORCHESTRATOR_FAILURE = "orchestrator_failure"
    TOOL_FAILURE = "tool_failure"
    MEMORY_FAILURE = "memory_failure"
    POLICY_FAILURE = "policy_failure"
    APPROVAL_TIMEOUT = "approval_timeout"
    ARTIFACT_FAILURE = "artifact_failure"
    QUALITY_FAILURE = "quality_failure"
    COST_GUARDRAIL = "cost_guardrail_violation"
    UNKNOWN_FAILURE = "unknown_failure"