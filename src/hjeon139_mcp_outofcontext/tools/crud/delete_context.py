"""Tool handler for delete_context."""

import logging
from typing import Any

from ...app_state import AppState

logger = logging.getLogger(__name__)


async def handle_delete_context(
    app_state: AppState,
    name: str | list[str] | None = None,
    names: list[str] | None = None,
) -> dict[str, Any]:
    """
    Delete context by name (forced eviction by agent). Supports both single and bulk operations.

    Single: provide 'name' (str).
    Bulk: provide 'names' (list[str]) or 'name' as list[str].

    Args:
        app_state: Application state with all components
        name: Context name (single) or list of names (bulk)
        names: List of context names (bulk operation)

    Returns:
        Dictionary with deletion results
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
                storage.delete_context(name)
                return {
                    "success": True,
                    "operation": "single",
                    "name": name,
                }
        else:
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "Either 'name' or 'names' must be provided",
                }
            }

        # Bulk operation
        results = storage.delete_contexts(name_list)

        return {
            "success": True,
            "operation": "bulk",
            "count": len(name_list),
            "results": results,
        }

    except ValueError as e:
        logger.error(f"Value error in delete_context: {e}")
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": str(e),
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error in delete_context: {e}", exc_info=True)
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal error: {e!s}",
            }
        }
