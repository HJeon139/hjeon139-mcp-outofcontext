"""Core data models for context management."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


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


class SegmentSummary(BaseModel):
    """High-level segment information."""

    segment_id: str = Field(description="Segment identifier")
    type: Literal["message", "code", "log", "note", "decision", "summary"] = Field(
        description="Segment type"
    )
    preview: str = Field(description="Text preview (first N characters)")
    tokens: int = Field(description="Token count")
    created_at: datetime = Field(description="Creation timestamp")


class TaskInfo(BaseModel):
    """Task metadata."""

    task_id: str = Field(description="Task identifier")
    name: str | None = Field(None, description="Task name")
    description: str | None = Field(None, description="Task description")
    created_at: datetime | None = Field(None, description="Task creation timestamp")


class ContextSegment(BaseModel):
    """Core segment model with all metadata fields."""

    segment_id: str = Field(description="Unique segment identifier")
    text: str = Field(description="Segment text content")
    type: Literal["message", "code", "log", "note", "decision", "summary"] = Field(
        description="Segment type"
    )

    # Metadata
    project_id: str = Field(description="Project identifier")
    task_id: str | None = Field(None, description="Task identifier")
    created_at: datetime = Field(description="Creation timestamp")
    last_touched_at: datetime = Field(description="Last access timestamp")

    # GC Metadata
    pinned: bool = Field(False, description="Whether segment is pinned")
    generation: Literal["young", "old"] = Field("young", description="GC generation")
    gc_survival_count: int = Field(0, description="Number of GC cycles survived")
    refcount: int = Field(0, description="Reference count")

    # Organization
    file_path: str | None = Field(None, description="File path if applicable")
    line_range: tuple[int, int] | None = Field(None, description="Line range if applicable")
    tags: list[str] = Field(default_factory=list, description="Tags")
    topic_id: str | None = Field(None, description="Topic identifier")

    # Storage
    tokens: int = Field(description="Token count")
    tier: Literal["working", "stashed", "archive"] = Field("working", description="Storage tier")


class ContextDescriptors(BaseModel):
    """Input descriptor for platform context."""

    recent_messages: list[Message] = Field(default_factory=list, description="Last N messages")
    current_file: FileInfo | None = Field(None, description="Active file and location")
    token_usage: TokenUsage = Field(description="Current token counts")
    segment_summaries: list[SegmentSummary] = Field(
        default_factory=list, description="High-level segment info"
    )
    task_info: TaskInfo | None = Field(None, description="Current task metadata")


class PruningRecommendation(BaseModel):
    """Pruning action recommendation."""

    segment_ids: list[str] = Field(description="Segments to prune")
    action: Literal["stash", "delete"] = Field(description="Action to take")
    reason: str = Field(description="Reason for pruning")
    tokens_freed: int = Field(description="Estimated tokens saved")


class WorkingSet(BaseModel):
    """Working set abstraction."""

    segments: list[ContextSegment] = Field(description="Active segments")
    total_tokens: int = Field(description="Total token count")
    project_id: str = Field(description="Project identifier")
    task_id: str | None = Field(None, description="Task identifier")


class StashResult(BaseModel):
    """Stashing operation result."""

    stashed_segments: list[str] = Field(description="IDs of stashed segments")
    tokens_freed: int = Field(description="Tokens freed by stashing")
    stash_location: str | None = Field(None, description="Stash storage location")


class AnalysisResult(BaseModel):
    """Context analysis results."""

    total_tokens: int = Field(description="Total token count")
    segment_count: int = Field(description="Number of segments")
    usage_percent: float = Field(description="Usage percentage")
    recommendations: list[str] = Field(default_factory=list, description="Analysis recommendations")


class PruningCandidate(BaseModel):
    """Pruning candidate with score and metadata."""

    segment_id: str = Field(description="Segment identifier")
    score: float = Field(description="Prune score (higher = more likely to prune)")
    tokens: int = Field(description="Token count for this segment")
    reason: str = Field(description="Reason why it's a candidate")
    segment_type: str = Field(description="Segment type")
    age_hours: float = Field(description="Age in hours")


class PruningPlan(BaseModel):
    """Pruning plan with candidates and actions."""

    candidates: list[PruningCandidate] = Field(description="Sorted candidates by score")
    total_tokens_freed: int = Field(description="Total tokens that will be freed")
    stash_segments: list[str] = Field(description="Segment IDs to stash")
    delete_segments: list[str] = Field(description="Segment IDs to delete")
    reason: str = Field(description="Explanation of plan")
