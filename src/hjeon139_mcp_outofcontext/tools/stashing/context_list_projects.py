"""Tool handler for context_list_projects."""

import logging
from typing import Any

from ...app_state import AppState

logger = logging.getLogger(__name__)


async def handle_list_projects(
    app_state: AppState,
) -> dict[str, Any]:
    """
    List all available project IDs from stashed storage.

    This tool discovers all project IDs that have stashed context segments.
    Use this tool to find available projects when you don't know the project_id
    or need to search across multiple projects.

    Args:
        app_state: Application state with all components

    Returns:
        Dictionary with:
        - projects: List[str] (list of project IDs)
        - count: int (number of projects)
    """
    try:
        project_ids = app_state.storage.list_projects()

        return {
            "projects": project_ids,
            "count": len(project_ids),
        }
    except Exception as e:
        logger.error(f"Unexpected error in context_list_projects: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
                "details": {"exception": str(e)},
            }
        }
