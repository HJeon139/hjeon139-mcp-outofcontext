"""Tool handler for context_gc_unpin."""

import logging
from typing import Any

from ...app_state import AppState
from ...models import GCUnpinParams

logger = logging.getLogger(__name__)


async def handle_gc_unpin(
    app_state: AppState,
    project_id: str | None = None,
    segment_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Unpin segments to allow pruning.

    Unpinned segments can be pruned by the GC engine. Use this tool to
    allow previously pinned segments to be removed.

    Args:
        app_state: Application state with all components
        project_id: Project identifier (required)
        segment_ids: List of segment IDs to unpin (required)

    Returns:
        Dictionary with:
        - unpinned_segments: List[str] (segment IDs that were unpinned)
        - errors: List[str] (any errors encountered)

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate and parse parameters
    try:
        params = GCUnpinParams(project_id=project_id or "", segment_ids=segment_ids or [])
    except Exception as e:
        logger.error(f"Invalid parameters for gc_unpin: {e}")
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
        # Load all segments
        all_segments = app_state.storage.load_segments(params.project_id)

        # Build segment lookup
        segment_map = {s.segment_id: s for s in all_segments}

        # Unpin segments
        unpinned_segments: list[str] = []
        errors: list[str] = []

        for segment_id in params.segment_ids:
            if segment_id not in segment_map:
                errors.append(f"Segment {segment_id} not found")
                continue

            segment = segment_map[segment_id]

            # Update pinned status
            segment.pinned = False

            # Update in storage
            try:
                app_state.storage.update_segment(segment, params.project_id)
                unpinned_segments.append(segment_id)
            except Exception as e:
                error_msg = f"Failed to unpin segment {segment_id}: {e!s}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)

        return {
            "unpinned_segments": unpinned_segments,
            "errors": errors,
        }
    except ValueError as e:
        logger.error(f"Value error in gc_unpin: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
                "details": {},
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in gc_unpin: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
                "details": {"exception": str(e)},
            }
        }
