"""Unit tests for tool registry."""

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
