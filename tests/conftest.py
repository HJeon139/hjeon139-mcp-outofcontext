"""Shared pytest fixtures for integration and performance testing."""

from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import Any

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.models import (
    ContextDescriptors,
    ContextSegment,
    Message,
    TaskInfo,
    TokenUsage,
)


@pytest.fixture
def project_id() -> str:
    """Provide a default project identifier for tests."""
    return "test-project"


@pytest.fixture
def task_id() -> str:
    """Provide a default task identifier for tests."""
    return "task-123"


@pytest.fixture
def context_descriptors(task_id: str) -> ContextDescriptors:
    """Create lightweight descriptors for context analysis workflows."""
    now = datetime.now()
    return ContextDescriptors(
        recent_messages=[
            Message(role="user", content="Hello world", timestamp=now - timedelta(minutes=1))
        ],
        current_file=None,
        token_usage=TokenUsage(current=10, limit=100, usage_percent=10.0),
        segment_summaries=[],
        task_info=TaskInfo(task_id=task_id, name="Test Task"),
    )


@pytest.fixture
def sample_segments(project_id: str, task_id: str) -> list[ContextSegment]:
    """Generate sample segments spanning types and metadata for storage tests."""
    now = datetime.now()
    return [
        ContextSegment(
            segment_id="seg-message",
            text="User: first message",
            type="message",
            project_id=project_id,
            task_id=task_id,
            created_at=now - timedelta(minutes=5),
            last_touched_at=now - timedelta(minutes=4),
            pinned=False,
            generation="young",
            gc_survival_count=0,
            refcount=0,
            file_path=None,
            line_range=None,
            tags=["chat"],
            topic_id=None,
            tokens=5,
            tokens_computed_at=now - timedelta(minutes=4),
            text_hash=None,
            tier="working",
        ),
        ContextSegment(
            segment_id="seg-log",
            text="Log entry for diagnostics",
            type="log",
            project_id=project_id,
            task_id=None,
            created_at=now - timedelta(hours=1),
            last_touched_at=now - timedelta(hours=1),
            pinned=False,
            generation="old",
            gc_survival_count=3,
            refcount=1,
            file_path=None,
            line_range=None,
            tags=["log"],
            topic_id=None,
            tokens=8,
            tokens_computed_at=now - timedelta(hours=1),
            text_hash=None,
            tier="working",
        ),
    ]


@pytest.fixture
def app_state(tmp_path) -> Iterator[AppState]:
    """Provision an isolated AppState backed by a temporary storage path."""
    state = AppState(config={"storage_path": tmp_path.as_posix(), "model": "gpt-4"})
    try:
        yield state
    finally:
        # No teardown required currently; placeholder for future cleanup.
        pass


@pytest.fixture
def context_manager(app_state: AppState) -> Any:
    """Expose the ContextManager from the shared AppState."""
    return app_state.context_manager
