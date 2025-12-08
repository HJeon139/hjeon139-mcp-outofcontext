"""Unit tests for pruning tools."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.models import (
    ContextSegment,
    PruningCandidate,
    PruningPlan,
)
from hjeon139_mcp_outofcontext.tool_registry import ToolRegistry
from hjeon139_mcp_outofcontext.tools.pruning import (
    handle_gc_analyze,
    handle_gc_pin,
    handle_gc_prune,
    handle_gc_unpin,
    register_pruning_tools,
)


@pytest.mark.unit
class TestGCAnalyze:
    """Test context_gc_analyze tool handler."""

    @pytest.mark.asyncio
    async def test_gc_analyze_with_valid_parameters(self) -> None:
        """Test gc_analyze with valid parameters."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        # Create mock segments
        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment 1",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now() - timedelta(hours=2),
                tokens=100,
                tier="working",
            ),
            ContextSegment(
                segment_id="seg2",
                text="Test segment 2",
                type="log",
                project_id=project_id,
                created_at=datetime.now() - timedelta(hours=10),
                last_touched_at=datetime.now() - timedelta(hours=10),
                tokens=200,
                tier="working",
            ),
        ]

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Mock GC engine
        mock_candidates = [
            PruningCandidate(
                segment_id="seg2",
                score=0.8,
                tokens=200,
                reason="old (10.0h), low-value type (log)",
                segment_type="log",
                age_hours=10.0,
            )
        ]
        app_state.gc_engine.analyze_pruning_candidates = MagicMock(  # type: ignore[method-assign]
            return_value=mock_candidates
        )

        # Act
        result = await handle_gc_analyze(
            app_state=app_state,
            project_id=project_id,
        )

        # Assert
        assert "error" not in result
        assert result["total_candidates"] == 1
        assert result["estimated_tokens_freed"] == 200
        assert len(result["pruning_candidates"]) == 1
        assert result["pruning_candidates"][0]["segment_id"] == "seg2"

    @pytest.mark.asyncio
    async def test_gc_analyze_with_target_tokens(self) -> None:
        """Test gc_analyze with target_tokens generates pruning plan."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment",
                type="log",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="working",
            )
        ]

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        mock_candidates = [
            PruningCandidate(
                segment_id="seg1",
                score=0.8,
                tokens=100,
                reason="low-value type (log)",
                segment_type="log",
                age_hours=0.1,
            )
        ]

        mock_plan = PruningPlan(
            candidates=mock_candidates,
            total_tokens_freed=100,
            stash_segments=[],
            delete_segments=["seg1"],
            reason="delete 1 segment(s) to target met",
        )

        app_state.gc_engine.analyze_pruning_candidates = MagicMock(  # type: ignore[method-assign]
            return_value=mock_candidates
        )
        app_state.gc_engine.generate_pruning_plan = MagicMock(  # type: ignore[method-assign]
            return_value=mock_plan
        )

        # Act
        result = await handle_gc_analyze(
            app_state=app_state,
            project_id=project_id,
            target_tokens=50,
        )

        # Assert
        assert "error" not in result
        assert "pruning_plan" in result
        assert result["pruning_plan"]["total_tokens_freed"] == 100
        assert result["pruning_plan"]["delete_segments"] == ["seg1"]

    @pytest.mark.asyncio
    async def test_gc_analyze_with_missing_project_id(self) -> None:
        """Test gc_analyze with missing project_id returns error."""
        # Arrange
        app_state = AppState()

        # Act
        result = await handle_gc_analyze(
            app_state=app_state,
            project_id=None,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert "project_id is required" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_gc_analyze_with_context_descriptors(self) -> None:
        """Test gc_analyze with context descriptors builds root set."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        context_descriptors = {
            "recent_messages": [],
            "current_file": {"path": "/test/file.py"},
            "token_usage": {"current": 1000, "limit": 32000, "usage_percent": 3.125},
            "segment_summaries": [],
            "task_info": None,
        }

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment",
                type="code",
                project_id=project_id,
                file_path="/test/file.py",
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                tier="working",
            )
        ]

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        app_state.gc_engine.analyze_pruning_candidates = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Act
        result = await handle_gc_analyze(
            app_state=app_state,
            project_id=project_id,
            context_descriptors=context_descriptors,
        )

        # Assert
        assert "error" not in result
        # Verify root set was built (seg1 should be in roots)
        call_args = app_state.gc_engine.analyze_pruning_candidates.call_args
        assert call_args is not None
        roots = call_args[0][1]  # Second positional argument is roots
        assert "seg1" in roots


