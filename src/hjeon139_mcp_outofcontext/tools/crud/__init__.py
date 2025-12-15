"""CRUD tools for context management."""

from ...app_state import AppState
from ...tool_registry import ToolRegistry
from .delete_context import handle_delete_context
from .get_context import handle_get_context
from .list_context import handle_list_context
from .models import (
    DeleteContextParams,
    GetContextParams,
    ListContextParams,
    PutContextParams,
    SearchContextParams,
)
from .put_context import handle_put_context
from .search_context import handle_search_context

__all__ = ["register_crud_tools", "register_tools"]


def register_crud_tools(registry: ToolRegistry, app_state: AppState) -> None:
    """Register all CRUD tools with the tool registry.

    Args:
        registry: Tool registry instance
        app_state: Application state (for dependency injection)
    """
    # Register put_context tool
    registry.register(
        name="put_context",
        handler=handle_put_context,
        description=(
            "Add or update context by name. Supports both single and bulk operations. "
            "Single: provide 'name' (str), 'text' (str, markdown content), and optional 'metadata' (dict). "
            "Bulk: provide 'contexts' (list[dict]) where each dict has 'name', 'text', optional 'metadata'. "
            "Names must be filename-safe (alphanumeric, hyphens, underscores). "
            "Overwrites existing contexts with a warning. "
            "Contexts are stored as .mdc files (markdown with YAML frontmatter)."
        ),
        params_model=PutContextParams,
    )

    # Register list_context tool
    registry.register(
        name="list_context",
        handler=handle_list_context,
        description=(
            "List all contexts, sorted by creation date (newest first). "
            "Returns list of contexts with 'name', 'created_at', and 'preview' (first 100 chars). "
            "Optional 'limit' parameter to limit number of results."
        ),
        params_model=ListContextParams,
    )

    # Register get_context tool
    registry.register(
        name="get_context",
        handler=handle_get_context,
        description=(
            "Get context by name. Supports both single and bulk operations. "
            "Single: provide 'name' (str). "
            "Bulk: provide 'names' (list[str]) or 'name' as list[str]. "
            "Returns context with 'text' (markdown body) and 'metadata' (from frontmatter). "
            "For bulk operations, returns list of results with errors for missing contexts."
        ),
        params_model=GetContextParams,
    )

    # Register search_context tool
    registry.register(
        name="search_context",
        handler=handle_search_context,
        description=(
            "Search contexts by query string. "
            "Searches in both YAML frontmatter (metadata) and markdown body (text content). "
            "Returns matching contexts with 'name', 'text', 'metadata', and 'matches' (where query was found). "
            "Optional 'limit' parameter to limit number of results."
        ),
        params_model=SearchContextParams,
    )

    # Register delete_context tool
    registry.register(
        name="delete_context",
        handler=handle_delete_context,
        description=(
            "Delete context by name (forced eviction by agent). Supports both single and bulk operations. "
            "Single: provide 'name' (str). "
            "Bulk: provide 'names' (list[str]) or 'name' as list[str]. "
            "For bulk operations, returns list of results with errors for missing contexts."
        ),
        params_model=DeleteContextParams,
    )


def register_tools() -> None:
    """Register all CRUD tools with FastMCP.

    Tools are registered via @mcp.tool() decorators when imported.
    This function ensures all tool modules are imported.
    """
    # Import all tool modules (decorators register tools on import)
    from . import fastmcp_tools  # noqa: F401
