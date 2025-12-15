"""Pydantic models for query tool parameters."""

from pydantic import BaseModel, Field


class ListContextParams(BaseModel):
    """Parameters for list_context tool."""

    limit: int | None = Field(None, description="Limit number of results", ge=1)


class SearchContextParams(BaseModel):
    """Parameters for search_context tool."""

    query: str = Field(..., description="Search query string")
    limit: int | None = Field(None, description="Limit number of results", ge=1)
