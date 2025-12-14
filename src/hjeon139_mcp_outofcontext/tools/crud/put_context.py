"""Tool handler for put_context."""

import logging
from typing import Any

from ...app_state import AppState

logger = logging.getLogger(__name__)


async def handle_put_context(
    app_state: AppState,
    name: str | None = None,
    text: str | None = None,
    metadata: dict[str, Any] | None = None,
    contexts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Add or update context by name. Supports both single and bulk operations.

    Single operation: provide 'name' (str), 'text' (str, markdown content), optional 'metadata' (dict).
    Bulk operation: provide 'contexts' (list[dict]) where each dict has 'name', 'text', optional 'metadata'.

    Args:
        app_state: Application state with all components
        name: Context name (for single operation)
        text: Markdown content (for single operation)
        metadata: Optional metadata dict (for single operation)
        contexts: List of context dicts (for bulk operation)

    Returns:
        Dictionary with success status and results
    """
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
