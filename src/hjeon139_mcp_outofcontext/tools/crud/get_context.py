"""Tool handler for get_context."""

import logging
from typing import Any

from ...app_state import AppState

logger = logging.getLogger(__name__)


async def handle_get_context(
    app_state: AppState,
    name: str | list[str] | None = None,
    names: list[str] | None = None,
) -> dict[str, Any]:
    """
    Get context by name. Supports both single and bulk operations.

    Single: provide 'name' (str).
    Bulk: provide 'names' (list[str]) or 'name' as list[str].

    Args:
        app_state: Application state with all components
        name: Context name (single) or list of names (bulk)
        names: List of context names (bulk operation)

    Returns:
        Dictionary with context data
    """
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
