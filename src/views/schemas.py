from datetime import datetime
from pydantic import BaseModel, Field

from src.db.models import TaskStatus


class TaskCreateRequest(BaseModel):
    payload: str = Field(..., min_length=1, description="Task payload")


class TaskCreateResponse(BaseModel):
    task_id: int = Field(..., description="ID of created task")


class TaskResponse(BaseModel):
    id: int
    payload: str
    status: TaskStatus
    result: str | None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
