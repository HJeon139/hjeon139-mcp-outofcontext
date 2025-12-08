"""Tool parameter models."""

from typing import Literal

from pydantic import BaseModel, Field

from .descriptors import ContextDescriptors


class AnalyzeUsageParams(BaseModel):
    """Parameters for context_analyze_usage tool."""

    context_descriptors: ContextDescriptors | None = Field(
        None, description="Optional context descriptors from platform"
    )
    project_id: str = Field(description="Project identifier")
    task_id: str | None = Field(None, description="Optional task identifier")
    token_limit: int | None = Field(
        None, description="Optional token limit (defaults to config value, typically 1 million)"
    )


class GetWorkingSetParams(BaseModel):
    """Parameters for context_get_working_set tool."""

    project_id: str = Field(description="Project identifier")
    task_id: str | None = Field(None, description="Optional task identifier")


class GCAnalyzeParams(BaseModel):
    """Parameters for context_gc_analyze tool."""

    context_descriptors: ContextDescriptors | None = Field(
        None, description="Optional context descriptors from platform"
    )
    project_id: str = Field(description="Project identifier")
    task_id: str | None = Field(None, description="Optional task identifier")
    target_tokens: int | None = Field(None, description="Optional target tokens to free")


class GCPruneParams(BaseModel):
    """Parameters for context_gc_prune tool."""

    project_id: str = Field(description="Project identifier")
    segment_ids: list[str] = Field(description="List of segment IDs to prune")
    action: Literal["stash", "delete"] = Field(description="Action to take: stash or delete")
    confirm: bool = Field(False, description="Safety flag - must be True for delete actions")


class GCPinParams(BaseModel):
    """Parameters for context_gc_pin tool."""

    project_id: str = Field(description="Project identifier")
    segment_ids: list[str] = Field(description="List of segment IDs to pin")


class GCUnpinParams(BaseModel):
    """Parameters for context_gc_unpin tool."""

    project_id: str = Field(description="Project identifier")
    segment_ids: list[str] = Field(description="List of segment IDs to unpin")


class StashParams(BaseModel):
    """Parameters for context_stash tool."""

    project_id: str = Field(description="Project identifier")
    query: str | None = Field(
        None,
        description=(
            "Optional keyword search query to match segment text. "
            "If provided, only segments containing this text will be stashed."
        ),
    )
    filters: dict | None = Field(
        None,
        description=(
            "Optional metadata filters: file_path, task_id, tags (list), type, "
            "created_after (ISO datetime), created_before (ISO datetime). "
            "If provided, only segments matching these filters will be stashed."
        ),
    )


class SearchStashedParams(BaseModel):
    """Parameters for context_search_stashed tool."""

    project_id: str | None = Field(
        None, description="Optional project identifier. If omitted, searches across all projects."
    )
    query: str | None = Field(None, description="Keyword search query")
    filters: dict | None = Field(
        None,
        description=(
            "Metadata filters: file_path, task_id, tags (list), type, "
            "created_after (ISO datetime), created_before (ISO datetime)"
        ),
    )
    limit: int | None = Field(50, description="Maximum number of results to return")


class RetrieveStashedParams(BaseModel):
    """Parameters for context_retrieve_stashed tool."""

    project_id: str = Field(description="Project identifier")
    query: str | None = Field(
        None,
        description=(
            "Optional keyword search query to match segment text. "
            "If provided, only segments containing this text will be retrieved."
        ),
    )
    filters: dict | None = Field(
        None,
        description=(
            "Optional metadata filters: file_path, task_id, tags (list), type, "
            "created_after (ISO datetime), created_before (ISO datetime). "
            "If provided, only segments matching these filters will be retrieved."
        ),
    )
    move_to_active: bool = Field(
        False,
        description=(
            "If True, move retrieved segments back to active storage. "
            "If False, segments remain stashed but are returned for inspection."
        ),
    )


class SetCurrentTaskParams(BaseModel):
    """Parameters for context_set_current_task tool."""

    project_id: str = Field(description="Project identifier")
    task_id: str | None = Field(None, description="Task identifier (None to clear current task)")


class GetTaskContextParams(BaseModel):
    """Parameters for context_get_task_context tool."""

    project_id: str = Field(description="Project identifier")
    task_id: str | None = Field(None, description="Task identifier (None uses current task)")


class CreateTaskSnapshotParams(BaseModel):
    """Parameters for context_create_task_snapshot tool."""

    project_id: str = Field(description="Project identifier")
    task_id: str | None = Field(None, description="Task identifier (None uses current task)")
    name: str | None = Field(None, description="Optional snapshot name")
