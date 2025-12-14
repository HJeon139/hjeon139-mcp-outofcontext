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
                # Generate input schema from Pydantic model if available
                if tool_handler.params_model:
                    schema = tool_handler.params_model.model_json_schema()
                    # Resolve $ref references to inline definitions for MCP compatibility
                    schema = self._resolve_schema_refs(schema)
                    # Simplify schema for better MCP client compatibility
                    schema = self._simplify_schema(schema)
                    # Remove title and other metadata that MCP doesn't need
                    schema.pop("title", None)
                    # Ensure required fields are properly set
                    required = schema.get("required", [])
                    if not required:
                        schema.pop("required", None)
                else:
                    # Fallback to empty schema
                    schema = {
                        "type": "object",
                        "properties": {},
                    }

                tools.append(
                    Tool(
                        name=tool_handler.name,
                        description=tool_handler.description,
                        inputSchema=schema,
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

    def _resolve_schema_refs(self, schema: dict[str, Any]) -> dict[str, Any]:
        """
        Resolve $ref references in JSON schema to inline definitions.

        MCP clients may not properly resolve $ref references, so we inline
        the definitions directly into the schema.

        Args:
            schema: JSON schema with potential $ref references

        Returns:
            Schema with $ref references resolved to inline definitions
        """
        if not isinstance(schema, dict):
            return schema

        # Get definitions if they exist
        defs = schema.get("$defs", {})

        # Recursively resolve references
        def resolve_value(value: Any) -> Any:
            if isinstance(value, dict):
                # Check if this is a $ref
                if "$ref" in value:
                    ref_path = value["$ref"]
                    # Handle #/$defs/ModelName format
                    if ref_path.startswith("#/$defs/"):
                        def_name = ref_path.replace("#/$defs/", "")
                        if def_name in defs:
                            # Resolve the referenced definition
                            resolved = defs[def_name].copy()
                            # Recursively resolve any nested refs
                            return resolve_value(resolved)
                    return value
                else:
                    # Recursively process dict
                    return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                # Recursively process list items
                return [resolve_value(item) for item in value]
            else:
                return value

        # Resolve the schema
        resolved = resolve_value(schema)
        # Remove $defs since we've inlined everything
        if isinstance(resolved, dict):
            resolved.pop("$defs", None)

        return resolved

    def _simplify_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """
        Simplify schema for better MCP client compatibility.

        Some MCP clients have issues with anyOf/oneOf structures.
        This method simplifies nullable types by making them optional instead.

        Args:
            schema: JSON schema to simplify

        Returns:
            Simplified schema
        """
        if not isinstance(schema, dict):
            return schema

        simplified: dict[str, Any] = {}
        for key, value in schema.items():
            if key == "properties" and isinstance(value, dict):
                # Simplify properties
                simplified_props: dict[str, Any] = {}
                for prop_name, prop_schema in value.items():
                    simplified_props[prop_name] = self._simplify_property(prop_schema)
                simplified[key] = simplified_props
            elif key == "$defs":
                # Keep $defs but simplify them too
                simplified[key] = {k: self._simplify_schema(v) for k, v in value.items()}
            else:
                simplified[key] = value

        return simplified

    def _simplify_property(self, prop: Any) -> Any:
        """
        Simplify a property schema, handling anyOf for nullable types.

        Args:
            prop: Property schema

        Returns:
            Simplified property schema
        """
        if not isinstance(prop, dict):
            return prop

        # If it's an anyOf with string/null or object/null, simplify it
        if "anyOf" in prop:
            any_of = prop["anyOf"]
            if len(any_of) == 2:
                # Check if one is null and the other is a concrete type
                types = [item.get("type") for item in any_of if isinstance(item, dict)]
                if "null" in types:
                    # Find the non-null type
                    non_null = next((item for item in any_of if item.get("type") != "null"), None)
                    if non_null:
                        # Make it optional (remove required constraint) instead of nullable
                        simplified = non_null.copy()
                        # Keep description and other metadata
                        if "description" in prop:
                            simplified["description"] = prop["description"]
                        # Remove title to keep schema clean
                        simplified.pop("title", None)
                        return simplified

        # Recursively simplify nested structures
        if "items" in prop:
            prop["items"] = self._simplify_property(prop["items"])
        if "properties" in prop:
            prop["properties"] = {
                k: self._simplify_property(v) for k, v in prop["properties"].items()
            }

        return prop


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
