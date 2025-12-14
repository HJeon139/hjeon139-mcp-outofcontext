"""Tool handler for list_context."""

import logging
from typing import Any

from ...app_state import AppState

logger = logging.getLogger(__name__)


async def handle_list_context(
    app_state: AppState,
    limit: int | None = None,
) -> dict[str, Any]:
    """
    List all contexts, sorted by creation date (newest first).

    Args:
        app_state: Application state with all components
        limit: Optional maximum number of results to return

    Returns:
        Dictionary with list of contexts
    """
    try:
        storage = app_state.storage
        contexts = storage.list_contexts()

        # Apply limit if provided
        if limit is not None and limit > 0:
            contexts = contexts[:limit]

        return {
            "success": True,
            "count": len(contexts),
            "contexts": contexts,
        }

    except Exception as e:
        logger.error(f"Unexpected error in list_context: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
            }
        }
