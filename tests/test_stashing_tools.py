"""Unit tests for stashing tools."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.models import ContextSegment, StashResult
from hjeon139_mcp_outofcontext.tool_registry import ToolRegistry
from hjeon139_mcp_outofcontext.tools.stashing import (
    handle_retrieve_stashed,
    handle_search_stashed,
    handle_stash,
    register_stashing_tools,
)


@pytest.mark.unit
class TestContextStash:
    """Test context_stash tool handler."""

    @pytest.mark.asyncio
    async def test_stash_with_valid_parameters(self) -> None:
        """Test stash with valid parameters."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        segment_ids = ["seg1", "seg2"]

        # Mock context manager
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
            segment_ids=segment_ids,
        )

        # Assert
        assert "error" not in result
        assert result["stashed_segments"] == ["seg1", "seg2"]
        assert result["tokens_stashed"] == 300
        assert result["errors"] == []
        app_state.context_manager.stash_segments.assert_called_once_with(
            segment_ids=segment_ids, project_id=project_id
        )

    @pytest.mark.asyncio
    async def test_stash_missing_project_id(self) -> None:
        """Test stash with missing project_id."""
        # Arrange
        app_state = AppState()

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=None,
            segment_ids=["seg1"],
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert result["error"]["message"] == "project_id is required"

    @pytest.mark.asyncio
    async def test_stash_empty_segment_ids(self) -> None:
        """Test stash with empty segment_ids."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            segment_ids=[],
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert result["error"]["message"] == "segment_ids cannot be empty"

    @pytest.mark.asyncio
    async def test_stash_invalid_parameters(self) -> None:
        """Test stash with invalid parameters."""
        # Arrange
        app_state = AppState()

        # Act - passing invalid type for segment_ids
        result = await handle_stash(
            app_state=app_state,
            project_id="test-project",
            segment_ids="not-a-list",  # type: ignore[arg-type]
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
        segment_ids = ["seg1"]

        app_state.context_manager.stash_segments = MagicMock(  # type: ignore[method-assign]
            side_effect=ValueError("Invalid segment")
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
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
        segment_ids = ["seg1"]

        app_state.context_manager.stash_segments = MagicMock(  # type: ignore[method-assign]
            side_effect=RuntimeError("Unexpected error")
        )

        # Act
        result = await handle_stash(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
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
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" not in result
        assert len(result["segments"]) == 1

    @pytest.mark.asyncio
    async def test_search_with_limit(self) -> None:
        """Test search with result limit."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        limit = 2

        # Create 5 segments
        mock_segments = [
            ContextSegment(
                segment_id=f"seg{i}",
                text=f"Test segment {i}",
                type="message",
                project_id=project_id,
                created_at=datetime.now() - timedelta(hours=i),
                last_touched_at=datetime.now() - timedelta(hours=i),
                tokens=100,
                tier="stashed",
            )
            for i in range(5)
        ]

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
            limit=limit,
        )

        # Assert
        assert "error" not in result
        assert len(result["segments"]) == limit
        assert result["total_matches"] == 5

    @pytest.mark.asyncio
    async def test_search_empty_query(self) -> None:
        """Test search with empty query returns all segments."""
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
        )

        # Assert
        assert "error" not in result
        assert result["query"] == ""

    @pytest.mark.asyncio
    async def test_search_missing_project_id(self) -> None:
        """Test search without project_id searches across all projects."""
        # Arrange
        app_state = AppState()

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

    @pytest.mark.asyncio
    async def test_search_invalid_datetime_format(self) -> None:
        """Test search with invalid datetime format."""
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
    async def test_search_invalid_datetime_type(self) -> None:
        """Test search with invalid datetime type."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        filters = {"created_after": 12345}  # type: ignore[dict-item]

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
            filters=filters,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_search_value_error(self) -> None:
        """Test search with ValueError."""
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
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

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
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INTERNAL_ERROR"

    @pytest.mark.asyncio
    async def test_search_with_datetime_filtering(self) -> None:
        """Test search with datetime filters applied after search."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        now = datetime.now()
        filters = {
            "created_after": (now - timedelta(days=1)).isoformat(),
            "created_before": now.isoformat(),
        }

        # Create segments with different timestamps
        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment 1",
                type="message",
                project_id=project_id,
                created_at=now - timedelta(hours=12),  # Within range
                last_touched_at=now - timedelta(hours=12),
                tokens=100,
                tier="stashed",
            ),
            ContextSegment(
                segment_id="seg2",
                text="Test segment 2",
                type="message",
                project_id=project_id,
                created_at=now - timedelta(days=2),  # Outside range
                last_touched_at=now - timedelta(days=2),
                tokens=200,
                tier="stashed",
            ),
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
        assert len(result["segments"]) == 1  # Only seg1 should pass filter
        assert result["segments"][0]["segment_id"] == "seg1"

    @pytest.mark.asyncio
    async def test_search_sorts_by_recency(self) -> None:
        """Test search results are sorted by recency."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        now = datetime.now()

        # Create segments with different timestamps (oldest first)
        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Oldest segment",
                type="message",
                project_id=project_id,
                created_at=now - timedelta(hours=10),
                last_touched_at=now - timedelta(hours=10),
                tokens=100,
                tier="stashed",
            ),
            ContextSegment(
                segment_id="seg2",
                text="Newest segment",
                type="message",
                project_id=project_id,
                created_at=now - timedelta(hours=1),
                last_touched_at=now - timedelta(hours=1),
                tokens=200,
                tier="stashed",
            ),
            ContextSegment(
                segment_id="seg3",
                text="Middle segment",
                type="message",
                project_id=project_id,
                created_at=now - timedelta(hours=5),
                last_touched_at=now - timedelta(hours=5),
                tokens=150,
                tier="stashed",
            ),
        ]

        app_state.storage.search_stashed = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Act
        result = await handle_search_stashed(
            app_state=app_state,
            project_id=project_id,
        )

        # Assert
        assert "error" not in result
        assert len(result["segments"]) == 3
        # Should be sorted by recency (most recent first)
        assert result["segments"][0]["segment_id"] == "seg2"  # Newest
        assert result["segments"][1]["segment_id"] == "seg3"  # Middle
        assert result["segments"][2]["segment_id"] == "seg1"  # Oldest

    @pytest.mark.asyncio
    async def test_search_with_zero_limit(self) -> None:
        """Test search with limit=0 doesn't apply limit (0 is falsy)."""
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
            limit=0,
        )

        # Assert
        assert "error" not in result
        assert len(result["segments"]) == 1  # Limit=0 doesn't apply (falsy check)
        assert result["total_matches"] == 1

    @pytest.mark.asyncio
    async def test_search_with_negative_limit(self) -> None:
        """Test search with negative limit returns all results."""
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
            limit=-1,
        )

        # Assert
        assert "error" not in result
        assert len(result["segments"]) == 1  # Negative limit ignored


