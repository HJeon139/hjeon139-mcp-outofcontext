"""Unit tests for tool registry."""

import json

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.tool_registry import ToolRegistry


@pytest.mark.unit
class TestToolRegistry:
    """Test ToolRegistry class."""

    def test_register_tool(self) -> None:
        """Test tool registration."""
        registry = ToolRegistry()

        async def dummy_handler(app_state: AppState, **kwargs: dict) -> dict:
            return {"result": "success"}

        registry.register(
            name="test_tool",
            handler=dummy_handler,
            description="A test tool",
        )

        assert registry.get_tool("test_tool") is not None
        assert registry.get_tool("test_tool").name == "test_tool"
        assert registry.get_tool("test_tool").description == "A test tool"

    def test_register_duplicate_tool(self) -> None:
        """Test that registering duplicate tool raises error."""
        registry = ToolRegistry()

        async def dummy_handler(app_state: AppState, **kwargs: dict) -> dict:
            return {"result": "success"}

        registry.register(
            name="test_tool",
            handler=dummy_handler,
            description="A test tool",
        )

        with pytest.raises(ValueError, match="already registered"):
            registry.register(
                name="test_tool",
                handler=dummy_handler,
                description="Another tool",
            )

    @pytest.mark.asyncio
    async def test_dispatch_tool(self) -> None:
        """Test tool dispatch with dependency injection."""
        registry = ToolRegistry()
        app_state = AppState()

        async def echo_handler(app_state: AppState, message: str = "") -> dict:
            return {"echo": message}

        registry.register(
            name="echo",
            handler=echo_handler,
            description="Echo tool",
        )

        result = await registry.dispatch("echo", {"message": "hello"}, app_state)
        assert result == {"echo": "hello"}

    @pytest.mark.asyncio
    async def test_dispatch_nonexistent_tool(self) -> None:
        """Test that dispatching nonexistent tool raises error."""
        registry = ToolRegistry()
        app_state = AppState()

        with pytest.raises(ValueError, match="not registered"):
            await registry.dispatch("nonexistent", {}, app_state)

    def test_list_tools(self) -> None:
        """Test listing registered tools."""
        registry = ToolRegistry()

        async def handler1(app_state: AppState, **kwargs: dict) -> dict:
            return {}

        async def handler2(app_state: AppState, **kwargs: dict) -> dict:
            return {}

        registry.register("tool1", handler1, "First tool")
        registry.register("tool2", handler2, "Second tool")

        tools = registry.list_tools()
        assert len(tools) == 2
        tool_names = {tool.name for tool in tools}
        assert tool_names == {"tool1", "tool2"}

    def test_get_tool_nonexistent(self) -> None:
        """Test getting nonexistent tool returns None."""
        registry = ToolRegistry()
        assert registry.get_tool("nonexistent") is None


@pytest.mark.unit
class TestToolRegistryDependencyInjection:
    """Test tool registry dependency injection pattern."""

    @pytest.mark.asyncio
    async def test_handler_receives_app_state(self) -> None:
        """Test that handlers receive app_state via dependency injection."""
        registry = ToolRegistry()
        app_state = AppState(config={"test": "value"})

        async def state_handler(app_state: AppState, **kwargs: dict) -> dict:
            return {"config": app_state.config}

        registry.register(
            name="get_config",
            handler=state_handler,
            description="Get config",
        )

        result = await registry.dispatch("get_config", {}, app_state)
        assert result["config"] == {"test": "value"}

    @pytest.mark.asyncio
    async def test_multiple_handlers_isolated_state(self) -> None:
        """Test that handlers don't share state incorrectly."""
        registry = ToolRegistry()
        app_state1 = AppState(config={"app": "1"})
        app_state2 = AppState(config={"app": "2"})

        async def get_app_handler(app_state: AppState, **kwargs: dict) -> dict:
            return {"app": app_state.config.get("app")}

        registry.register("get_app", get_app_handler, "Get app")

        result1 = await registry.dispatch("get_app", {}, app_state1)
        result2 = await registry.dispatch("get_app", {}, app_state2)

        assert result1["app"] == "1"
        assert result2["app"] == "2"


