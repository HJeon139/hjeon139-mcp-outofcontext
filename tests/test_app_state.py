"""Tests for AppState."""

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState


@pytest.mark.unit
class TestAppState:
    """Test AppState class."""

    def test_app_state_initialization(self) -> None:
        """Test AppState initialization."""
        app_state = AppState()
        assert app_state.config == {}
        assert app_state.storage is not None

    def test_app_state_with_config(self) -> None:
        """Test AppState initialization with config."""
        config = {"storage_path": "/tmp/test"}
        app_state = AppState(config=config)
        assert app_state.config == config
        assert app_state.storage is not None

    @pytest.mark.asyncio
    async def test_app_state_lifespan(self) -> None:
        """Test AppState lifespan context manager."""
        app_state = AppState()
        async with app_state.lifespan():
            # Components should be available
            assert app_state.storage is not None
        # After context, components should still be available
        assert app_state.storage is not None
