"""Tool handler for search_context."""

import logging
from typing import Any

from ...app_state import AppState

logger = logging.getLogger(__name__)


async def handle_search_context(
    app_state: AppState,
    query: str,
    limit: int | None = None,
) -> dict[str, Any]:
    """
    Search contexts by query string.

    Args:
        app_state: Application state with all components
        query: Search query string
        limit: Optional maximum number of results to return

    Returns:
        Dictionary with matching contexts
    """
    try:
        if not query:
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "'query' is required",
                }
            }

        storage = app_state.storage
        matches = storage.search_contexts(query)

        # Apply limit if provided
        if limit is not None and limit > 0:
            matches = matches[:limit]

        return {
            "success": True,
            "query": query,
            "count": len(matches),
            "matches": matches,
        }

    except Exception as e:
        logger.error(f"Unexpected error in search_context: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
            }
        }
