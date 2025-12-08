"""Tool handler for context_gc_analyze."""

import logging
from datetime import datetime, timedelta
from typing import Any

from ...app_state import AppState
from ...models import ContextDescriptors, GCAnalyzeParams

logger = logging.getLogger(__name__)


async def handle_gc_analyze(
    app_state: AppState,
    context_descriptors: dict[str, Any] | None = None,
    project_id: str | None = None,
    task_id: str | None = None,
    target_tokens: int | None = None,
) -> dict[str, Any]:
    """
    Analyze context and identify pruning candidates using GC heuristics.

    This tool analyzes the current context and identifies segments that are
    candidates for pruning based on GC heuristics (age, reachability, type, etc.).
    Optionally, if target_tokens is provided, it generates a pruning plan.

    Args:
        app_state: Application state with all components
        context_descriptors: Optional context descriptors from platform
        project_id: Project identifier (required)
        task_id: Optional task identifier
        target_tokens: Optional target tokens to free (if provided, generates pruning plan)

    Returns:
        Dictionary with:
        - pruning_candidates: List[PruningCandidate]
        - total_candidates: int
        - estimated_tokens_freed: int
        - pruning_plan: Optional[PruningPlan] (if target_tokens provided)

    Raises:
        ValueError: If project_id is missing or invalid
    """
    # Validate and parse parameters
    try:
        params = GCAnalyzeParams(
            context_descriptors=(
                ContextDescriptors(**context_descriptors) if context_descriptors else None
            ),
            project_id=project_id or "",
            task_id=task_id,
            target_tokens=target_tokens,
        )
    except Exception as e:
        logger.error(f"Invalid parameters for gc_analyze: {e}")
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
        # Get current segments from storage
        all_segments = app_state.storage.load_segments(params.project_id)
        working_segments = [s for s in all_segments if s.tier == "working"]

        # Compute root set from context descriptors
        roots: set[str] = set()

        if params.context_descriptors:
            # Add recent message segments to root set
            if params.context_descriptors.recent_messages and params.task_id:
                # In a real implementation, we'd track which segments correspond to messages
                # For now, we'll use all segments that match the task_id
                roots.update(
                    {
                        s.segment_id
                        for s in working_segments
                        if s.task_id == params.task_id and s.type == "message"
                    }
                )

            # Add current file segments to root set
            if params.context_descriptors.current_file:
                file_path = params.context_descriptors.current_file.path
                roots.update({s.segment_id for s in working_segments if s.file_path == file_path})

            # Add decision segments created recently
            recent_threshold = datetime.now() - timedelta(hours=1)
            roots.update(
                {
                    s.segment_id
                    for s in working_segments
                    if s.type == "decision" and s.created_at > recent_threshold
                }
            )

        # Call GC engine to analyze candidates
        pruning_candidates = app_state.gc_engine.analyze_pruning_candidates(working_segments, roots)

        # Calculate total tokens that could be freed
        estimated_tokens_freed = sum(c.tokens for c in pruning_candidates)

        # Generate pruning plan if target_tokens provided
        pruning_plan = None
        if params.target_tokens is not None:
            pruning_plan = app_state.gc_engine.generate_pruning_plan(
                pruning_candidates, params.target_tokens
            )

        # Format response
        result: dict[str, Any] = {
            "pruning_candidates": [c.model_dump() for c in pruning_candidates],
            "total_candidates": len(pruning_candidates),
            "estimated_tokens_freed": estimated_tokens_freed,
        }

        if pruning_plan:
            result["pruning_plan"] = pruning_plan.model_dump()

        return result
    except ValueError as e:
        logger.error(f"Value error in gc_analyze: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
                "details": {},
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in gc_analyze: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
                "details": {"exception": str(e)},
            }
        }
