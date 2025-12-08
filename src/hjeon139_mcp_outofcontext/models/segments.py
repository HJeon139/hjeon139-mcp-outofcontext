"""Segment-related models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SegmentSummary(BaseModel):
    """High-level segment information."""

    segment_id: str = Field(description="Segment identifier")
    type: Literal["message", "code", "log", "note", "decision", "summary"] = Field(
        description="Segment type"
    )
    preview: str = Field(description="Text preview (first N characters)")
    tokens: int = Field(description="Token count")
    created_at: datetime = Field(description="Creation timestamp")


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
    tokens: int | None = Field(None, description="Token count (cached)")
    tokens_computed_at: datetime | None = Field(None, description="When token count was computed")
    text_hash: str | None = Field(None, description="Hash of text for cache invalidation")
    tier: Literal["working", "stashed", "archive"] = Field("working", description="Storage tier")
