"""Tool handler for context_set_current_task."""

import logging
from typing import Any

from ...app_state import AppState
from ...models import SetCurrentTaskParams

logger = logging.getLogger(__name__)


async def handle_set_current_task(
    app_state: AppState,
    project_id: str | None = None,
    task_id: str | None = None,
) -> dict[str, Any]:
    """
    Set the active task ID for a project, updating the working set.

    This tool sets the current task for a project and automatically updates
    the working set to include only segments for that task. Setting task_id
    to None clears the current task.

    Args:
        app_state: Application state with all components
        project_id: Project identifier (required)
        task_id: Optional task identifier (None to clear current task)

    Returns:
        Dictionary with:
        - previous_task_id: Optional[str]
        - current_task_id: Optional[str]
        - working_set_updated: bool

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate and parse parameters
    try:
        params = SetCurrentTaskParams(
            project_id=project_id or "",
            task_id=task_id,
        )
    except Exception as e:
        logger.error(f"Invalid parameters for context_set_current_task: {e}")
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
        # Call context manager to set current task
        result = app_state.context_manager.set_current_task(
            project_id=params.project_id,
            task_id=params.task_id,
        )

        # Format response
        return {
            "previous_task_id": result["previous_task_id"],
            "current_task_id": result["current_task_id"],
            "working_set_updated": result["working_set_updated"],
        }
    except ValueError as e:
        logger.error(f"Value error in context_set_current_task: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
                "details": {},
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in context_set_current_task: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
                "details": {"exception": str(e)},
            }
        }
