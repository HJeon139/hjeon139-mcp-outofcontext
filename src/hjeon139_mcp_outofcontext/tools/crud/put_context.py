"""Tool handler for put_context."""

import logging
from typing import Any

from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context

from ...app_state import AppState
from ...fastmcp_server import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def put_context(
    name: str | None = None,
    text: str | None = None,
    metadata: dict[str, Any] | None = None,
    contexts: list[dict[str, Any]] | None = None,
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    """Add or update context by name. Supports both single and bulk operations.

    Single: provide 'name' (str), 'text' (str, markdown content), and optional 'metadata' (dict).
    Bulk: provide 'contexts' (list[dict]) where each dict has 'name', 'text', optional 'metadata'.
    Names must be filename-safe (alphanumeric, hyphens, underscores).
    Overwrites existing contexts with a warning.
    Contexts are stored as .mdc files (markdown with YAML frontmatter).
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

        # Determine if single or bulk operation
        if contexts is not None:
            # Bulk operation
            if not isinstance(contexts, list):
                return {
                    "error": {
                        "code": "INVALID_PARAMETER",
                        "message": "'contexts' must be a list",
                    }
                }

            results = storage.save_contexts(contexts)
            return {
                "success": True,
                "operation": "bulk",
                "count": len(contexts),
                "results": results,
            }

        # Single operation
        if not name:
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "'name' is required for single operation",
                }
            }

        if text is None:
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "'text' is required for single operation",
                }
            }

        storage.save_context(name, text, metadata)
        return {
            "success": True,
            "operation": "single",
            "name": name,
        }

    except ValueError as e:
        logger.error(f"Value error in put_context: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in put_context: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
            }
        }
