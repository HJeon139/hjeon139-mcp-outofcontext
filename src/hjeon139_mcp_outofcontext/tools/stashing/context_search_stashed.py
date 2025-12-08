"""Tool handler for context_search_stashed."""

import logging
from datetime import datetime
from typing import Any

from ...app_state import AppState
from ...models import SearchStashedParams

logger = logging.getLogger(__name__)


async def handle_search_stashed(
    app_state: AppState,
    project_id: str | None = None,
    query: str | None = None,
    filters: dict[str, Any] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """
    Search stashed segments by keyword and metadata filters.

    This tool searches stashed segments using:
    - Keyword search: case-insensitive substring matching in segment text
    - Metadata filters: file_path, task_id, tags, type, created_after, created_before

    Args:
        app_state: Application state with all components
        project_id: Project identifier (required)
        query: Optional keyword search query
        filters: Optional metadata filters dictionary
        limit: Optional maximum number of results (default: 50)

    Returns:
        Dictionary with:
        - segments: List[ContextSegment] (matching segments)
        - total_matches: int (total number of matches)
        - query: str (the query used)
        - filters_applied: dict (the filters applied)

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate and parse parameters
    try:
        params = SearchStashedParams(
            project_id=project_id or "",
            query=query,
            filters=filters,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Invalid parameters for context_search_stashed: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": f"Invalid parameters: {e!s}",
                "details": {"exception": str(e)},
            }
        }

    if not params.project_id:
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": "project_id is required",
                "details": {},
            }
        }

    try:
        # Normalize query (empty string if None)
        search_query = params.query or ""

        # Prepare filters dictionary
        filters_dict: dict[str, Any] = params.filters or {}

        # Parse datetime filters if present
        if "created_after" in filters_dict:
            try:
                filters_dict["created_after"] = datetime.fromisoformat(
                    filters_dict["created_after"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid created_after datetime: {e}")
                return {
                    "error": {
                        "code": "INVALID_PARAMETER",
                        "message": f"Invalid created_after datetime format: {e!s}",
                        "details": {},
                    }
                }

        if "created_before" in filters_dict:
            try:
                filters_dict["created_before"] = datetime.fromisoformat(
                    filters_dict["created_before"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid created_before datetime: {e}")
                return {
                    "error": {
                        "code": "INVALID_PARAMETER",
                        "message": f"Invalid created_before datetime format: {e!s}",
                        "details": {},
                    }
                }

        # Call storage layer to search stashed segments
        # This uses the indexed search implementation
        segments = app_state.storage.search_stashed(
            query=search_query,
            filters=filters_dict,
            project_id=params.project_id,
        )

        # Apply datetime filters (not handled by indexing layer)
        if "created_after" in filters_dict:
            after = filters_dict["created_after"]
            segments = [s for s in segments if s.created_at >= after]

        if "created_before" in filters_dict:
            before = filters_dict["created_before"]
            segments = [s for s in segments if s.created_at <= before]

        # Sort by recency (most recent first)
        segments.sort(key=lambda s: s.created_at, reverse=True)

        # Apply limit
        total_matches = len(segments)
        if params.limit and params.limit > 0:
            segments = segments[: params.limit]

        # Format response
        return {
            "segments": [segment.model_dump() for segment in segments],
            "total_matches": total_matches,
            "query": search_query,
            "filters_applied": filters_dict,
        }
    except ValueError as e:
        logger.error(f"Value error in context_search_stashed: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
                "details": {},
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in context_search_stashed: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
                "details": {"exception": str(e)},
            }
        }
