"""FastMCP tool implementation example.

Reference implementation showing how to convert existing tool handlers.
"""

from typing import Any

from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context

from hjeon139_mcp_outofcontext.fastmcp_server import mcp  # Import mcp instance to use decorator
from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.tools.crud.put_context import handle_put_context


@mcp.tool()
async def put_context(
    name: str | None = None,
    text: str | None = None,
    metadata: dict[str, Any] | None = None,
    contexts: list[dict[str, Any]] | None = None,
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    """Add or update context by name. Supports both single and bulk operations.

    Single operation: provide 'name' (str), 'text' (str, markdown content),
    and optional 'metadata' (dict). Bulk operation: provide 'contexts' (list[dict])
    where each dict has 'name', 'text', optional 'metadata'.
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
