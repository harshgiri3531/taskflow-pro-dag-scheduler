from pydantic import BaseModel, Field
from typing import Optional, List


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    duration: float = Field(1.0, gt=0)
    column: str = "Backlog"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[float] = None
    column: Optional[str] = None


class TaskOut(BaseModel):
    id: str
    title: str
    description: str
    duration: float
    column: str

    class Config:
        from_attributes = True


class DependencyCreate(BaseModel):
    predecessor_id: str
    successor_id: str


class DependencyOut(BaseModel):
    id: str
    predecessor_id: str
    successor_id: str
    source: str

    class Config:
        from_attributes = True


class ScheduledTaskOut(BaseModel):
    id: str
    title: str
    description: str
    duration: float
    column: str
    earliest_start: float
    earliest_finish: float
    slack: float
    is_critical: bool
    is_blocked: bool


class WorkflowOut(BaseModel):
    tasks: List[ScheduledTaskOut]
    dependencies: List[DependencyOut]


class SuggestionOut(BaseModel):
    id: str
    predecessor_id: str
    successor_id: str
    reason: str
    confidence: float
    status: str

    class Config:
        from_attributes = True
