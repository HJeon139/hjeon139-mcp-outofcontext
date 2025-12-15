"""Tests for FastMCP server implementation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.config import Config
from hjeon139_mcp_outofcontext.fastmcp_server import (
    AppStateMiddleware,
    get_app_state,
    initialize_app_state,
    mcp,
)


@pytest.mark.unit
class TestAppStateInitialization:
    """Test AppState initialization functions."""

    def test_get_app_state_not_initialized(self) -> None:
        """Test get_app_state raises when not initialized."""
        # Reset state
        from hjeon139_mcp_outofcontext import fastmcp_server

        fastmcp_server._app_state = None

        with pytest.raises(RuntimeError, match="AppState not initialized"):
            get_app_state()

    def test_initialize_app_state_with_config(self, tmp_path) -> None:
        """Test initialize_app_state with config."""
        test_path = str(tmp_path / "test_storage")
        config = Config(storage_path=test_path, log_level="INFO")
        initialize_app_state(config)

        app_state = get_app_state()
        assert isinstance(app_state, AppState)
        assert app_state.config["storage_path"] == test_path

    def test_initialize_app_state_without_config(self, tmp_path) -> None:
        """Test initialize_app_state loads config when None."""
        test_path = str(tmp_path / "default_storage")
        with patch("hjeon139_mcp_outofcontext.fastmcp_server.load_config") as mock_load:
            mock_config = Config(storage_path=test_path, log_level="INFO")
            mock_load.return_value = mock_config

            initialize_app_state(None)

            app_state = get_app_state()
            assert isinstance(app_state, AppState)
            mock_load.assert_called_once()


@pytest.mark.unit
class TestAppStateMiddleware:
    """Test AppStateMiddleware."""

    @pytest.mark.asyncio
    async def test_middleware_injects_app_state_on_call_tool(self, tmp_path) -> None:
        """Test middleware injects AppState on tool call."""
        # Initialize app state
        test_path = str(tmp_path / "test_storage")
        config = Config(storage_path=test_path, log_level="INFO")
        initialize_app_state(config)

        middleware = AppStateMiddleware()
        mock_context = MagicMock()
        mock_context.fastmcp_context = MagicMock()
        mock_call_next = AsyncMock(return_value="result")

        result = await middleware.on_call_tool(mock_context, mock_call_next)

        assert result == "result"
        mock_context.fastmcp_context.set_state.assert_called_once_with("app_state", get_app_state())
        mock_call_next.assert_called_once_with(mock_context)

    @pytest.mark.asyncio
    async def test_middleware_raises_when_app_state_not_initialized(self) -> None:
        """Test middleware raises when AppState not initialized."""
        # Reset state
        from hjeon139_mcp_outofcontext import fastmcp_server

        fastmcp_server._app_state = None

        middleware = AppStateMiddleware()
        mock_context = MagicMock()
        mock_call_next = MagicMock()

        with pytest.raises(RuntimeError, match="AppState not initialized"):
            await middleware.on_call_tool(mock_context, mock_call_next)

    @pytest.mark.asyncio
    async def test_middleware_raises_when_fastmcp_context_none(self, tmp_path) -> None:
        """Test middleware raises when fastmcp_context is None."""
        test_path = str(tmp_path / "test_storage")
        config = Config(storage_path=test_path, log_level="INFO")
        initialize_app_state(config)

        middleware = AppStateMiddleware()
        mock_context = MagicMock()
        mock_context.fastmcp_context = None
        mock_call_next = MagicMock()

        with pytest.raises(RuntimeError, match="FastMCP context not available"):
            await middleware.on_call_tool(mock_context, mock_call_next)

    @pytest.mark.asyncio
    async def test_middleware_injects_app_state_on_read_resource(self, tmp_path) -> None:
        """Test middleware injects AppState on resource read."""
        test_path = str(tmp_path / "test_storage")
        config = Config(storage_path=test_path, log_level="INFO")
        initialize_app_state(config)

        middleware = AppStateMiddleware()
        mock_context = MagicMock()
        mock_context.fastmcp_context = MagicMock()
        mock_call_next = AsyncMock(return_value="result")

        result = await middleware.on_read_resource(mock_context, mock_call_next)

        assert result == "result"
        mock_context.fastmcp_context.set_state.assert_called_once_with("app_state", get_app_state())
        mock_call_next.assert_called_once_with(mock_context)


@pytest.mark.unit
class TestFastMCPServer:
    """Test FastMCP server instance."""

    def test_mcp_instance_exists(self) -> None:
        """Test that mcp instance exists."""
        assert mcp is not None
        assert hasattr(mcp, "add_middleware")

    def test_register_all_tools(self) -> None:
        """Test register_all_tools function."""
        from hjeon139_mcp_outofcontext.fastmcp_server import register_all_tools

        with patch("hjeon139_mcp_outofcontext.tools.crud.register_tools") as mock_register:
            register_all_tools()
            mock_register.assert_called_once()
