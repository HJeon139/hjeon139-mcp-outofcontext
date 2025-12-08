"""Tool handler for context_stash."""

import logging
from typing import Any

from ...app_state import AppState
from ...models import StashParams

logger = logging.getLogger(__name__)


async def handle_stash(
    app_state: AppState,
    project_id: str | None = None,
    segment_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Move segments from active context to stashed storage.

    This tool moves specified segments from active (working) storage to
    stashed storage. Stashed segments are persisted and can be searched and
    retrieved later.

    Args:
        app_state: Application state with all components
        project_id: Project identifier (required)
        segment_ids: List of segment IDs to stash (required)

    Returns:
        Dictionary with:
        - stashed_segments: List[str] (segment IDs that were stashed)
        - tokens_stashed: int (total tokens stashed)
        - errors: List[str] (any errors encountered)

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate and parse parameters
    try:
        params = StashParams(
            project_id=project_id or "",
            segment_ids=segment_ids or [],
        )
    except Exception as e:
        logger.error(f"Invalid parameters for context_stash: {e}")
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

    if not params.segment_ids:
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": "segment_ids cannot be empty",
                "details": {},
            }
        }

    try:
        # Use context manager to stash segments
        stash_result = app_state.context_manager.stash_segments(
            segment_ids=params.segment_ids,
            project_id=params.project_id,
        )

        # Format response
        return {
            "stashed_segments": stash_result.stashed_segments,
            "tokens_stashed": stash_result.tokens_freed,
            "errors": [],  # Context manager handles errors internally
        }
    except ValueError as e:
        logger.error(f"Value error in context_stash: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
                "details": {},
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in context_stash: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
                "details": {"exception": str(e)},
            }
        }
