"""Working set model."""

from datetime import datetime

from pydantic import BaseModel, Field

from .segments import ContextSegment


class WorkingSet(BaseModel):
    """Working set abstraction."""

    segments: list[ContextSegment] = Field(description="Active segments")
    total_tokens: int = Field(description="Total token count")
    project_id: str = Field(description="Project identifier")
    task_id: str | None = Field(None, description="Task identifier")
    last_updated: datetime = Field(description="Last update timestamp")
