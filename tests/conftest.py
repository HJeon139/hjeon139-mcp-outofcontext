"""Shared pytest fixtures for testing."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState


@pytest.fixture
def project_id() -> str:
    """Provide a default project identifier for tests."""
    return "test-project"


@pytest.fixture
def app_state(tmp_path: Path) -> Iterator[AppState]:
    """Provision an isolated AppState backed by a temporary storage path."""
    state = AppState(config={"storage_path": str(tmp_path)})
    try:
        yield state
    finally:
        # No teardown required currently; placeholder for future cleanup.
        pass
