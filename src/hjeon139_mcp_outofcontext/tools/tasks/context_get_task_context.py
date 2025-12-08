"""Tool handler for context_get_task_context."""

import logging
from typing import Any

from ...app_state import AppState
from ...models import GetTaskContextParams

logger = logging.getLogger(__name__)


async def handle_get_task_context(
    app_state: AppState,
    project_id: str | None = None,
    task_id: str | None = None,
) -> dict[str, Any]:
    """
    Get all context segments for a specific task.

    This tool returns all context segments (from all tiers) that belong to
    a specific task. If task_id is not provided, it uses the current task
    for the project.

    Args:
        app_state: Application state with all components
        project_id: Project identifier (required)
        task_id: Optional task identifier (None uses current task)

    Returns:
        Dictionary with:
        - task_id: str
        - segments: List[ContextSegment]
        - total_tokens: int
        - segment_count: int
        - active: bool (Is this the current task?)

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate and parse parameters
    try:
        params = GetTaskContextParams(
            project_id=project_id or "",
            task_id=task_id,
        )
    except Exception as e:
        logger.error(f"Invalid parameters for context_get_task_context: {e}")
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
        # Call context manager to get task context
        result = app_state.context_manager.get_task_context(
            project_id=params.project_id,
            task_id=params.task_id,
        )

        # Format response
        return {
            "task_id": result["task_id"],
            "segments": [segment.model_dump() for segment in result["segments"]],
            "total_tokens": result["total_tokens"],
            "segment_count": result["segment_count"],
            "active": result["active"],
        }
    except ValueError as e:
        logger.error(f"Value error in context_get_task_context: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
                "details": {},
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in context_get_task_context: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
                "details": {"exception": str(e)},
            }
        }
