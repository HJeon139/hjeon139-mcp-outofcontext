"""FastMCP server implementation with proper dependency injection.

Reference implementation for Phase 1 migration.
"""

from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.server.middleware import Middleware, MiddlewareContext

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.config import Config, load_config

# Create FastMCP instance
mcp = FastMCP("out-of-context")

# Application state (initialized at startup, accessed via middleware)
_app_state: AppState | None = None


def get_app_state() -> AppState:
    """Get application state instance (for initialization/testing).

    Note: Tools should use ctx.get_state("app_state") instead.

    Returns:
        AppState instance

    Raises:
        RuntimeError: If AppState is not initialized
    """
    if _app_state is None:
        raise RuntimeError("AppState not initialized. Call initialize_app_state() first.")
    return _app_state


def initialize_app_state(config: Config | None = None) -> None:
    """Initialize application state.

    Must be called before starting the server (in lifespan/startup).

    Args:
        config: Optional configuration. If None, loads from environment/files.
    """
    global _app_state
    if config is None:
        config = load_config()
    _app_state = AppState(config=config.to_dict())


class AppStateMiddleware(Middleware):
    """Middleware to inject AppState into request context.

    This ensures AppState is available in tools via ctx.get_state("app_state").
    Follows FastMCP best practices for dependency injection.
    """

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Inject AppState into context state before tool execution."""
        if _app_state is None:
            raise RuntimeError("AppState not initialized")
        context.set_state("app_state", _app_state)
        return await call_next(context)

    # Optionally handle resources and prompts similarly
    async def on_read_resource(self, context: MiddlewareContext, call_next):
        """Inject AppState for resource access."""
        if _app_state is None:
            raise RuntimeError("AppState not initialized")
        context.set_state("app_state", _app_state)
        return await call_next(context)


# Add middleware to inject AppState
mcp.add_middleware(AppStateMiddleware())

# Import and register tools (must be after mcp instance is created)
# Tools use @mcp.tool() decorator which registers them automatically
from hjeon139_mcp_outofcontext.tools.crud import register_tools  # noqa: E402

def register_all_tools() -> None:
    """Register all tools with FastMCP.

    This function is called to ensure all tools are registered.
    Tools are registered via @mcp.tool() decorators when modules are imported.
    """
    # Tools are registered via decorators, just need to import
    register_tools()
