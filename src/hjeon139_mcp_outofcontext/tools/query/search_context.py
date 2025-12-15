"""Tool handler for search_context."""

import logging
from typing import Any

from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context

from ...app_state import AppState
from ...fastmcp_server import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def search_context(
    query: str,
    limit: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    """Search contexts by query string.

    Searches in both YAML frontmatter (metadata) and markdown body (text content).
    Returns matching contexts with 'name', 'text', 'metadata', and 'matches' (where query was found).
    Optional 'limit' parameter to limit number of results.
    """
    # Get AppState from context (injected by middleware)
    app_state: AppState = ctx.get_state("app_state")
    if app_state is None:
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "AppState not available in context",
            }
        }

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
