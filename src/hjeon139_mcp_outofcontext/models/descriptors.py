"""Context descriptor models for platform input."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .segments import SegmentSummary


class TokenUsage(BaseModel):
    """Token count information."""

    current: int = Field(description="Current token count")
    limit: int = Field(description="Token limit")
    usage_percent: float = Field(description="Usage percentage (0-100)")


class FileInfo(BaseModel):
    """File metadata."""

    path: str = Field(description="File path")
    name: str | None = Field(None, description="File name")
    extension: str | None = Field(None, description="File extension")
    line_count: int | None = Field(None, description="Total line count")
    current_line: int | None = Field(None, description="Current cursor line")


class Message(BaseModel):
    """Message structure."""

    role: Literal["user", "assistant", "system"] = Field(description="Message role")
    content: str = Field(description="Message content")
    timestamp: datetime | None = Field(None, description="Message timestamp")


class TaskInfo(BaseModel):
    """Task metadata."""

    task_id: str = Field(description="Task identifier")
    name: str | None = Field(None, description="Task name")
    description: str | None = Field(None, description="Task description")
    created_at: datetime | None = Field(None, description="Task creation timestamp")


class ContextDescriptors(BaseModel):
    """Input descriptor for platform context."""

    recent_messages: list[Message] = Field(default_factory=list, description="Last N messages")
    current_file: FileInfo | None = Field(None, description="Active file and location")
    token_usage: TokenUsage = Field(description="Current token counts")
    segment_summaries: list[SegmentSummary] = Field(
        default_factory=list, description="High-level segment info"
    )
    task_info: TaskInfo | None = Field(None, description="Current task metadata")
