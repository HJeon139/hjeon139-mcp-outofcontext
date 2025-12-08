"""Unit tests for stashing tools."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.models import ContextSegment, StashResult, WorkingSet
from hjeon139_mcp_outofcontext.tool_registry import ToolRegistry
from hjeon139_mcp_outofcontext.tools.stashing import (
    handle_list_projects,
    handle_retrieve_stashed,
    handle_search_stashed,
    handle_stash,
    register_stashing_tools,
)
from hjeon139_mcp_outofcontext.tools.stashing.helpers import (
    create_error_response,
    parse_filters_param,
    parse_json_or_literal,
)


@pytest.mark.unit
class TestStashingHelpers:
    """Test helper functions for stashing tools."""

    def test_create_error_response(self) -> None:
        """Test create_error_response helper."""
        result = create_error_response("TEST_CODE", "Test message")
        assert "error" in result
        assert result["error"]["code"] == "TEST_CODE"
        assert result["error"]["message"] == "Test message"
        assert result["error"]["details"] == {}

    def test_create_error_response_with_details(self) -> None:
        """Test create_error_response with details."""
        details = {"key": "value"}
        result = create_error_response("TEST_CODE", "Test message", details)
        assert result["error"]["details"] == details

    def test_parse_json_or_literal_json(self) -> None:
        """Test parse_json_or_literal with JSON string."""
        result = parse_json_or_literal('{"key": "value"}', "test_param")
        assert result == {"key": "value"}

    def test_parse_json_or_literal_python_literal(self) -> None:
        """Test parse_json_or_literal with Python literal."""
        result = parse_json_or_literal("{'key': 'value'}", "test_param")
        assert result == {"key": "value"}

    def test_parse_json_or_literal_list(self) -> None:
        """Test parse_json_or_literal with list."""
        result = parse_json_or_literal('["a", "b"]', "test_param")
        assert result == ["a", "b"]

    def test_parse_json_or_literal_invalid(self) -> None:
        """Test parse_json_or_literal with invalid input."""
        with pytest.raises(ValueError, match="Invalid format"):
            parse_json_or_literal("not valid", "test_param")

    def test_parse_filters_param_none(self) -> None:
        """Test parse_filters_param with None."""
        result = parse_filters_param(None)
        assert result is None

    def test_parse_filters_param_dict(self) -> None:
        """Test parse_filters_param with dict."""
        filters = {"type": "message"}
        result = parse_filters_param(filters)
        assert result == filters

    def test_parse_filters_param_json_string(self) -> None:
        """Test parse_filters_param with JSON string."""
        result = parse_filters_param('{"type": "message"}')
        assert result == {"type": "message"}

    def test_parse_filters_param_python_literal_string(self) -> None:
        """Test parse_filters_param with Python literal string."""
        result = parse_filters_param("{'type': 'message'}")
        assert result == {"type": "message"}

    def test_parse_filters_param_non_dict_string(self) -> None:
        """Test parse_filters_param with string that parses to non-dict."""
        with pytest.raises(ValueError, match="filters must be a dictionary"):
            parse_filters_param('["not", "a", "dict"]')

    def test_parse_filters_param_invalid_type(self) -> None:
        """Test parse_filters_param with invalid type."""
        with pytest.raises(ValueError, match="filters must be a dict, string, or None"):
            parse_filters_param(123)  # type: ignore[arg-type]


@pytest.mark.unit
class TestContextStash:
    """Test context_stash tool handler."""

    @pytest.mark.asyncio
    async def test_stash_with_valid_parameters(self) -> None:
        """Test stash with valid parameters."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        query = "test"

        # Create mock segments
        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="test segment 1",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="working",
            ),
            ContextSegment(
                segment_id="seg2",
                text="test segment 2",
                type="code",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=200,
                tier="working",
            ),
        ]

        # Mock working set
        mock_working_set = WorkingSet(
            segments=mock_segments,
            total_tokens=300,
            project_id=project_id,
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        # Mock stash result
        mock_stash_result = StashResult(
            stashed_segments=["seg1", "seg2"],
            tokens_freed=300,
            stash_location=None,
        )
        app_state.context_manager.stash_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_stash_result
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            query=query,
        )

        # Assert
        assert "error" not in result
        assert result["stashed_segments"] == ["seg1", "seg2"]
        assert result["tokens_stashed"] == 300
        assert result["segments_matched"] == 2
        assert result["errors"] == []
        app_state.context_manager.stash_segments.assert_called_once()

    @pytest.mark.asyncio
    async def test_stash_without_project_id_uses_default(self) -> None:
        """Test stash without project_id uses default project."""
        # Arrange
        app_state = AppState()
        query = "test"

        # Mock empty working set for default project
        mock_working_set = WorkingSet(
            segments=[],
            total_tokens=0,
            project_id="default",
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=None,
            query=query,
        )

        # Assert - should use 'default' project_id
        assert "error" not in result
        assert result["stashed_segments"] == []
        assert result["segments_matched"] == 0
        app_state.context_manager.get_working_set.assert_called_once_with(
            project_id="default", task_id=None
        )

    @pytest.mark.asyncio
    async def test_stash_no_matching_segments(self) -> None:
        """Test stash with no matching segments."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        # Mock empty working set
        mock_working_set = WorkingSet(
            segments=[],
            total_tokens=0,
            project_id=project_id,
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            query="nonexistent",
        )

        # Assert
        assert "error" not in result
        assert result["stashed_segments"] == []
        assert result["tokens_stashed"] == 0
        assert result["segments_matched"] == 0

    @pytest.mark.asyncio
    async def test_stash_with_filters_dict(self) -> None:
        """Test stash with metadata filters as dict."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = {"type": "message"}

        # Create mock segments
        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="test segment",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="working",
            ),
            ContextSegment(
                segment_id="seg2",
                text="test segment",
                type="code",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=200,
                tier="working",
            ),
        ]

        # Mock working set
        mock_working_set = WorkingSet(
            segments=mock_segments,
            total_tokens=300,
            project_id=project_id,
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        # Mock stash result
        mock_stash_result = StashResult(
            stashed_segments=["seg1"],
            tokens_freed=100,
            stash_location=None,
        )
        app_state.context_manager.stash_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_stash_result
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        assert result["stashed_segments"] == ["seg1"]  # Only message type
        assert result["segments_matched"] == 1

    @pytest.mark.asyncio
    async def test_stash_with_filters_json_string(self) -> None:
        """Test stash with filters as JSON string."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = '{"type": "message"}'

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="test",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="working",
            )
        ]

        mock_working_set = WorkingSet(
            segments=mock_segments,
            total_tokens=100,
            project_id=project_id,
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        mock_stash_result = StashResult(
            stashed_segments=["seg1"],
            tokens_freed=100,
            stash_location=None,
        )
        app_state.context_manager.stash_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_stash_result
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        assert result["stashed_segments"] == ["seg1"]

    @pytest.mark.asyncio
    async def test_stash_with_invalid_filters(self) -> None:
        """Test stash with invalid filters format."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = "not a valid dict"

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_stash_value_error(self) -> None:
        """Test stash with ValueError from context manager."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        # Mock working set
        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="test",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="working",
            )
        ]
        mock_working_set = WorkingSet(
            segments=mock_segments,
            total_tokens=100,
            project_id=project_id,
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        app_state.context_manager.stash_segments = MagicMock(  # type: ignore[method-assign]
            side_effect=ValueError("Invalid segment")
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            query="test",
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert result["error"]["message"] == "Invalid segment"

    @pytest.mark.asyncio
    async def test_stash_unexpected_error(self) -> None:
        """Test stash with unexpected error."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        # Mock working set
        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="test",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="working",
            )
        ]
        mock_working_set = WorkingSet(
            segments=mock_segments,
            total_tokens=100,
            project_id=project_id,
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        app_state.context_manager.stash_segments = MagicMock(  # type: ignore[method-assign]
            side_effect=RuntimeError("Unexpected error")
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            query="test",
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INTERNAL_ERROR"
        assert "Unexpected error" in result["error"]["message"]


@pytest.mark.unit
class TestContextSearchStashed:
    """Test context_search_stashed tool handler."""

    @pytest.mark.asyncio
    async def test_search_with_query(self) -> None:
        """Test search with keyword query."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        query = "test query"

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="stashed",
            )
        ]

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
            query=query,
        )

        # Assert
        assert "error" not in result
        assert len(result["segments"]) == 1
        assert result["total_matches"] == 1
        assert result["query"] == query
        app_state.storage.search_stashed.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_filters(self) -> None:
        """Test search with metadata filters."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = {"file_path": "test.py", "tags": ["test"]}

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment",
                type="code",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="stashed",
                file_path="test.py",
                tags=["test"],
            )
        ]

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        assert len(result["segments"]) == 1
        assert "filters_applied" in result

    @pytest.mark.asyncio
    async def test_search_missing_project_id(self) -> None:
        """Test search without project_id searches across all projects."""
        # Arrange
        app_state = AppState()
        # Mock storage to return empty results (no stashed segments)
        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )
        app_state.storage.list_projects = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=None,
        )

        # Assert - should search across all projects (empty result if no projects)
        assert "error" not in result
        assert "segments" in result
        assert "total_matches" in result
        assert result["total_matches"] == 0  # No projects exist in empty storage


