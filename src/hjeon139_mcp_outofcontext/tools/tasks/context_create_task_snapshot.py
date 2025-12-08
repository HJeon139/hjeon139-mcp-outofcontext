"""Tool handler for context_create_task_snapshot."""

import logging
from typing import Any

from ...app_state import AppState
from ...models import CreateTaskSnapshotParams

logger = logging.getLogger(__name__)


async def handle_create_task_snapshot(
    app_state: AppState,
    project_id: str | None = None,
    task_id: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    """
    Create a snapshot of current task state for later retrieval.

    This tool creates a snapshot of all segments belonging to a task. The
    snapshot is stored in stashed storage with special tags that allow it to
    be retrieved later. Snapshots preserve the state of a task before
    switching to another task or performing major context cleanup.

    Args:
        app_state: Application state with all components
        project_id: Project identifier (required)
        task_id: Optional task identifier (None uses current task)
        name: Optional snapshot name

    Returns:
        Dictionary with:
        - snapshot_id: str
        - task_id: str
        - segments_captured: int
        - tokens_captured: int
        - created_at: str (ISO datetime)

    Raises:
        ValueError: If parameters are invalid or no task is set
    """
    # Validate and parse parameters
    try:
        params = CreateTaskSnapshotParams(
            project_id=project_id or "",
            task_id=task_id,
            name=name,
        )
    except Exception as e:
        logger.error(f"Invalid parameters for context_create_task_snapshot: {e}")
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
        # Call context manager to create task snapshot
        result = app_state.context_manager.create_task_snapshot(
            project_id=params.project_id,
            task_id=params.task_id,
            name=params.name,
        )

        # Format response
        return {
            "snapshot_id": result["snapshot_id"],
            "task_id": result["task_id"],
            "segments_captured": result["segments_captured"],
            "tokens_captured": result["tokens_captured"],
            "created_at": result["created_at"],
        }
    except ValueError as e:
        logger.error(f"Value error in context_create_task_snapshot: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
                "details": {},
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in context_create_task_snapshot: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
                "details": {"exception": str(e)},
            }
        }
