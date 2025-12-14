"""Tool registry for MCP tool registration and dispatch with dependency injection."""

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel

from hjeon139_mcp_outofcontext.app_state import AppState

logger = logging.getLogger(__name__)


class ToolHandler:
    """
    Tool handler with dependency injection support.

    Handlers receive AppState as a dependency, not global state.
    """

    def __init__(
        self,
        name: str,
        handler: Callable[..., Awaitable[Any]],
        description: str,
        params_model: type[BaseModel] | None = None,
    ) -> None:
        """
        Initialize tool handler.

        Args:
            name: Tool name
            handler: Async handler function that receives app_state as first arg
            description: Tool description
            params_model: Optional Pydantic model for parameter validation
        """
        self.name = name
        self.handler = handler
        self.description = description
        self.params_model = params_model


class ToolRegistry:
    """
    Registry for MCP tools with dependency injection.

    Maintains a registry of tool name -> handler mappings.
    Provides registration and dispatch functions.
    """

    def __init__(self) -> None:
        """Initialize empty tool registry."""
        self._tools: dict[str, ToolHandler] = {}

    def register(
        self,
        name: str,
        handler: Callable[..., Awaitable[Any]],
        description: str,
        params_model: type[BaseModel] | None = None,
    ) -> None:
        """
        Register a tool with the registry.

        Args:
            name: Tool name (must be unique)
            handler: Async handler function that receives app_state as first arg
            description: Tool description
            params_model: Optional Pydantic model for parameter validation and schema generation

        Raises:
            ValueError: If tool name is already registered
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")

        self._tools[name] = ToolHandler(name, handler, description, params_model)

    async def dispatch(self, name: str, arguments: dict[str, Any], app_state: AppState) -> Any:
        """
        Dispatch tool call to registered handler.

        Args:
            name: Tool name
            arguments: Tool arguments
            app_state: Application state for dependency injection

        Returns:
            Tool result

        Raises:
            ValueError: If tool is not registered
        """
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' is not registered")

        tool = self._tools[name]

        # Validate arguments using Pydantic model if available
        if tool.params_model:
            try:
                # Handle case where arguments might contain JSON strings
                # (can happen with complex nested structures through MCP protocol)
                processed_arguments = self._process_arguments(arguments)
                logger.debug(f"Processed arguments for '{name}': {processed_arguments}")
                validated_params = tool.params_model.model_validate(processed_arguments)
                # Convert validated model to dict for **kwargs
                # Use mode='python' to ensure nested models are converted to dicts
                arguments = validated_params.model_dump(mode="python", exclude_none=False)
            except Exception as e:
                logger.error(f"Parameter validation failed for tool '{name}': {e}")
                logger.error(f"Arguments received: {arguments}")
                logger.error(f"Arguments type: {type(arguments)}")
                # Return validation error with more details
                error_msg = str(e)
                # Try to extract more useful error information
                if hasattr(e, "errors"):
                    error_details = e.errors()
                    if error_details:
                        error_msg = f"Validation errors: {error_details}"
                return {
                    "error": {
                        "code": "INVALID_PARAMETER",
                        "message": f"Parameter validation failed: {error_msg}",
                    }
                }

        # Call handler with app_state as first argument (dependency injection)
        result = await tool.handler(app_state, **arguments)
        return result

    def list_tools(self) -> list[ToolHandler]:
        """
        List all registered tools.

        Returns:
            List of tool handlers
        """
        return list(self._tools.values())

    def get_tool(self, name: str) -> ToolHandler | None:
        """
        Get tool handler by name.

        Args:
            name: Tool name

        Returns:
            Tool handler or None if not found
        """
        return self._tools.get(name)

    def _process_arguments(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Process arguments to handle JSON string values.

        Some MCP clients may serialize complex nested structures as JSON strings.
        This method recursively parses JSON strings back to their original types.

        Args:
            arguments: Raw arguments dict

        Returns:
            Processed arguments dict with JSON strings parsed
        """
        processed: dict[str, Any] = {}
        for key, value in arguments.items():
            processed[key] = self._process_value(value)

        return processed

    def _process_value(self, value: Any) -> Any:
        """
        Recursively process a value, parsing JSON strings if needed.

        Some MCP clients may serialize complex nested structures as JSON strings
        or even Python repr() strings. This method handles both cases.

        Args:
            value: Value to process

        Returns:
            Processed value
        """
        if isinstance(value, str):
            # Try to parse as JSON if it looks like JSON (starts with [ or {)
            if value.strip().startswith(("[", "{")):
                try:
                    parsed = json.loads(value)
                    # Recursively process the parsed value
                    return self._process_value(parsed)
                except (json.JSONDecodeError, ValueError):
                    # Not valid JSON, might be Python repr() string
                    # Try to evaluate it safely (only for list/dict structures)
                    if value.strip().startswith("[") or value.strip().startswith("{"):
                        try:
                            # Use ast.literal_eval for safe evaluation of Python literals
                            import ast

                            parsed = ast.literal_eval(value)
                            # Recursively process the parsed value
                            return self._process_value(parsed)
                        except (ValueError, SyntaxError):
                            # Not a valid Python literal either, keep as string
                            logger.warning(
                                f"Could not parse string value as JSON or Python literal: {value[:100]}"
                            )
                            return value
                    return value
            return value
        elif isinstance(value, list):
            # Recursively process list items
            return [self._process_value(item) for item in value]
        elif isinstance(value, dict):
            # Recursively process nested dicts
            return self._process_arguments(value)
        else:
            return value
