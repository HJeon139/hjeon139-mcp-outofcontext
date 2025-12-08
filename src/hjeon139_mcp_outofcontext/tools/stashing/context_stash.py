"""Tool handler for context_stash."""

import logging
from datetime import datetime
from typing import Any

from ...app_state import AppState
from ...models import StashParams
from .helpers import create_error_response, parse_filters_param

logger = logging.getLogger(__name__)


async def handle_stash(
    app_state: AppState,
    project_id: str | None = None,
    query: str | None = None,
    filters: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    """
    Put context into stashed storage by filtering active segments.

    This tool moves segments from active (working) storage to stashed storage
    based on query and filter criteria. Use this when you need to free up active
    context space or archive segments for later retrieval.

    **When to use:**
    - When context usage is high (e.g., >80%) and you need to free space
    - When you want to archive old or unused segments
    - When you want to stash segments matching specific criteria (file, task, type, etc.)

    **How to use:**
    - **Avoid project_id when possible** - the server uses the project directory by default
    - Optional: project_id (defaults to 'default' if omitted)
    - Optional: query to match segment text (e.g., "old documentation")
    - Optional: filters to match metadata (e.g., {"type": "file", "task_id": "task-123"})
    - If both query and filters are omitted, all working segments will be stashed

    Args:
        app_state: Application state with all components
        project_id: Optional project identifier (defaults to 'default')
        query: Optional keyword search to match segment text
        filters: Optional metadata filters (file_path, task_id, tags, type, created_after, created_before)

    Returns:
        Dictionary with:
        - stashed_segments: List[str] (segment IDs that were stashed)
        - tokens_stashed: int (total tokens stashed)
        - segments_matched: int (number of segments that matched the criteria)
        - errors: List[str] (any errors encountered)
    """
    # Parse and validate parameters
    try:
        parsed_filters = parse_filters_param(filters)
        # Use 'default' as the default project_id when not provided
        effective_project_id = project_id or "default"
        params = StashParams(
            project_id=effective_project_id,
            query=query,
            filters=parsed_filters,
        )
    except ValueError as e:
        logger.error(f"Invalid parameters for context_stash: {e}")
        return create_error_response("INVALID_PARAMETER", str(e), {"exception": str(e)})
    except Exception as e:
        logger.error(f"Unexpected parameter error in context_stash: {e}")
        return create_error_response(
            "INVALID_PARAMETER", f"Invalid parameters: {e!s}", {"exception": str(e)}
        )

    # Execute stash operation
    try:
        working_set = app_state.context_manager.get_working_set(
            project_id=effective_project_id,
            task_id=None,  # Get all segments, not just current task
        )

        matching_segments = _filter_segments(
            working_set.segments,
            query=params.query,
            filters=params.filters,
        )

        if not matching_segments:
            return {
                "stashed_segments": [],
                "tokens_stashed": 0,
                "segments_matched": 0,
                "errors": [],
            }

        segment_ids = [seg.segment_id for seg in matching_segments]
        stash_result = app_state.context_manager.stash_segments(
            segment_ids=segment_ids,
            project_id=effective_project_id,
        )

        return {
            "stashed_segments": stash_result.stashed_segments,
            "tokens_stashed": stash_result.tokens_freed,
            "segments_matched": len(matching_segments),
            "errors": [],
        }
    except ValueError as e:
        logger.error(f"Value error in context_stash: {e}")
        return create_error_response("INVALID_PARAMETER", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in context_stash: {e}", exc_info=True)
        return create_error_response(
            "INTERNAL_ERROR", f"Internal error: {e!s}", {"exception": str(e)}
        )


def _filter_segments(
    segments: list[Any],
    query: str | None = None,
    filters: dict[str, Any] | None = None,
) -> list[Any]:
    """Filter segments by query and metadata filters.

    Args:
        segments: List of segments to filter
        query: Optional keyword search query (case-insensitive substring match)
        filters: Optional metadata filters dictionary

    Returns:
        List of matching segments
    """
    filtered = segments

    if query:
        filtered = _apply_query_filter(filtered, query)

    if filters:
        filtered = _apply_metadata_filters(filtered, filters)

    return filtered


def _apply_query_filter(segments: list[Any], query: str) -> list[Any]:
    """Apply keyword query filter to segments."""
    query_lower = query.lower()
    return [seg for seg in segments if seg.text and query_lower in seg.text.lower()]


def _apply_metadata_filters(segments: list[Any], filters: dict[str, Any]) -> list[Any]:
    """Apply metadata filters to segments."""
    filtered = segments

    # Direct equality filters
    for key in ("file_path", "task_id", "type"):
        if key in filters:
            filtered = [seg for seg in filtered if getattr(seg, key, None) == filters[key]]

    # Tags filter (segment must have all specified tags)
    if "tags" in filters:
        required_tags = set(filters["tags"])
        filtered = [seg for seg in filtered if required_tags.issubset(set(seg.tags or []))]

    # Datetime filters
    if "created_after" in filters:
        filtered = _apply_datetime_filter(filtered, filters["created_after"], "created_after")
    if "created_before" in filters:
        filtered = _apply_datetime_filter(filtered, filters["created_before"], "created_before")

    return filtered


def _apply_datetime_filter(segments: list[Any], datetime_str: str, filter_type: str) -> list[Any]:
    """Apply datetime filter to segments."""
    try:
        dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        if filter_type == "created_after":
            return [seg for seg in segments if seg.created_at >= dt]
        if filter_type == "created_before":
            return [seg for seg in segments if seg.created_at <= dt]
    except (ValueError, AttributeError) as e:
        logger.warning(f"Invalid {filter_type} datetime: {e}")
    return segments
