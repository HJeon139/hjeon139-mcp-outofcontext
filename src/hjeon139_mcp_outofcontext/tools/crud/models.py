"""Pydantic models for CRUD tool parameters."""

from typing import Any

from pydantic import BaseModel, Field


class ContextItem(BaseModel):
    """Single context item for bulk operations."""

    name: str = Field(..., description="Context name (filename-safe)")
    text: str = Field(..., description="Markdown content")
    metadata: dict[str, Any] | None = Field(None, description="Optional metadata dict")


class PutContextParams(BaseModel):
    """Parameters for put_context tool."""

    name: str | None = Field(None, description="Context name (for single operation)")
    text: str | None = Field(None, description="Markdown content (for single operation)")
    metadata: dict[str, Any] | None = Field(
        None, description="Optional metadata (for single operation)"
    )
    contexts: list[ContextItem] | None = Field(
        None, description="List of contexts (for bulk operation)"
    )


class GetContextParams(BaseModel):
    """Parameters for get_context tool."""

    name: str | list[str] | None = Field(None, description="Context name (single) or list (bulk)")
    names: list[str] | None = Field(None, description="List of context names (bulk operation)")


class DeleteContextParams(BaseModel):
    """Parameters for delete_context tool."""

    name: str | list[str] | None = Field(None, description="Context name (single) or list (bulk)")
    names: list[str] | None = Field(None, description="List of context names (bulk operation)")
