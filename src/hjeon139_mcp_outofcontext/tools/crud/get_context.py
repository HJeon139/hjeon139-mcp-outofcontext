"""Tool handler for get_context."""

import logging
from typing import Any

from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context

from ...app_state import AppState
from ...fastmcp_server import mcp

logger = logging.getLogger(__name__)


def _process_bulk_get_results(
    name_list: list[str], results: list[dict[str, Any] | None]
) -> list[dict[str, Any]]:
    """Process bulk get operation results.

    Args:
        name_list: List of context names requested
        results: List of context results (can be None if not found)

    Returns:
        List of processed context results with success/error status
    """
    contexts: list[dict[str, Any]] = []
    for i, result in enumerate(results):
        if result is None:
            contexts.append(
                {
                    "name": name_list[i],
                    "success": False,
                    "error": "Context not found",
                }
            )
        else:
            contexts.append(
                {
                    "name": name_list[i],
                    "success": True,
                    "text": result.get("text", ""),
                    "metadata": result.get("metadata", {}),
                }
            )
    return contexts


@mcp.tool()
async def get_context(
    name: str | list[str] | None = None,
    names: list[str] | None = None,
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    """Get context by name. Supports both single and bulk operations.

    Single: provide 'name' (str).
    Bulk: provide 'names' (list[str]) or 'name' as list[str].
    Returns context with 'text' (markdown body) and 'metadata' (from frontmatter).
    For bulk operations, returns list of results with errors for missing contexts.
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
        # Check 'names' first, then 'name' (can be str or list)
        if names is not None:
            # Bulk operation via 'names'
            if not isinstance(names, list):
                return {
                    "error": {
                        "code": "INVALID_PARAMETER",
                        "message": "'names' must be a list",
                    }
                }
            name_list = names
        elif name is not None:
            if isinstance(name, list):
                # Bulk operation via 'name' as list
                name_list = name
            else:
                # Single operation
                result = storage.load_context(name)
                if result is None:
                    return {
                        "error": {
                            "code": "NOT_FOUND",
                            "message": f"Context '{name}' not found",
                        }
                    }
                return {
                    "success": True,
                    "operation": "single",
                    "name": name,
                    "text": result.get("text", ""),
                    "metadata": result.get("metadata", {}),
                }
        else:
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "Either 'name' or 'names' must be provided",
                }
            }

        # Bulk operation
        results = storage.load_contexts(name_list)
        contexts = _process_bulk_get_results(name_list, results)

        return {
            "success": True,
            "operation": "bulk",
            "count": len(name_list),
            "contexts": contexts,
        }

    except ValueError as e:
        logger.error(f"Value error in get_context: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_context: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
            }
        }
