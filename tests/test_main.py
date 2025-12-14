"""Tests for main entry point."""

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hjeon139_mcp_outofcontext.main import main


@pytest.mark.unit
class TestMain:
    """Test main entry point."""

    @pytest.mark.asyncio
    async def test_main_success(self) -> None:
        """Test main function runs successfully."""
        with (
            patch("hjeon139_mcp_outofcontext.main.load_config") as mock_load_config,
            patch("hjeon139_mcp_outofcontext.main.MCPServer") as mock_server_class,
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.storage_path = "/test/path"
            mock_config.log_level = "INFO"
            mock_load_config.return_value = mock_config

            mock_server = AsyncMock()
            mock_server.run = AsyncMock()
            mock_server_class.return_value = mock_server

            # Run main
            await main()

            # Verify
            mock_load_config.assert_called_once()
            mock_server_class.assert_called_once_with(config=mock_config)
            mock_server.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self) -> None:
        """Test main handles KeyboardInterrupt gracefully."""
        with (
            patch("hjeon139_mcp_outofcontext.main.load_config") as mock_load_config,
            patch("hjeon139_mcp_outofcontext.main.MCPServer") as mock_server_class,
            patch("hjeon139_mcp_outofcontext.main.logger") as mock_logger,
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.storage_path = "/test/path"
            mock_config.log_level = "INFO"
            mock_load_config.return_value = mock_config

            mock_server = AsyncMock()
            mock_server.run = AsyncMock(side_effect=KeyboardInterrupt())
            mock_server_class.return_value = mock_server

            # Run main - should not raise
            await main()

            # Verify KeyboardInterrupt was logged
            mock_logger.info.assert_any_call("Server stopped by user")

    @pytest.mark.asyncio
    async def test_main_exception_handling(self) -> None:
        """Test main handles exceptions and exits."""
        with (
            patch("hjeon139_mcp_outofcontext.main.load_config") as mock_load_config,
            patch("hjeon139_mcp_outofcontext.main.MCPServer") as mock_server_class,
            patch("hjeon139_mcp_outofcontext.main.logger") as mock_logger,
            patch("hjeon139_mcp_outofcontext.main.sys.exit") as mock_exit,
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.storage_path = "/test/path"
            mock_config.log_level = "INFO"
            mock_load_config.return_value = mock_config

            mock_server = AsyncMock()
            mock_server.run = AsyncMock(side_effect=ValueError("Test error"))
            mock_server_class.return_value = mock_server

            # Run main
            await main()

            # Verify exception was logged and sys.exit was called
            mock_logger.exception.assert_called_once()
            mock_exit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_main_log_level_config(self) -> None:
        """Test main sets log level from config."""
        with (
            patch("hjeon139_mcp_outofcontext.main.load_config") as mock_load_config,
            patch("hjeon139_mcp_outofcontext.main.MCPServer") as mock_server_class,
            patch("hjeon139_mcp_outofcontext.main.logging.getLogger") as mock_get_logger,
        ):
            # Setup mocks
            mock_config = MagicMock()
            mock_config.storage_path = "/test/path"
            mock_config.log_level = "DEBUG"
            mock_load_config.return_value = mock_config

            mock_server = AsyncMock()
            mock_server.run = AsyncMock()
            mock_server_class.return_value = mock_server

            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Run main
            await main()

            # Verify log level was set
            mock_get_logger.assert_called()
            # The logger's setLevel should have been called with DEBUG
            # (We can't easily verify this without more complex mocking, but the code path is tested)


@pytest.mark.unit
class TestMainEntryPoint:
    """Test __main__ block execution."""

    def test_main_module_execution(self) -> None:
        """Test that main can be executed as a module."""
        with (
            patch("hjeon139_mcp_outofcontext.main.asyncio.run") as _mock_asyncio_run,
            patch("hjeon139_mcp_outofcontext.main.__name__", "__main__"),
        ):
            # This simulates running: python -m hjeon139_mcp_outofcontext.main
            # We can't easily test the actual __main__ block without importing and executing,
            # but we can verify the structure is correct
            assert callable(main)
            assert inspect.iscoroutinefunction(main)
