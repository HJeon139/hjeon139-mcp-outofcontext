"""Tool handler for list_context."""

import logging
from typing import Any

from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context

from ...app_state import AppState
from ...fastmcp_server import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def list_context(
    limit: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    """List all contexts, sorted by creation date (newest first).

    Returns list of contexts with 'name', 'created_at', and 'preview' (first 100 chars).
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
