"""Tool handler for context_retrieve_stashed."""

import logging
from datetime import datetime
from typing import Any

from ...app_state import AppState
from ...models import RetrieveStashedParams
from .helpers import create_error_response, parse_filters_param

logger = logging.getLogger(__name__)


def _parse_search_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
    """Parse and validate search filters, converting datetime strings.

    Args:
        filters: Filters dictionary to parse

    Returns:
        Parsed filters dictionary with datetime objects

    Raises:
        ValueError: If datetime parsing fails
    """
    filters_dict: dict[str, Any] = filters or {}

    for key in ("created_after", "created_before"):
        if key in filters_dict:
            try:
                filters_dict[key] = datetime.fromisoformat(
                    str(filters_dict[key]).replace("Z", "+00:00")
                )
            except (ValueError, AttributeError) as e:
                raise ValueError(f"Invalid {key} datetime format: {e!s}") from e

    return filters_dict


def _process_retrieved_segments(
    segments: list[Any],
    move_to_active: bool,
    app_state: AppState,
    project_id: str,
) -> dict[str, Any]:
    """Process retrieved segments and optionally move them to active storage.

    Returns:
        Dictionary with "retrieved_segments" and "moved_ids" keys
    """
    retrieved_segments: list[dict[str, Any]] = []
    moved_ids: list[str] = []

    for segment in segments:
        retrieved_segments.append(segment.model_dump())

        if move_to_active:
            try:
                segment.tier = "working"
                app_state.storage.unstash_segment(segment, project_id)
                moved_ids.append(segment.segment_id)
            except Exception as e:
                logger.error(f"Failed to move segment {segment.segment_id} to active: {e}")

    if move_to_active and moved_ids:
        _invalidate_working_set_cache(app_state, project_id)

    return {
        "retrieved_segments": retrieved_segments,
        "moved_ids": moved_ids,
    }


def _invalidate_working_set_cache(app_state: AppState, project_id: str) -> None:
    """Invalidate working set cache for a project."""
    if (
        hasattr(app_state.context_manager, "working_sets")
        and project_id in app_state.context_manager.working_sets
    ):
        app_state.context_manager.working_sets[project_id].clear()


async def handle_retrieve_stashed(
    app_state: AppState,
    project_id: str | None = None,
    query: str | None = None,
    filters: dict[str, Any] | str | None = None,
    move_to_active: bool = False,
) -> dict[str, Any]:
    """
    Fetch context from stashed storage by searching with query and filters.

    This tool retrieves stashed segments by searching with keyword queries and
    metadata filters. Use this to find and retrieve previously stashed context
    that you need to access again.

    **When to use:**
    - When you need to access previously stashed context
    - When you want to find context by content (query) or metadata (filters)
    - When you want to restore stashed segments back to active context (move_to_active=True)

    **How to use:**
    - **Avoid project_id when possible** - the server uses the project directory by default
    - Optional: project_id (defaults to 'default' if omitted)
    - Optional: query to match segment text (e.g., "launch bugs")
    - Optional: filters to match metadata (e.g., {"type": "file", "task_id": "task-123"})
    - Optional: move_to_active=True to restore segments to active context (default: False, just retrieves for inspection)
    - If both query and filters are omitted, all stashed segments will be retrieved

    Args:
        app_state: Application state with all components
        project_id: Optional project identifier (defaults to 'default')
        query: Optional keyword search to match segment text
        filters: Optional metadata filters (file_path, task_id, tags, type, created_after, created_before)
        move_to_active: If True, move segments back to active storage (default: False)

    Returns:
        Dictionary with:
        - retrieved_segments: List[dict] (retrieved segments with full details)
        - moved_to_active: List[str] (segment IDs moved to active, if move_to_active=True)
        - segments_found: int (number of segments that matched the criteria)
    """
    # Parse and validate parameters
    try:
        parsed_filters = parse_filters_param(filters)
        # Use 'default' as the default project_id when not provided
        effective_project_id = project_id or "default"
        params = RetrieveStashedParams(
            project_id=effective_project_id,
            query=query,
            filters=parsed_filters,
            move_to_active=move_to_active,
        )
    except ValueError as e:
        logger.error(f"Invalid parameters for context_retrieve_stashed: {e}")
        return create_error_response("INVALID_PARAMETER", str(e), {"exception": str(e)})
    except Exception as e:
        logger.error(f"Unexpected parameter error in context_retrieve_stashed: {e}")
        return create_error_response(
            "INVALID_PARAMETER", f"Invalid parameters: {e!s}", {"exception": str(e)}
        )

    # Execute retrieve operation
    try:
        filters_parsed = _parse_search_filters(params.filters)
        search_query = params.query or ""

        segments = app_state.storage.search_stashed(
            query=search_query,
            filters=filters_parsed,
            project_id=effective_project_id,
        )

        # Apply datetime filters (not handled by indexing layer)
        if "created_after" in filters_parsed:
            after = filters_parsed["created_after"]
            segments = [s for s in segments if s.created_at >= after]
        if "created_before" in filters_parsed:
            before = filters_parsed["created_before"]
            segments = [s for s in segments if s.created_at <= before]

        segments.sort(key=lambda s: s.created_at, reverse=True)

        result = _process_retrieved_segments(
            segments, params.move_to_active, app_state, effective_project_id
        )

        return {
            "retrieved_segments": result["retrieved_segments"],
            "moved_to_active": result["moved_ids"],
            "segments_found": len(segments),
        }
    except ValueError as e:
        logger.error(f"Value error in context_retrieve_stashed: {e}")
        return create_error_response("INVALID_PARAMETER", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in context_retrieve_stashed: {e}", exc_info=True)
        return create_error_response(
            "INTERNAL_ERROR", f"Internal error: {e!s}", {"exception": str(e)}
        )
