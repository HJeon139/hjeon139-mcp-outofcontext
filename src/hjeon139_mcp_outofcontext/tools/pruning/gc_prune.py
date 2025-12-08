"""Tool handler for context_gc_prune."""

import logging
from typing import Any, Literal, cast

from ...app_state import AppState
from ...models import GCPruneParams

logger = logging.getLogger(__name__)


async def handle_gc_prune(
    app_state: AppState,
    project_id: str | None = None,
    segment_ids: list[str] | None = None,
    action: str | None = None,
    confirm: bool = False,
) -> dict[str, Any]:
    """
    Execute pruning plan to free context space.

    This tool executes a pruning operation on specified segments. Segments can be
    either stashed (moved to stashed storage) or deleted (permanently removed).
    Pinned segments cannot be pruned and will result in an error.

    Args:
        app_state: Application state with all components
        project_id: Project identifier (required)
        segment_ids: List of segment IDs to prune (required)
        action: Action to take: "stash" or "delete" (required)
        confirm: Safety flag - must be True for delete actions (default: False)

    Returns:
        Dictionary with:
        - pruned_segments: List[str] (segment IDs that were pruned)
        - tokens_freed: int
        - action: str ("stashed" or "deleted")
        - errors: List[str] (any errors encountered)

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate and parse parameters
    try:
        # Cast action to Literal type
        action_value = cast(
            Literal["stash", "delete"],
            action if action in ("stash", "delete") else "stash",
        )
        params = GCPruneParams(
            project_id=project_id or "",
            segment_ids=segment_ids or [],
            action=action_value,
            confirm=confirm,
        )
    except Exception as e:
        logger.error(f"Invalid parameters for gc_prune: {e}")
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

    # Safety check for delete actions
    if params.action == "delete" and not params.confirm:
        return {
            "error": {
                "code": "CONFIRMATION_REQUIRED",
                "message": "confirm=True is required for delete actions",
                "details": {},
            }
        }

    try:
        # Load all segments to validate
        all_segments = app_state.storage.load_segments(params.project_id)

        # Build segment lookup
        segment_map = {s.segment_id: s for s in all_segments}

        # Validate segment IDs and check for pinned segments
        pruned_segments: list[str] = []
        tokens_freed = 0
        errors: list[str] = []
        segments_to_prune: list[tuple[str, Any]] = []

        for segment_id in params.segment_ids:
            if segment_id not in segment_map:
                errors.append(f"Segment {segment_id} not found")
                continue

            segment = segment_map[segment_id]

            # Check if pinned
            if segment.pinned:
                errors.append(f"Segment {segment_id} is pinned and cannot be pruned")
                continue

            # Check if segment is in working tier
            if segment.tier != "working":
                errors.append(f"Segment {segment_id} is not in working tier (tier: {segment.tier})")
                continue

            segments_to_prune.append((segment_id, segment))

        # Execute pruning action
        action_taken = "stashed" if params.action == "stash" else "deleted"

        for segment_id, segment in segments_to_prune:
            try:
                if params.action == "stash":
                    # Stash the segment
                    app_state.storage.stash_segment(segment, params.project_id)
                    pruned_segments.append(segment_id)
                    tokens = segment.tokens if segment.tokens is not None else 0
                    tokens_freed += tokens
                elif params.action == "delete":
                    # Delete the segment
                    app_state.storage.delete_segment(segment_id, params.project_id)
                    pruned_segments.append(segment_id)
                    tokens = segment.tokens if segment.tokens is not None else 0
                    tokens_freed += tokens
            except Exception as e:
                error_msg = f"Failed to {params.action} segment {segment_id}: {e!s}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)

        # Invalidate working set cache in context manager
        if (
            hasattr(app_state.context_manager, "working_sets")
            and params.project_id in app_state.context_manager.working_sets
        ):
            app_state.context_manager.working_sets[params.project_id].clear()

        return {
            "pruned_segments": pruned_segments,
            "tokens_freed": tokens_freed,
            "action": action_taken,
            "errors": errors,
        }
    except ValueError as e:
        logger.error(f"Value error in gc_prune: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
                "details": {},
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in gc_prune: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
                "details": {"exception": str(e)},
            }
        }
