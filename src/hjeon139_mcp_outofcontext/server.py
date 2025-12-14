"""MCP server with dependency injection and lifecycle management."""

import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.config import Config, load_config
from hjeon139_mcp_outofcontext.tool_registry import ToolRegistry
from hjeon139_mcp_outofcontext.tools.crud import register_crud_tools

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP server with dependency injection and lifecycle management.

    Follows best practices:
    - NO global variables - all state is instance-scoped
    - AppState holds all components (initialized in __init__)
    - Lifecycle management via async context manager
    - Tool registry with dependency injection
    """

    def __init__(self, config: Config | dict[str, Any] | None = None) -> None:
        """
        Initialize MCP server.

        Args:
            config: Optional configuration (Config instance or dict)
        """
        # Convert dict to Config if needed
        if isinstance(config, dict):
            self.config = config
        elif isinstance(config, Config):
            self.config = config.to_dict()
        else:
            # Load from environment/files
            loaded_config = load_config()
            self.config = loaded_config.to_dict()

        # Create AppState instance (not global)
        self.app_state = AppState(config=self.config)
        # Create tool registry
        self.tool_registry = ToolRegistry()
        # Register all tools
        self._register_tools()
        # Create MCP Server instance
        self.mcp_server = Server("out-of-context")
        self._running = False
        # Register MCP handlers
        self._register_mcp_handlers()

    @asynccontextmanager
    async def lifespan(self) -> Any:
        """
        Lifespan context manager for startup/shutdown.

        Usage:
            async with server.lifespan():
                # Server running
                pass
        """
        self._running = True
        try:
            async with self.app_state.lifespan():
                yield
        finally:
            self._running = False

    async def run(self) -> None:
        """
        Run the MCP server with stdio transport.

        This starts the MCP server and handles tool calls via stdio.
        """
        async with (
            self.lifespan(),
            stdio_server() as (
                read_stream,
                write_stream,
            ),
        ):
            await self.mcp_server.run(
                read_stream,
                write_stream,
                self.mcp_server.create_initialization_options(),
            )

    def get_app_state(self) -> AppState:
        """
        Get application state instance.

        Returns:
            AppState instance
        """
        return self.app_state

    def get_tool_registry(self) -> ToolRegistry:
        """
        Get tool registry instance.

        Returns:
            ToolRegistry instance
        """
        return self.tool_registry

    def _register_tools(self) -> None:
        """
        Register all tools with the tool registry.

        Called during initialization to register all available tools.
        """
        # Register CRUD tools
        register_crud_tools(self.tool_registry, self.app_state)

    def _register_mcp_handlers(self) -> None:
        """
        Register MCP protocol handlers for tool discovery and execution.

        This registers handlers for:
        - tools/list: List all available tools
        - tools/call: Execute a tool call
        """

        # Register tools/list handler
        @self.mcp_server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools."""
            tools = []
            for tool_handler in self.tool_registry.list_tools():
                # Convert tool handler to MCP Tool format
                # Note: We need to extract input schema from tool handlers
                # For now, we'll create a basic tool definition
                tools.append(
                    Tool(
                        name=tool_handler.name,
                        description=tool_handler.description,
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    )
                )
            return tools

        # Register tools/call handler
        @self.mcp_server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
            """Handle tool call."""
            try:
                # Validate tool exists
                registered_tools = self.tool_registry.list_tools()
                tool_names = {tool.name for tool in registered_tools}
                if name not in tool_names:
                    error = ValueError(f"Tool '{name}' is not registered")
                    error_msg = self._format_error(error)
                    return [TextContent(type="text", text=error_msg)]

                # Dispatch to tool handler
                result = await self.tool_registry.dispatch(
                    name,
                    arguments or {},
                    self.app_state,
                )

                # Format response in MCP format
                response_text = json.dumps(result, default=str)
                return [TextContent(type="text", text=response_text)]

            except Exception as e:
                logger.exception(f"Error handling tool call '{name}': {e}")
                error_msg = self._format_error(e)
                return [TextContent(type="text", text=error_msg)]

    def _format_error(self, error: Exception) -> str:
        """
        Format error in MCP-compatible format.

        Args:
            error: Exception to format

        Returns:
            JSON string with error information
        """
        error_dict = {
            "error": {
                "code": type(error).__name__,
                "message": str(error),
            }
        }
        return json.dumps(error_dict)


async def create_server(
    config: Config | dict[str, Any] | None = None,
) -> MCPServer:
    """
    Create MCP server instance.

    Args:
        config: Optional configuration (Config instance or dict)

    Returns:
        MCPServer instance (components initialized in __init__)
    """
    return MCPServer(config=config)
