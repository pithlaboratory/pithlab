"""Task entity — единица работы."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
import uuid


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str
    query: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    runtime_version_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}