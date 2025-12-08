"""Pruning-related models."""

from typing import Literal

from pydantic import BaseModel, Field


class PruningRecommendation(BaseModel):
    """Pruning action recommendation."""

    segment_ids: list[str] = Field(description="Segments to prune")
    action: Literal["stash", "delete"] = Field(description="Action to take")
    reason: str = Field(description="Reason for pruning")
    tokens_freed: int = Field(description="Estimated tokens saved")


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
