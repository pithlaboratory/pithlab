"""Artifact entity — результат задачи."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
import uuid


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    workspace_id: str
    artifact_type: Literal["response", "file", "patch", "summary"]
    content: Optional[str] = None
    file_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}