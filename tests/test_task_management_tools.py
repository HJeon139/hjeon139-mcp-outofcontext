"""Unit tests for task management tools."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.models import ContextSegment
from hjeon139_mcp_outofcontext.tool_registry import ToolRegistry
from hjeon139_mcp_outofcontext.tools.tasks import (
    handle_create_task_snapshot,
    handle_get_task_context,
    handle_set_current_task,
    register_task_management_tools,
)


@pytest.mark.unit
class TestContextSetCurrentTask:
    """Test context_set_current_task tool handler."""

    @pytest.mark.asyncio
    async def test_set_current_task_with_valid_parameters(self) -> None:
        """Test set current task with valid parameters."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        task_id = "task-123"

        # Mock context manager
        mock_result = {
            "previous_task_id": None,
            "current_task_id": task_id,
            "working_set_updated": True,
        }
        app_state.context_manager.set_current_task = MagicMock(  # type: ignore[method-assign]
            return_value=mock_result
        )

        # Act
        result = await handle_set_current_task(
            app_state=app_state,
            project_id=project_id,
            task_id=task_id,
        )

        # Assert
        assert "error" not in result
        assert result["previous_task_id"] is None
        assert result["current_task_id"] == task_id
        assert result["working_set_updated"] is True
        app_state.context_manager.set_current_task.assert_called_once_with(
            project_id=project_id, task_id=task_id
        )

    @pytest.mark.asyncio
    async def test_set_current_task_clear_task(self) -> None:
        """Test set current task to None (clear task)."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        # Mock context manager
        mock_result = {
            "previous_task_id": "task-123",
            "current_task_id": None,
            "working_set_updated": True,
        }
        app_state.context_manager.set_current_task = MagicMock(  # type: ignore[method-assign]
            return_value=mock_result
        )

        # Act
        result = await handle_set_current_task(
            app_state=app_state,
            project_id=project_id,
            task_id=None,
        )

        # Assert
        assert "error" not in result
        assert result["previous_task_id"] == "task-123"
        assert result["current_task_id"] is None
        assert result["working_set_updated"] is True

    @pytest.mark.asyncio
    async def test_set_current_task_switch_tasks(self) -> None:
        """Test switching from one task to another."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        new_task_id = "task-456"

        # Mock context manager
        mock_result = {
            "previous_task_id": "task-123",
            "current_task_id": new_task_id,
            "working_set_updated": True,
        }
        app_state.context_manager.set_current_task = MagicMock(  # type: ignore[method-assign]
            return_value=mock_result
        )

        # Act
        result = await handle_set_current_task(
            app_state=app_state,
            project_id=project_id,
            task_id=new_task_id,
        )

        # Assert
        assert "error" not in result
        assert result["previous_task_id"] == "task-123"
        assert result["current_task_id"] == new_task_id

    @pytest.mark.asyncio
    async def test_set_current_task_missing_project_id(self) -> None:
        """Test set current task with missing project_id."""
        # Arrange
        app_state = AppState()

        # Act
        result = await handle_set_current_task(
            app_state=app_state,
            project_id=None,
            task_id="task-123",
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert result["error"]["message"] == "project_id is required"

    @pytest.mark.asyncio
    async def test_set_current_task_value_error(self) -> None:
        """Test set current task with ValueError from context manager."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        task_id = "task-123"

        app_state.context_manager.set_current_task = MagicMock(  # type: ignore[method-assign]
            side_effect=ValueError("Invalid project")
        )

        # Act
        result = await handle_set_current_task(
            app_state=app_state,
            project_id=project_id,
            task_id=task_id,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert result["error"]["message"] == "Invalid project"

    @pytest.mark.asyncio
    async def test_set_current_task_unexpected_error(self) -> None:
        """Test set current task with unexpected error."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        task_id = "task-123"

        app_state.context_manager.set_current_task = MagicMock(  # type: ignore[method-assign]
            side_effect=RuntimeError("Unexpected error")
        )

        # Act
        result = await handle_set_current_task(
            app_state=app_state,
            project_id=project_id,
            task_id=task_id,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INTERNAL_ERROR"
        assert "Unexpected error" in result["error"]["message"]


@pytest.mark.unit
class TestContextGetTaskContext:
    """Test context_get_task_context tool handler."""

    @pytest.mark.asyncio
    async def test_get_task_context_with_task_id(self) -> None:
        """Test get task context with specific task_id."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        task_id = "task-123"

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment 1",
                type="message",
                project_id=project_id,
                task_id=task_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="working",
            ),
            ContextSegment(
                segment_id="seg2",
                text="Test segment 2",
                type="code",
                project_id=project_id,
                task_id=task_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=200,
                tier="stashed",
            ),
        ]

        mock_result = {
            "task_id": task_id,
            "segments": mock_segments,
            "total_tokens": 300,
            "segment_count": 2,
            "active": False,
        }

        app_state.context_manager.get_task_context = MagicMock(  # type: ignore[method-assign]
            return_value=mock_result
        )

        # Act
        result = await handle_get_task_context(
            app_state=app_state,
            project_id=project_id,
            task_id=task_id,
        )

        # Assert
        assert "error" not in result
        assert result["task_id"] == task_id
        assert len(result["segments"]) == 2
        assert result["total_tokens"] == 300
        assert result["segment_count"] == 2
        assert result["active"] is False
        app_state.context_manager.get_task_context.assert_called_once_with(
            project_id=project_id, task_id=task_id
        )

    @pytest.mark.asyncio
    async def test_get_task_context_with_current_task(self) -> None:
        """Test get task context using current task."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        task_id = "task-123"

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment",
                type="message",
                project_id=project_id,
                task_id=task_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="working",
            )
        ]

        mock_result = {
            "task_id": task_id,
            "segments": mock_segments,
            "total_tokens": 100,
            "segment_count": 1,
            "active": True,
        }

        app_state.context_manager.get_task_context = MagicMock(  # type: ignore[method-assign]
            return_value=mock_result
        )

        # Act
        result = await handle_get_task_context(
            app_state=app_state,
            project_id=project_id,
            task_id=None,
        )

        # Assert
        assert "error" not in result
        assert result["task_id"] == task_id
        assert result["active"] is True
        app_state.context_manager.get_task_context.assert_called_once_with(
            project_id=project_id, task_id=None
        )

    @pytest.mark.asyncio
    async def test_get_task_context_no_task(self) -> None:
        """Test get task context when no task is set."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        mock_result = {
            "task_id": None,
            "segments": [],
            "total_tokens": 0,
            "segment_count": 0,
            "active": False,
        }

        app_state.context_manager.get_task_context = MagicMock(  # type: ignore[method-assign]
            return_value=mock_result
        )

        # Act
        result = await handle_get_task_context(
            app_state=app_state,
            project_id=project_id,
            task_id=None,
        )

        # Assert
        assert "error" not in result
        assert result["task_id"] is None
        assert result["segment_count"] == 0
        assert result["total_tokens"] == 0

    @pytest.mark.asyncio
    async def test_get_task_context_missing_project_id(self) -> None:
        """Test get task context with missing project_id."""
        # Arrange
        app_state = AppState()

        # Act
        result = await handle_get_task_context(
            app_state=app_state,
            project_id=None,
            task_id="task-123",
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert result["error"]["message"] == "project_id is required"

    @pytest.mark.asyncio
    async def test_get_task_context_value_error(self) -> None:
        """Test get task context with ValueError."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        task_id = "task-123"

        app_state.context_manager.get_task_context = MagicMock(  # type: ignore[method-assign]
            side_effect=ValueError("Invalid project")
        )

        # Act
        result = await handle_get_task_context(
            app_state=app_state,
            project_id=project_id,
            task_id=task_id,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert result["error"]["message"] == "Invalid project"

    @pytest.mark.asyncio
    async def test_get_task_context_unexpected_error(self) -> None:
        """Test get task context with unexpected error."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        task_id = "task-123"

        app_state.context_manager.get_task_context = MagicMock(  # type: ignore[method-assign]
            side_effect=RuntimeError("Unexpected error")
        )

        # Act
        result = await handle_get_task_context(
            app_state=app_state,
            project_id=project_id,
            task_id=task_id,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INTERNAL_ERROR"
        assert "Unexpected error" in result["error"]["message"]


@pytest.mark.unit
class TestContextCreateTaskSnapshot:
    """Test context_create_task_snapshot tool handler."""

    @pytest.mark.asyncio
    async def test_create_snapshot_with_valid_parameters(self) -> None:
        """Test create snapshot with valid parameters."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        task_id = "task-123"
        name = "before-refactor"

        mock_result = {
            "snapshot_id": "snapshot-123",
            "task_id": task_id,
            "segments_captured": 3,
            "tokens_captured": 500,
            "created_at": datetime.now().isoformat(),
        }

        app_state.context_manager.create_task_snapshot = MagicMock(  # type: ignore[method-assign]
            return_value=mock_result
        )

        # Act
        result = await handle_create_task_snapshot(
            app_state=app_state,
            project_id=project_id,
            task_id=task_id,
            name=name,
        )

        # Assert
        assert "error" not in result
        assert result["snapshot_id"] == "snapshot-123"
        assert result["task_id"] == task_id
        assert result["segments_captured"] == 3
        assert result["tokens_captured"] == 500
        assert "created_at" in result
        app_state.context_manager.create_task_snapshot.assert_called_once_with(
            project_id=project_id, task_id=task_id, name=name
        )

    @pytest.mark.asyncio
    async def test_create_snapshot_without_name(self) -> None:
        """Test create snapshot without optional name."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        task_id = "task-123"

        mock_result = {
            "snapshot_id": "snapshot-123",
            "task_id": task_id,
            "segments_captured": 2,
            "tokens_captured": 300,
            "created_at": datetime.now().isoformat(),
        }

        app_state.context_manager.create_task_snapshot = MagicMock(  # type: ignore[method-assign]
            return_value=mock_result
        )

        # Act
        result = await handle_create_task_snapshot(
            app_state=app_state,
            project_id=project_id,
            task_id=task_id,
            name=None,
        )

        # Assert
        assert "error" not in result
        assert result["snapshot_id"] == "snapshot-123"
        app_state.context_manager.create_task_snapshot.assert_called_once_with(
            project_id=project_id, task_id=task_id, name=None
        )

    @pytest.mark.asyncio
    async def test_create_snapshot_with_current_task(self) -> None:
        """Test create snapshot using current task."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        task_id = "task-123"

        mock_result = {
            "snapshot_id": "snapshot-123",
            "task_id": task_id,
            "segments_captured": 1,
            "tokens_captured": 100,
            "created_at": datetime.now().isoformat(),
        }

        app_state.context_manager.create_task_snapshot = MagicMock(  # type: ignore[method-assign]
            return_value=mock_result
        )

        # Act
        result = await handle_create_task_snapshot(
            app_state=app_state,
            project_id=project_id,
            task_id=None,
        )

        # Assert
        assert "error" not in result
        assert result["task_id"] == task_id
        app_state.context_manager.create_task_snapshot.assert_called_once_with(
            project_id=project_id, task_id=None, name=None
        )

    @pytest.mark.asyncio
    async def test_create_snapshot_missing_project_id(self) -> None:
        """Test create snapshot with missing project_id."""
        # Arrange
        app_state = AppState()

        # Act
        result = await handle_create_task_snapshot(
            app_state=app_state,
            project_id=None,
            task_id="task-123",
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert result["error"]["message"] == "project_id is required"

    @pytest.mark.asyncio
    async def test_create_snapshot_no_task_set(self) -> None:
        """Test create snapshot when no task is set."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        app_state.context_manager.create_task_snapshot = MagicMock(  # type: ignore[method-assign]
            side_effect=ValueError("No task specified and no current task set")
        )

        # Act
        result = await handle_create_task_snapshot(
            app_state=app_state,
            project_id=project_id,
            task_id=None,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert "No task specified" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_create_snapshot_value_error(self) -> None:
        """Test create snapshot with ValueError."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        task_id = "task-123"

        app_state.context_manager.create_task_snapshot = MagicMock(  # type: ignore[method-assign]
            side_effect=ValueError("Invalid project")
        )

        # Act
        result = await handle_create_task_snapshot(
            app_state=app_state,
            project_id=project_id,
            task_id=task_id,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert result["error"]["message"] == "Invalid project"

    @pytest.mark.asyncio
    async def test_create_snapshot_unexpected_error(self) -> None:
        """Test create snapshot with unexpected error."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        task_id = "task-123"

        app_state.context_manager.create_task_snapshot = MagicMock(  # type: ignore[method-assign]
            side_effect=RuntimeError("Unexpected error")
        )

        # Act
        result = await handle_create_task_snapshot(
            app_state=app_state,
            project_id=project_id,
            task_id=task_id,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INTERNAL_ERROR"
        assert "Unexpected error" in result["error"]["message"]


@pytest.mark.unit
class TestTaskManagementToolsRegistration:
    """Test task management tools registration."""

    def test_register_task_management_tools(self) -> None:
        """Test that task management tools are registered correctly."""
        # Arrange
        registry = ToolRegistry()
        app_state = AppState()

        # Act
        register_task_management_tools(registry, app_state)

        # Assert
        tools = registry.list_tools()
        tool_names = {tool.name for tool in tools}
        assert "context_set_current_task" in tool_names
        assert "context_get_task_context" in tool_names
        assert "context_create_task_snapshot" in tool_names
