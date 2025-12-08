"""Tool handler for context_gc_pin."""

import logging
from typing import Any

from ...app_state import AppState
from ...models import GCPinParams

logger = logging.getLogger(__name__)


async def handle_gc_pin(
    app_state: AppState,
    project_id: str | None = None,
    segment_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Pin segments to protect them from pruning.

    Pinned segments will not be pruned by the GC engine. Use this tool to
    protect important segments from being removed.

    Args:
        app_state: Application state with all components
        project_id: Project identifier (required)
        segment_ids: List of segment IDs to pin (required)

    Returns:
        Dictionary with:
        - pinned_segments: List[str] (segment IDs that were pinned)
        - errors: List[str] (any errors encountered)

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate and parse parameters
    try:
        params = GCPinParams(project_id=project_id or "", segment_ids=segment_ids or [])
    except Exception as e:
        logger.error(f"Invalid parameters for gc_pin: {e}")
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

        # Pin segments
        pinned_segments: list[str] = []
        errors: list[str] = []

        for segment_id in params.segment_ids:
            if segment_id not in segment_map:
                errors.append(f"Segment {segment_id} not found")
                continue

            segment = segment_map[segment_id]

            # Update pinned status
            segment.pinned = True

            # Update in storage
            try:
                app_state.storage.update_segment(segment, params.project_id)
                pinned_segments.append(segment_id)
            except Exception as e:
                error_msg = f"Failed to pin segment {segment_id}: {e!s}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)

        return {
            "pinned_segments": pinned_segments,
            "errors": errors,
        }
    except ValueError as e:
        logger.error(f"Value error in gc_pin: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
                "details": {},
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in gc_pin: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
                "details": {"exception": str(e)},
            }
        }
