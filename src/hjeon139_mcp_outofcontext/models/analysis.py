"""Analysis and metrics models."""

from typing import Literal

from pydantic import BaseModel, Field


class UsageMetrics(BaseModel):
    """Context usage metrics."""

    total_tokens: int = Field(description="Total token count")
    total_segments: int = Field(description="Total segment count")
    tokens_by_type: dict[str, int] = Field(
        default_factory=dict, description="Token count by segment type"
    )
    segments_by_type: dict[str, int] = Field(
        default_factory=dict, description="Segment count by type"
    )
    tokens_by_task: dict[str, int] = Field(
        default_factory=dict, description="Token count by task ID"
    )
    oldest_segment_age_hours: float = Field(description="Age of oldest segment in hours")
    newest_segment_age_hours: float = Field(description="Age of newest segment in hours")
    pinned_segments_count: int = Field(description="Number of pinned segments")
    pinned_tokens: int = Field(description="Total tokens in pinned segments")
    usage_percent: float = Field(description="Usage percentage (0-100)")
    estimated_remaining_tokens: int = Field(description="Estimated remaining tokens")


class HealthScore(BaseModel):
    """Context health score."""

    score: float = Field(description="Health score (0-100, higher = healthier)")
    usage_percent: float = Field(description="Usage percentage (0-100)")
    factors: dict[str, float] = Field(
        default_factory=dict, description="Score factors and contributions"
    )


class Recommendation(BaseModel):
    """Recommendation for context management."""

    priority: Literal["low", "medium", "high", "urgent"] = Field(description="Priority level")
    message: str = Field(description="Recommendation message")
    action: str | None = Field(None, description="Suggested action")


class AnalysisResult(BaseModel):
    """Context analysis results."""

    total_tokens: int = Field(description="Total token count")
    segment_count: int = Field(description="Number of segments")
    usage_percent: float = Field(description="Usage percentage")
    health_score: "HealthScore" = Field(description="Context health score")
    recommendations: list[str] = Field(default_factory=list, description="Analysis recommendations")
