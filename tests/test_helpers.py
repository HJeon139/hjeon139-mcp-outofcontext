"""Test helpers for FastMCP tools."""

from typing import Any
from unittest.mock import MagicMock

from fastmcp.server.context import Context

from hjeon139_mcp_outofcontext.app_state import AppState


def create_mock_context(app_state: AppState) -> Context:
    """Create a mock FastMCP context with app_state injected.

    Args:
        app_state: Application state to inject

    Returns:
        Mock Context object with app_state in state
    """
    mock_ctx = MagicMock(spec=Context)
    mock_ctx.get_state = MagicMock(return_value=app_state)
    return mock_ctx


async def call_tool_with_app_state(tool_func: Any, app_state: AppState, **kwargs: Any) -> Any:
    """Call a FastMCP tool function with app_state injected.

    Args:
        tool_func: The tool function to call (may be wrapped by @mcp.tool())
        app_state: Application state to inject
        **kwargs: Arguments to pass to the tool function

    Returns:
        Result from the tool function
    """
    mock_ctx = create_mock_context(app_state)
    # If the function is wrapped by FastMCP (FunctionTool), access the underlying function via .fn
    if hasattr(tool_func, "fn"):
        actual_func = tool_func.fn
    elif hasattr(tool_func, "__wrapped__"):
        actual_func = tool_func.__wrapped__
    else:
        actual_func = tool_func
    return await actual_func(**kwargs, ctx=mock_ctx)
