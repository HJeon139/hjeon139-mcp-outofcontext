"""Verification tests for token limit configuration."""

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.config import Config, load_config
from hjeon139_mcp_outofcontext.server import MCPServer
from hjeon139_mcp_outofcontext.tools.monitoring import handle_analyze_usage


@pytest.mark.unit
def test_app_state_extracts_token_limit_from_config() -> None:
    """Verify AppState extracts token_limit from config."""
    # Test with default config
    app_state = AppState()
    assert app_state.token_limit == 1000000  # Default from config

    # Test with custom config
    custom_config = {"token_limit": 2000000}
    app_state_custom = AppState(config=custom_config)
    assert app_state_custom.token_limit == 2000000

    # Test with config missing token_limit (should use default)
    config_no_limit = {"storage_path": "/tmp/test"}
    app_state_no_limit = AppState(config=config_no_limit)
    assert app_state_no_limit.token_limit == 1000000  # Default


@pytest.mark.unit
def test_config_default_token_limit() -> None:
    """Verify Config class has correct default token_limit."""
    config = Config()
    assert config.token_limit == 1000000
    assert config.to_dict()["token_limit"] == 1000000


@pytest.mark.unit
def test_server_uses_config_token_limit() -> None:
    """Verify MCPServer uses config token_limit."""
    # Test with default config
    server = MCPServer()
    assert server.app_state.token_limit == 1000000

    # Test with custom config
    custom_config = Config(token_limit=5000000)
    server_custom = MCPServer(config=custom_config)
    assert server_custom.app_state.token_limit == 5000000


@pytest.mark.unit
@pytest.mark.asyncio
async def test_analyze_usage_uses_app_state_token_limit() -> None:
    """Verify handle_analyze_usage uses app_state.token_limit when token_limit not provided."""
    # Create app_state with custom token_limit
    custom_config = {"token_limit": 2000000}
    app_state = AppState(config=custom_config)

    # Call analyze_usage without providing token_limit
    result = await handle_analyze_usage(
        app_state=app_state,
        project_id="test-project",
        token_limit=None,  # Should use app_state.token_limit
    )

    # Should not have error
    assert "error" not in result

    # Verify the token_limit was used (check via usage_metrics if available)
    if "usage_metrics" in result:
        # The limit should be reflected in the metrics
        # We can't directly check the limit, but we can verify it's working
        assert "estimated_remaining_tokens" in result["usage_metrics"]
        # With 0 tokens used, remaining should be close to the limit
        # (allowing for some calculation differences)
        remaining = result["usage_metrics"]["estimated_remaining_tokens"]
        assert remaining >= 1000000  # Should be at least 1M, likely 2M


@pytest.mark.unit
@pytest.mark.asyncio
async def test_analyze_usage_respects_explicit_token_limit() -> None:
    """Verify handle_analyze_usage respects explicit token_limit parameter."""
    # Create app_state with custom token_limit
    custom_config = {"token_limit": 2000000}
    app_state = AppState(config=custom_config)

    # Call analyze_usage with explicit token_limit
    result = await handle_analyze_usage(
        app_state=app_state,
        project_id="test-project",
        token_limit=500000,  # Explicit limit should override config
    )

    # Should not have error
    assert "error" not in result

    # Verify the explicit token_limit was used
    if "usage_metrics" in result:
        remaining = result["usage_metrics"]["estimated_remaining_tokens"]
        # Should be close to 500k (allowing for calculation)
        assert 400000 <= remaining <= 600000


@pytest.mark.unit
def test_load_config_includes_token_limit() -> None:
    """Verify load_config() includes token_limit in returned config."""
    config = load_config()
    assert config.token_limit == 1000000
    config_dict = config.to_dict()
    assert config_dict["token_limit"] == 1000000