@pytest.mark.unit
class TestContextRetrieveStashed:
    """Test context_retrieve_stashed tool handler."""

    @pytest.mark.asyncio
    async def test_retrieve_without_move_to_active(self) -> None:
        """Test retrieve without moving to active."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        segment_ids = ["seg1", "seg2"]

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

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
            move_to_active=False,
        )

        # Assert
        assert "error" not in result
        assert len(result["retrieved_segments"]) == 2
        assert result["moved_to_active"] == []

    @pytest.mark.asyncio
    async def test_retrieve_with_move_to_active(self) -> None:
        """Test retrieve with move_to_active=True."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        segment_ids = ["seg1"]

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

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=[mock_segment]
        )
        app_state.storage.unstash_segment = MagicMock()  # type: ignore[method-assign]
        app_state.context_manager.working_sets = {project_id: {}}

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
            move_to_active=True,
        )

        # Assert
        assert "error" not in result
        assert len(result["retrieved_segments"]) == 1
        assert result["moved_to_active"] == ["seg1"]
        app_state.storage.unstash_segment.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_filters_working_tier(self) -> None:
        """Test retrieve only returns stashed segments."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        segment_ids = ["seg1", "seg2"]

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
                tier="working",  # Not stashed
            ),
        ]

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
        )

        # Assert
        assert "error" not in result
        assert len(result["retrieved_segments"]) == 1
        assert result["retrieved_segments"][0]["segment_id"] == "seg1"

    @pytest.mark.asyncio
    async def test_retrieve_missing_project_id(self) -> None:
        """Test retrieve with missing project_id."""
        # Arrange
        app_state = AppState()

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=None,
            segment_ids=["seg1"],
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert result["error"]["message"] == "project_id is required"

    @pytest.mark.asyncio
    async def test_retrieve_empty_segment_ids(self) -> None:
        """Test retrieve with empty segment_ids."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            segment_ids=[],
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert result["error"]["message"] == "segment_ids cannot be empty"

    @pytest.mark.asyncio
    async def test_retrieve_invalid_parameters(self) -> None:
        """Test retrieve with invalid parameters."""
        # Arrange
        app_state = AppState()

        # Act - passing invalid type for segment_ids
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id="test-project",
            segment_ids="not-a-list",  # type: ignore[arg-type]
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_retrieve_error_during_move(self) -> None:
        """Test retrieve handles error during move to active."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        segment_ids = ["seg1"]

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

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=[mock_segment]
        )
        app_state.storage.unstash_segment = MagicMock(  # type: ignore[method-assign]
            side_effect=RuntimeError("Move failed")
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
            move_to_active=True,
        )

        # Assert
        assert "error" not in result
        assert len(result["retrieved_segments"]) == 1
        assert result["moved_to_active"] == []  # Failed to move

    @pytest.mark.asyncio
    async def test_retrieve_no_working_sets_attribute(self) -> None:
        """Test retrieve when context_manager has no working_sets."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        segment_ids = ["seg1"]

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

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=[mock_segment]
        )
        app_state.storage.unstash_segment = MagicMock()  # type: ignore[method-assign]
        # Don't set working_sets attribute

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
            move_to_active=True,
        )

        # Assert
        assert "error" not in result
        assert len(result["retrieved_segments"]) == 1

    @pytest.mark.asyncio
    async def test_retrieve_value_error(self) -> None:
        """Test retrieve with ValueError."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        segment_ids = ["seg1"]

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            side_effect=ValueError("Invalid project")
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
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
        segment_ids = ["seg1"]

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            side_effect=RuntimeError("Unexpected error")
        )

        # Act
        result = await handle_retrieve_stashed(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INTERNAL_ERROR"


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
