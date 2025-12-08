"""Tool handler for context_retrieve_stashed."""

import logging
from typing import Any

from ...app_state import AppState
from ...models import RetrieveStashedParams

logger = logging.getLogger(__name__)


async def handle_retrieve_stashed(
    app_state: AppState,
    project_id: str | None = None,
    segment_ids: list[str] | None = None,
    move_to_active: bool = False,
) -> dict[str, Any]:
    """
    Retrieve specific stashed segments by ID and optionally move back to active.

    This tool retrieves stashed segments by their IDs. Optionally, segments can
    be moved back to active storage (unstashed) if move_to_active=True.

    Args:
        app_state: Application state with all components
        project_id: Project identifier (required)
        segment_ids: List of segment IDs to retrieve (required)
        move_to_active: If True, move segments back to active storage (default: False)

    Returns:
        Dictionary with:
        - retrieved_segments: List[ContextSegment] (retrieved segments)
        - moved_to_active: List[str] (segment IDs moved to active, if move_to_active=True)

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate and parse parameters
    try:
        params = RetrieveStashedParams(
            project_id=project_id or "",
            segment_ids=segment_ids or [],
            move_to_active=move_to_active,
        )
    except Exception as e:
        logger.error(f"Invalid parameters for context_retrieve_stashed: {e}")
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
        # Load all segments to find stashed ones
        all_segments = app_state.storage.load_segments(params.project_id)

        # Filter to only stashed segments with matching IDs
        segments_to_retrieve: list[tuple[str, Any]] = []
        for segment in all_segments:
            if segment.segment_id in params.segment_ids and segment.tier == "stashed":
                segments_to_retrieve.append((segment.segment_id, segment))

        # Retrieve segments
        retrieved_segments: list[Any] = []
        moved_ids: list[str] = []

        for segment_id, segment in segments_to_retrieve:
            # Add to retrieved list
            retrieved_segments.append(segment)

            # Move to active if requested
            if params.move_to_active:
                try:
                    # Update segment tier to working
                    segment.tier = "working"
                    # Unstash the segment (move from stashed to active)
                    app_state.storage.unstash_segment(segment, params.project_id)
                    moved_ids.append(segment_id)
                except Exception as e:
                    logger.error(f"Failed to move segment {segment_id} to active: {e}")
                    # Continue with other segments

        # Invalidate working set cache if segments were moved to active
        if (
            params.move_to_active
            and moved_ids
            and hasattr(app_state.context_manager, "working_sets")
            and params.project_id in app_state.context_manager.working_sets
        ):
            app_state.context_manager.working_sets[params.project_id].clear()

        # Format response
        return {
            "retrieved_segments": [segment.model_dump() for segment in retrieved_segments],
            "moved_to_active": moved_ids if params.move_to_active else [],
        }
    except ValueError as e:
        logger.error(f"Value error in context_retrieve_stashed: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
                "details": {},
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in context_retrieve_stashed: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
                "details": {"exception": str(e)},
            }
        }