@pytest.mark.unit
class TestToolRegistryParameterProcessing:
    """Test tool registry parameter processing (JSON strings, Python repr, etc.)."""

    def test_process_json_string_argument(self) -> None:
        """Test processing JSON string arguments."""
        registry = ToolRegistry()

        # Test JSON string for contexts
        arguments = {
            "contexts": '[{"name": "test-1", "text": "Content 1", "metadata": {"type": "test"}}]'
        }

        processed = registry._process_arguments(arguments)
        assert isinstance(processed["contexts"], list)
        assert len(processed["contexts"]) == 1
        assert processed["contexts"][0]["name"] == "test-1"
        assert processed["contexts"][0]["text"] == "Content 1"
        assert processed["contexts"][0]["metadata"] == {"type": "test"}

    def test_process_python_repr_string_argument(self) -> None:
        """Test processing Python repr() string arguments."""
        registry = ToolRegistry()

        # Test Python repr string for contexts
        contexts_list = [
            {"name": "test-1", "text": "Content 1", "metadata": {"type": "test"}},
            {"name": "test-2", "text": "Content 2"},
        ]
        contexts_repr = repr(contexts_list)

        arguments = {"contexts": contexts_repr}

        processed = registry._process_arguments(arguments)
        assert isinstance(processed["contexts"], list)
        assert len(processed["contexts"]) == 2
        assert processed["contexts"][0]["name"] == "test-1"
        assert processed["contexts"][1]["name"] == "test-2"

    def test_process_nested_json_strings(self) -> None:
        """Test processing nested JSON strings."""
        registry = ToolRegistry()

        # Test nested structure with JSON strings
        arguments = {
            "contexts": json.dumps(
                [{"name": "test-1", "text": "Content 1", "metadata": json.dumps({"type": "test"})}]
            )
        }

        processed = registry._process_arguments(arguments)
        assert isinstance(processed["contexts"], list)
        # The nested metadata JSON string should also be parsed
        assert isinstance(processed["contexts"][0]["metadata"], dict)
        assert processed["contexts"][0]["metadata"]["type"] == "test"

    def test_process_regular_list_argument(self) -> None:
        """Test that regular list arguments pass through unchanged."""
        registry = ToolRegistry()

        arguments = {
            "contexts": [
                {"name": "test-1", "text": "Content 1"},
                {"name": "test-2", "text": "Content 2"},
            ]
        }

        processed = registry._process_arguments(arguments)
        assert isinstance(processed["contexts"], list)
        assert len(processed["contexts"]) == 2
        assert processed["contexts"][0]["name"] == "test-1"

    def test_process_non_json_string(self) -> None:
        """Test that non-JSON strings are left as-is."""
        registry = ToolRegistry()

        arguments = {"name": "regular-string", "text": "This is not JSON"}

        processed = registry._process_arguments(arguments)
        assert processed["name"] == "regular-string"
        assert processed["text"] == "This is not JSON"

    @pytest.mark.asyncio
    async def test_dispatch_with_json_string_contexts(self) -> None:
        """Test dispatch with JSON string contexts parameter."""
        from hjeon139_mcp_outofcontext.tools.crud.models import PutContextParams

        registry = ToolRegistry()
        app_state = AppState()

        async def test_handler(app_state: AppState, **kwargs: dict) -> dict:
            return {"received": kwargs}

        registry.register(
            name="test_tool",
            handler=test_handler,
            description="Test tool",
            params_model=PutContextParams,
        )

        # Dispatch with JSON string
        arguments = {"contexts": '[{"name": "test-1", "text": "Content 1"}]'}

        result = await registry.dispatch("test_tool", arguments, app_state)
        # Should succeed and convert JSON string to list
        assert "error" not in result
        assert "received" in result
        assert isinstance(result["received"]["contexts"], list)
        assert len(result["received"]["contexts"]) == 1
