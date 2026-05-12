from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class TaskState(str, Enum):
    created = "created"
    queued = "queued"
    context_assembling = "context_assembling"
    planned = "planned"
    executing = "executing"
    evaluating = "evaluating"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class WorkspaceStatus(str, Enum):
    active = "active"
    archived = "archived"
    deleted = "deleted"


class ArtifactType(str, Enum):
    text = "text"
    summary = "summary"
    report = "report"
    code_patch = "code_patch"
    file = "file"
    decision = "decision"
    plan = "plan"
    dataset = "dataset"
    log = "log"


class TraceStepStatus(str, Enum):
    started = "started"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


class WorkspaceRecord(BaseModel):
    workspace_id: str = Field(default_factory=lambda: new_id("ws"))
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    tenant_id: Optional[str] = None
    status: WorkspaceStatus = WorkspaceStatus.active
    domain_type: Optional[str] = None
    default_policy_id: Optional[str] = None
    default_model_profile: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskRecord(BaseModel):
    task_id: str = Field(default_factory=lambda: new_id("task"))
    workspace_id: str
    owner_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    trace_id: Optional[str] = None

    source_interface: Literal["telegram", "api", "dashboard", "cli", "system"] = "telegram"
    input_text: str
    intent_type: Optional[str] = None
    priority: int = 5

    status: TaskState = TaskState.created

    runtime_version: Optional[str] = None
    model_lane: Optional[str] = None
    model_id: Optional[str] = None

    cost_usd: float = 0.0
    latency_ms: Optional[int] = None

    error_message: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ArtifactRecord(BaseModel):
    artifact_id: str = Field(default_factory=lambda: new_id("art"))
    task_id: str
    workspace_id: str

    artifact_type: ArtifactType
    title: str

    content_text: Optional[str] = None
    content_ref: Optional[str] = None
    mime_type: Optional[str] = None

    version: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class TraceRecord(BaseModel):
    trace_id: str = Field(default_factory=lambda: new_id("trace"))
    task_id: str
    workspace_id: str

    step_name: str
    step_order: int = 0
    status: TraceStepStatus = TraceStepStatus.started

    model_id: Optional[str] = None
    tool_name: Optional[str] = None

    cost_usd: float = 0.0
    latency_ms: Optional[int] = None

    input_ref: Optional[str] = None
    output_ref: Optional[str] = None
    error_ref: Optional[str] = None

    metadata: dict[str, Any] = Field(default_factory=dict)

    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None