"""FastMCP tool wrappers for CRUD operations."""

from typing import Any

from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.fastmcp_server import mcp
from hjeon139_mcp_outofcontext.tools.crud.delete_context import handle_delete_context
from hjeon139_mcp_outofcontext.tools.crud.get_context import handle_get_context
from hjeon139_mcp_outofcontext.tools.crud.list_context import handle_list_context
from hjeon139_mcp_outofcontext.tools.crud.put_context import handle_put_context
from hjeon139_mcp_outofcontext.tools.crud.search_context import handle_search_context


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

    # Call existing handler (maintains existing logic)
    return await handle_put_context(
        app_state,
        name=name,
        text=text,
        metadata=metadata,
        contexts=contexts,
    )


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

    # Call existing handler (maintains existing logic)
    return await handle_get_context(app_state, name=name, names=names)


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

    # Call existing handler (maintains existing logic)
    return await handle_list_context(app_state, limit=limit)


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

    # Call existing handler (maintains existing logic)
    return await handle_search_context(app_state, query=query, limit=limit)


@mcp.tool()
async def delete_context(
    name: str | list[str] | None = None,
    names: list[str] | None = None,
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    """Delete context by name (forced eviction by agent). Supports both single and bulk operations.

    Single: provide 'name' (str).
    Bulk: provide 'names' (list[str]) or 'name' as list[str].
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

    # Call existing handler (maintains existing logic)
    return await handle_delete_context(app_state, name=name, names=names)