@pytest.mark.unit
class TestContextRetrieveStashed:
    """Test context_retrieve_stashed tool handler."""

    @pytest.mark.asyncio
    async def test_retrieve_without_move_to_active(self) -> None:
        """Test retrieve without moving to active."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        query = "test"

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment 1",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="stashed",
            ),
            ContextSegment(
                segment_id="seg2",
                text="Test segment 2",
                type="code",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=200,
                tier="stashed",
            ),
        ]

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            query=query,
            move_to_active=False,
        )

        # Assert
        assert "error" not in result
        assert len(result["retrieved_segments"]) == 2
        assert result["moved_to_active"] == []
        assert result["segments_found"] == 2

    @pytest.mark.asyncio
    async def test_retrieve_with_move_to_active(self) -> None:
        """Test retrieve with move_to_active=True."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        query = "test"

        mock_segment = ContextSegment(
            segment_id="seg1",
            text="Test segment",
            type="message",
            project_id=project_id,
            created_at=datetime.now(),
            last_touched_at=datetime.now(),
            tokens=100,
            tier="stashed",
        )

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=[mock_segment]
        )
        app_state.storage.unstash_segment = MagicMock()  # type: ignore[method-assign]
        app_state.context_manager.working_sets = {project_id: {}}

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            query=query,
            move_to_active=True,
        )

        # Assert
        assert "error" not in result
        assert len(result["retrieved_segments"]) == 1
        assert result["moved_to_active"] == ["seg1"]
        assert result["segments_found"] == 1
        app_state.storage.unstash_segment.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_with_filters_dict(self) -> None:
        """Test retrieve with metadata filters as dict."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = {"type": "message"}

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment 1",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="stashed",
            ),
            ContextSegment(
                segment_id="seg2",
                text="Test segment 2",
                type="code",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=200,
                tier="stashed",
            ),
        ]

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        assert "retrieved_segments" in result

    @pytest.mark.asyncio
    async def test_retrieve_with_filters_json_string(self) -> None:
        """Test retrieve with filters as JSON string."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = '{"type": "message"}'

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="stashed",
            )
        ]

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        assert len(result["retrieved_segments"]) == 1

    @pytest.mark.asyncio
    async def test_retrieve_with_invalid_filters(self) -> None:
        """Test retrieve with invalid filters format."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = "not a valid dict"

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_retrieve_without_project_id_uses_default(self) -> None:
        """Test retrieve without project_id uses default project."""
        # Arrange
        app_state = AppState()
        query = "test"

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=None,
            query=query,
        )

        # Assert - should use 'default' project_id
        assert "error" not in result
        assert len(result["retrieved_segments"]) == 0
        assert result["segments_found"] == 0
        app_state.storage.search_stashed.assert_called_once_with(
            query=query, filters={}, project_id="default"
        )

    @pytest.mark.asyncio
    async def test_retrieve_no_matching_segments(self) -> None:
        """Test retrieve with no matching segments."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            query="nonexistent",
        )

        # Assert
        assert "error" not in result
        assert len(result["retrieved_segments"]) == 0
        assert result["segments_found"] == 0

    @pytest.mark.asyncio
    async def test_retrieve_error_during_move(self) -> None:
        """Test retrieve handles error during move to active."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        query = "test"

        mock_segment = ContextSegment(
            segment_id="seg1",
            text="Test segment",
            type="message",
            project_id=project_id,
            created_at=datetime.now(),
            last_touched_at=datetime.now(),
            tokens=100,
            tier="stashed",
        )

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=[mock_segment]
        )
        app_state.storage.unstash_segment = MagicMock(  # type: ignore[method-assign]
            side_effect=RuntimeError("Move failed")
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            query=query,
            move_to_active=True,
        )

        # Assert
        assert "error" not in result
        assert len(result["retrieved_segments"]) == 1
        assert result["moved_to_active"] == []  # Failed to move

    @pytest.mark.asyncio
    async def test_retrieve_value_error(self) -> None:
        """Test retrieve with ValueError."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            side_effect=ValueError("Invalid project")
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            query="test",
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_retrieve_unexpected_error(self) -> None:
        """Test retrieve with unexpected error."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            side_effect=RuntimeError("Unexpected error")
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            query="test",
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INTERNAL_ERROR"

    @pytest.mark.asyncio
    async def test_retrieve_with_datetime_filters(self) -> None:
        """Test retrieve with datetime filters."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        now = datetime.now()
        filters = {
            "created_after": (now - timedelta(days=1)).isoformat(),
            "created_before": now.isoformat(),
        }

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment",
                type="message",
                project_id=project_id,
                created_at=now - timedelta(hours=12),
                last_touched_at=now - timedelta(hours=12),
                tokens=100,
                tier="stashed",
            )
        ]

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        assert len(result["retrieved_segments"]) == 1

    @pytest.mark.asyncio
    async def test_retrieve_with_invalid_datetime_filter(self) -> None:
        """Test retrieve with invalid datetime filter."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = {"created_after": "invalid-datetime"}

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert "datetime format" in result["error"]["message"]


@pytest.mark.unit
class TestContextListProjects:
    """Test context_list_projects tool handler."""

    @pytest.mark.asyncio
    async def test_list_projects_success(self) -> None:
        """Test list_projects with successful result."""
        # Arrange
        app_state = AppState()
        mock_projects = ["project1", "project2", "project3"]
        app_state.storage.list_projects = MagicMock(  # type: ignore[method-assign]
            return_value=mock_projects
        )

        # Act
        result = await handle_list_projects(app_state=app_state)

        # Assert
        assert "error" not in result
        assert result["projects"] == mock_projects
        assert result["count"] == 3
        app_state.storage.list_projects.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_projects_empty(self) -> None:
        """Test list_projects with no projects."""
        # Arrange
        app_state = AppState()
        app_state.storage.list_projects = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Act
        result = await handle_list_projects(app_state=app_state)

        # Assert
        assert "error" not in result
        assert result["projects"] == []
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_list_projects_error(self) -> None:
        """Test list_projects with storage error."""
        # Arrange
        app_state = AppState()
        app_state.storage.list_projects = MagicMock(  # type: ignore[method-assign]
            side_effect=RuntimeError("Storage error")
        )

        # Act
        result = await handle_list_projects(app_state=app_state)

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INTERNAL_ERROR"
        assert "Storage error" in result["error"]["message"]


@pytest.mark.unit
class TestContextSearchStashedAdditional:
    """Additional tests for context_search_stashed to improve coverage."""

    @pytest.mark.asyncio
    async def test_search_with_datetime_filters(self) -> None:
        """Test search with datetime filters."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        now = datetime.now()
        filters = {
            "created_after": (now - timedelta(days=1)).isoformat(),
            "created_before": now.isoformat(),
        }

        # Create segments with different timestamps
        old_segment = ContextSegment(
            segment_id="old",
            text="Old segment",
            type="message",
            project_id=project_id,
            created_at=now - timedelta(days=2),
            last_touched_at=now - timedelta(days=2),
            tokens=100,
            tier="stashed",
        )
        recent_segment = ContextSegment(
            segment_id="recent",
            text="Recent segment",
            type="message",
            project_id=project_id,
            created_at=now - timedelta(hours=12),
            last_touched_at=now - timedelta(hours=12),
            tokens=100,
            tier="stashed",
        )

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=[old_segment, recent_segment]
        )

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        # Only recent segment should pass datetime filter
        assert len(result["segments"]) == 1
        assert result["segments"][0]["segment_id"] == "recent"

    @pytest.mark.asyncio
    async def test_search_with_limit(self) -> None:
        """Test search with limit parameter."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        query = "test"

        # Create multiple segments
        mock_segments = [
            ContextSegment(
                segment_id=f"seg{i}",
                text="Test segment",
                type="message",
                project_id=project_id,
                created_at=datetime.now() - timedelta(hours=i),
                last_touched_at=datetime.now() - timedelta(hours=i),
                tokens=100,
                tier="stashed",
            )
            for i in range(10)
        ]

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
            query=query,
            limit=5,
        )

        # Assert
        assert "error" not in result
        assert len(result["segments"]) == 5
        assert result["total_matches"] == 10  # Total before limit

    @pytest.mark.asyncio
    async def test_search_invalid_created_after(self) -> None:
        """Test search with invalid created_after datetime."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = {"created_after": "invalid-datetime"}

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert "created_after datetime format" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_search_invalid_created_before(self) -> None:
        """Test search with invalid created_before datetime."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = {"created_before": "not-a-date"}

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert "created_before datetime format" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_search_with_empty_query_and_filters(self) -> None:
        """Test search with empty query and no filters."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="stashed",
            )
        ]

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
            query="",
            filters=None,
        )

        # Assert
        assert "error" not in result
        assert len(result["segments"]) == 1

    @pytest.mark.asyncio
    async def test_search_value_error(self) -> None:
        """Test search with ValueError from storage."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            side_effect=ValueError("Invalid search")
        )

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
            query="test",
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert "Invalid search" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_search_unexpected_error(self) -> None:
        """Test search with unexpected error."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            side_effect=RuntimeError("Unexpected error")
        )

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
            query="test",
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INTERNAL_ERROR"
        assert "Unexpected error" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_search_with_datetime_filtering(self) -> None:
        """Test search applies datetime filters in _format_search_results."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        now = datetime.now()
        filters = {
            "created_after": (now - timedelta(days=1)).isoformat(),
            "created_before": now.isoformat(),
        }

        # Create segments - one before, one within, one after
        before_segment = ContextSegment(
            segment_id="before",
            text="Before",
            type="message",
            project_id=project_id,
            created_at=now - timedelta(days=2),
            last_touched_at=now - timedelta(days=2),
            tokens=100,
            tier="stashed",
        )
        within_segment = ContextSegment(
            segment_id="within",
            text="Within",
            type="message",
            project_id=project_id,
            created_at=now - timedelta(hours=12),
            last_touched_at=now - timedelta(hours=12),
            tokens=100,
            tier="stashed",
        )
        after_segment = ContextSegment(
            segment_id="after",
            text="After",
            type="message",
            project_id=project_id,
            created_at=now + timedelta(days=1),
            last_touched_at=now + timedelta(days=1),
            tokens=100,
            tier="stashed",
        )

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=[before_segment, within_segment, after_segment]
        )

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        # Only within_segment should pass both filters
        assert len(result["segments"]) == 1
        assert result["segments"][0]["segment_id"] == "within"


@pytest.mark.unit
class TestContextStashAdditional:
    """Additional tests for context_stash to improve coverage."""

    @pytest.mark.asyncio
    async def test_stash_with_datetime_filters(self) -> None:
        """Test stash with datetime filters."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        now = datetime.now()
        filters = {
            "created_after": (now - timedelta(days=1)).isoformat(),
            "created_before": now.isoformat(),
        }

        # Create segments with different timestamps
        old_segment = ContextSegment(
            segment_id="old",
            text="Old segment",
            type="message",
            project_id=project_id,
            created_at=now - timedelta(days=2),
            last_touched_at=now - timedelta(days=2),
            tokens=100,
            tier="working",
        )
        recent_segment = ContextSegment(
            segment_id="recent",
            text="Recent segment",
            type="message",
            project_id=project_id,
            created_at=now - timedelta(hours=12),
            last_touched_at=now - timedelta(hours=12),
            tokens=100,
            tier="working",
        )

        mock_working_set = WorkingSet(
            segments=[old_segment, recent_segment],
            total_tokens=200,
            project_id=project_id,
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        mock_stash_result = StashResult(
            stashed_segments=["recent"],
            tokens_freed=100,
            stash_location=None,
        )
        app_state.context_manager.stash_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_stash_result
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        assert result["stashed_segments"] == ["recent"]  # Only recent segment matches

    @pytest.mark.asyncio
    async def test_stash_with_tags_filter(self) -> None:
        """Test stash with tags filter."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = {"tags": ["important", "urgent"]}

        # Create segments with different tags
        segment_with_tags = ContextSegment(
            segment_id="tagged",
            text="Tagged segment",
            type="message",
            project_id=project_id,
            created_at=datetime.now(),
            last_touched_at=datetime.now(),
            tokens=100,
            tier="working",
            tags=["important", "urgent", "other"],
        )
        segment_without_tags = ContextSegment(
            segment_id="untagged",
            text="Untagged segment",
            type="message",
            project_id=project_id,
            created_at=datetime.now(),
            last_touched_at=datetime.now(),
            tokens=100,
            tier="working",
            tags=[],
        )

        mock_working_set = WorkingSet(
            segments=[segment_with_tags, segment_without_tags],
            total_tokens=200,
            project_id=project_id,
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        mock_stash_result = StashResult(
            stashed_segments=["tagged"],
            tokens_freed=100,
            stash_location=None,
        )
        app_state.context_manager.stash_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_stash_result
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        assert result["stashed_segments"] == ["tagged"]  # Only tagged segment matches

    @pytest.mark.asyncio
    async def test_stash_with_invalid_datetime_filter(self) -> None:
        """Test stash with invalid datetime filter."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = {"created_after": "invalid-datetime"}

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="working",
            )
        ]

        mock_working_set = WorkingSet(
            segments=mock_segments,
            total_tokens=100,
            project_id=project_id,
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert - invalid datetime is logged as warning but filter is ignored
        # All segments will match since invalid filter is ignored
        assert "error" not in result
        # The invalid datetime filter is ignored, so all segments match
        assert result["segments_matched"] == 1

    @pytest.mark.asyncio
    async def test_stash_with_file_path_filter(self) -> None:
        """Test stash with file_path filter."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = {"file_path": "test.py"}

        segment_with_path = ContextSegment(
            segment_id="with_path",
            text="Code segment",
            type="code",
            project_id=project_id,
            created_at=datetime.now(),
            last_touched_at=datetime.now(),
            tokens=100,
            tier="working",
            file_path="test.py",
        )
        segment_without_path = ContextSegment(
            segment_id="without_path",
            text="Message segment",
            type="message",
            project_id=project_id,
            created_at=datetime.now(),
            last_touched_at=datetime.now(),
            tokens=100,
            tier="working",
        )

        mock_working_set = WorkingSet(
            segments=[segment_with_path, segment_without_path],
            total_tokens=200,
            project_id=project_id,
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        mock_stash_result = StashResult(
            stashed_segments=["with_path"],
            tokens_freed=100,
            stash_location=None,
        )
        app_state.context_manager.stash_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_stash_result
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        assert result["stashed_segments"] == ["with_path"]

    @pytest.mark.asyncio
    async def test_stash_with_task_id_filter(self) -> None:
        """Test stash with task_id filter."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = {"task_id": "task-123"}

        segment_with_task = ContextSegment(
            segment_id="with_task",
            text="Task segment",
            type="message",
            project_id=project_id,
            created_at=datetime.now(),
            last_touched_at=datetime.now(),
            tokens=100,
            tier="working",
            task_id="task-123",
        )
        segment_without_task = ContextSegment(
            segment_id="without_task",
            text="No task segment",
            type="message",
            project_id=project_id,
            created_at=datetime.now(),
            last_touched_at=datetime.now(),
            tokens=100,
            tier="working",
        )

        mock_working_set = WorkingSet(
            segments=[segment_with_task, segment_without_task],
            total_tokens=200,
            project_id=project_id,
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        mock_stash_result = StashResult(
            stashed_segments=["with_task"],
            tokens_freed=100,
            stash_location=None,
        )
        app_state.context_manager.stash_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_stash_result
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        assert result["stashed_segments"] == ["with_task"]

    @pytest.mark.asyncio
    async def test_stash_with_type_filter(self) -> None:
        """Test stash with type filter."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = {"type": "code"}

        code_segment = ContextSegment(
            segment_id="code",
            text="Code",
            type="code",
            project_id=project_id,
            created_at=datetime.now(),
            last_touched_at=datetime.now(),
            tokens=100,
            tier="working",
        )
        message_segment = ContextSegment(
            segment_id="message",
            text="Message",
            type="message",
            project_id=project_id,
            created_at=datetime.now(),
            last_touched_at=datetime.now(),
            tokens=100,
            tier="working",
        )

        mock_working_set = WorkingSet(
            segments=[code_segment, message_segment],
            total_tokens=200,
            project_id=project_id,
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        mock_stash_result = StashResult(
            stashed_segments=["code"],
            tokens_freed=100,
            stash_location=None,
        )
        app_state.context_manager.stash_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_stash_result
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        assert result["stashed_segments"] == ["code"]

    @pytest.mark.asyncio
    async def test_stash_with_all_filters_combined(self) -> None:
        """Test stash with multiple filters combined."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        now = datetime.now()
        filters = {
            "type": "message",
            "file_path": "test.py",
            "tags": ["important"],
            "created_after": (now - timedelta(days=1)).isoformat(),
        }

        # Create segment that matches all filters
        matching_segment = ContextSegment(
            segment_id="matching",
            text="Matching segment",
            type="message",
            project_id=project_id,
            created_at=now - timedelta(hours=12),
            last_touched_at=now - timedelta(hours=12),
            tokens=100,
            tier="working",
            file_path="test.py",
            tags=["important", "other"],
        )

        # Create segment that doesn't match
        non_matching_segment = ContextSegment(
            segment_id="non_matching",
            text="Non-matching segment",
            type="code",  # Different type
            project_id=project_id,
            created_at=now - timedelta(hours=12),
            last_touched_at=now - timedelta(hours=12),
            tokens=100,
            tier="working",
        )

        mock_working_set = WorkingSet(
            segments=[matching_segment, non_matching_segment],
            total_tokens=200,
            project_id=project_id,
            task_id=None,
            last_updated=datetime.now(),
        )
        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        mock_stash_result = StashResult(
            stashed_segments=["matching"],
            tokens_freed=100,
            stash_location=None,
        )
        app_state.context_manager.stash_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_stash_result
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        assert result["stashed_segments"] == ["matching"]
        assert result["segments_matched"] == 1


@pytest.mark.unit
class TestStashingToolsRegistration:
    """Test stashing tools registration."""

    def test_register_stashing_tools(self) -> None:
        """Test that stashing tools are registered correctly."""
        # Arrange
        registry = ToolRegistry()
        app_state = AppState()

        # Act
        register_stashing_tools(registry, app_state)

        # Assert
        tools = registry.list_tools()
        tool_names = {tool.name for tool in tools}
        assert "context_stash" in tool_names
        assert "context_search_stashed" in tool_names
        assert "context_retrieve_stashed" in tool_names
        assert "context_list_projects" in tool_names
