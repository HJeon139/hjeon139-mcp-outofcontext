"""Stashing-related models."""

from pydantic import BaseModel, Field


class StashResult(BaseModel):
    """Stashing operation result."""

    stashed_segments: list[str] = Field(description="IDs of stashed segments")
    tokens_freed: int = Field(description="Tokens freed by stashing")
    stash_location: str | None = Field(None, description="Stash storage location")