@pytest.mark.unit
class TestGCPrune:
    """Test context_gc_prune tool handler."""

    @pytest.mark.asyncio
    async def test_gc_prune_stash_action(self) -> None:
        """Test gc_prune with stash action."""
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
                pinned=False,
                tier="working",
            ),
            ContextSegment(
                segment_id="seg2",
                text="Test segment 2",
                type="log",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=200,
                pinned=False,
                tier="working",
            ),
        ]

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )
        app_state.storage.stash_segment = MagicMock()  # type: ignore[method-assign]

        # Mock context manager working_sets
        app_state.context_manager.working_sets = {project_id: {}}

        # Act
        result = await handle_gc_prune(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
            action="stash",
        )

        # Assert
        assert "error" not in result
        assert result["action"] == "stashed"
        assert len(result["pruned_segments"]) == 2
        assert result["tokens_freed"] == 300
        assert len(result["errors"]) == 0
        assert app_state.storage.stash_segment.call_count == 2

    @pytest.mark.asyncio
    async def test_gc_prune_delete_action(self) -> None:
        """Test gc_prune with delete action and confirmation."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        segment_ids = ["seg1"]

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment",
                type="log",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                pinned=False,
                tier="working",
            )
        ]

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )
        app_state.storage.delete_segment = MagicMock()  # type: ignore[method-assign]

        app_state.context_manager.working_sets = {project_id: {}}

        # Act
        result = await handle_gc_prune(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
            action="delete",
            confirm=True,
        )

        # Assert
        assert "error" not in result
        assert result["action"] == "deleted"
        assert len(result["pruned_segments"]) == 1
        assert result["tokens_freed"] == 100
        assert app_state.storage.delete_segment.call_count == 1

    @pytest.mark.asyncio
    async def test_gc_prune_delete_without_confirm(self) -> None:
        """Test gc_prune delete action without confirmation returns error."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        # Act
        result = await handle_gc_prune(
            app_state=app_state,
            project_id=project_id,
            segment_ids=["seg1"],
            action="delete",
            confirm=False,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "CONFIRMATION_REQUIRED"
        assert "confirm=True is required" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_gc_prune_pinned_segment(self) -> None:
        """Test gc_prune with pinned segment returns error."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        segment_ids = ["seg1"]

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
                pinned=True,  # Pinned!
                tier="working",
            )
        ]

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Act
        result = await handle_gc_prune(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
            action="stash",
        )

        # Assert
        assert "error" not in result  # No error, but segment not pruned
        assert len(result["pruned_segments"]) == 0
        assert len(result["errors"]) == 1
        assert "pinned" in result["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_gc_prune_segment_not_found(self) -> None:
        """Test gc_prune with non-existent segment returns error."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Act
        result = await handle_gc_prune(
            app_state=app_state,
            project_id=project_id,
            segment_ids=["nonexistent"],
            action="stash",
        )

        # Assert
        assert "error" not in result
        assert len(result["pruned_segments"]) == 0
        assert len(result["errors"]) == 1
        assert "not found" in result["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_gc_prune_missing_project_id(self) -> None:
        """Test gc_prune with missing project_id returns error."""
        # Arrange
        app_state = AppState()

        # Act
        result = await handle_gc_prune(
            app_state=app_state,
            project_id=None,
            segment_ids=["seg1"],
            action="stash",
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"


@pytest.mark.unit
class TestGCPin:
    """Test context_gc_pin tool handler."""

    @pytest.mark.asyncio
    async def test_gc_pin_success(self) -> None:
        """Test gc_pin successfully pins segments."""
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
                pinned=False,
                tokens=100,
            ),
            ContextSegment(
                segment_id="seg2",
                text="Test segment 2",
                type="code",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                pinned=False,
                tokens=200,
            ),
        ]

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )
        app_state.storage.update_segment = MagicMock()  # type: ignore[method-assign]

        # Act
        result = await handle_gc_pin(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
        )

        # Assert
        assert "error" not in result
        assert len(result["pinned_segments"]) == 2
        assert len(result["errors"]) == 0
        assert app_state.storage.update_segment.call_count == 2

        # Verify segments were pinned
        for call in app_state.storage.update_segment.call_args_list:
            segment = call[0][0]  # First positional argument
            assert segment.pinned is True

    @pytest.mark.asyncio
    async def test_gc_pin_segment_not_found(self) -> None:
        """Test gc_pin with non-existent segment returns error."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Act
        result = await handle_gc_pin(
            app_state=app_state,
            project_id=project_id,
            segment_ids=["nonexistent"],
        )

        # Assert
        assert "error" not in result
        assert len(result["pinned_segments"]) == 0
        assert len(result["errors"]) == 1
        assert "not found" in result["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_gc_pin_missing_project_id(self) -> None:
        """Test gc_pin with missing project_id returns error."""
        # Arrange
        app_state = AppState()

        # Act
        result = await handle_gc_pin(
            app_state=app_state,
            project_id=None,
            segment_ids=["seg1"],
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"


@pytest.mark.unit
class TestGCUnpin:
    """Test context_gc_unpin tool handler."""

    @pytest.mark.asyncio
    async def test_gc_unpin_success(self) -> None:
        """Test gc_unpin successfully unpins segments."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        segment_ids = ["seg1"]

        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                pinned=True,  # Currently pinned
                tokens=100,
            )
        ]

        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )
        app_state.storage.update_segment = MagicMock()  # type: ignore[method-assign]

        # Act
        result = await handle_gc_unpin(
            app_state=app_state,
            project_id=project_id,
            segment_ids=segment_ids,
        )

        # Assert
        assert "error" not in result
        assert len(result["unpinned_segments"]) == 1
        assert len(result["errors"]) == 0

        # Verify segment was unpinned
        call = app_state.storage.update_segment.call_args
        assert call is not None
        segment = call[0][0]  # First positional argument
        assert segment.pinned is False

    @pytest.mark.asyncio
    async def test_gc_unpin_missing_project_id(self) -> None:
        """Test gc_unpin with missing project_id returns error."""
        # Arrange
        app_state = AppState()

        # Act
        result = await handle_gc_unpin(
            app_state=app_state,
            project_id=None,
            segment_ids=["seg1"],
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"


@pytest.mark.unit
class TestRegisterPruningTools:
    """Test pruning tools registration."""

    def test_register_pruning_tools(self) -> None:
        """Test that pruning tools are registered correctly."""
        # Arrange
        registry = ToolRegistry()
        app_state = AppState()

        # Act
        register_pruning_tools(registry, app_state)

        # Assert
        tools = registry.list_tools()
        tool_names = [tool.name for tool in tools]

        assert "context_gc_analyze" in tool_names
        assert "context_gc_prune" in tool_names
        assert "context_gc_pin" in tool_names
        assert "context_gc_unpin" in tool_names

        # Verify handlers are registered
        assert registry.get_tool("context_gc_analyze") is not None
        assert registry.get_tool("context_gc_prune") is not None
        assert registry.get_tool("context_gc_pin") is not None
        assert registry.get_tool("context_gc_unpin") is not None
