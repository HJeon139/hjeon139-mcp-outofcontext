"""Unit tests for monitoring tools."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from hjeon139_mcp_outofcontext.app_state import AppState
from hjeon139_mcp_outofcontext.models import (
    AnalysisResult,
    ContextSegment,
    HealthScore,
    Recommendation,
    UsageMetrics,
    WorkingSet,
)
from hjeon139_mcp_outofcontext.monitoring_tools import (
    handle_analyze_usage,
    handle_get_working_set,
    register_monitoring_tools,
)
from hjeon139_mcp_outofcontext.tool_registry import ToolRegistry


@pytest.mark.unit
class TestAnalyzeUsage:
    """Test context_analyze_usage tool handler."""

    @pytest.mark.asyncio
    async def test_analyze_usage_with_valid_parameters(self) -> None:
        """Test analyze_usage with valid parameters."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        # Mock context manager
        mock_analysis_result = AnalysisResult(
            total_tokens=1000,
            segment_count=10,
            usage_percent=50.0,
            health_score=HealthScore(score=75.0, usage_percent=50.0, factors={}),
            recommendations=["Test recommendation"],
        )
        app_state.context_manager.analyze_context = MagicMock(  # type: ignore[method-assign]
            return_value=mock_analysis_result
        )

        # Mock storage
        mock_segments = [
            ContextSegment(
                segment_id="seg1",
                text="Test segment",
                type="message",
                project_id=project_id,
                created_at=datetime.now(),
                last_touched_at=datetime.now(),
                tokens=100,
            )
        ]
        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=mock_segments
        )

        # Mock analysis engine
        mock_metrics = UsageMetrics(
            total_tokens=1000,
            total_segments=10,
            tokens_by_type={"message": 1000},
            segments_by_type={"message": 10},
            tokens_by_task={},
            oldest_segment_age_hours=1.0,
            newest_segment_age_hours=0.1,
            pinned_segments_count=0,
            pinned_tokens=0,
            usage_percent=50.0,
            estimated_remaining_tokens=15000,
        )
        app_state.analysis_engine.analyze_context_usage = MagicMock(  # type: ignore[method-assign]
            return_value=mock_metrics
        )
        app_state.analysis_engine.generate_recommendations = MagicMock(  # type: ignore[method-assign]
            return_value=[
                Recommendation(priority="low", message="Test recommendation", action=None)
            ]
        )

        # Mock GC engine
        app_state.gc_engine.analyze_pruning_candidates = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Act
        result = await handle_analyze_usage(
            app_state=app_state,
            project_id=project_id,
            token_limit=32000,
        )

        # Assert
        assert "error" not in result
        assert "usage_metrics" in result
        assert "health_score" in result
        assert "recommendations" in result
        assert "pruning_candidates_count" in result
        assert result["pruning_candidates_count"] == 0
        app_state.context_manager.analyze_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_usage_missing_project_id(self) -> None:
        """Test analyze_usage with missing project_id."""
        # Arrange
        app_state = AppState()

        # Act
        result = await handle_analyze_usage(app_state=app_state, project_id=None)

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert "project_id is required" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_analyze_usage_with_context_descriptors(self) -> None:
        """Test analyze_usage with context descriptors."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        context_descriptors = {
            "recent_messages": [],
            "token_usage": {"current": 1000, "limit": 32000, "usage_percent": 3.125},
            "segment_summaries": [],
        }

        # Mock context manager
        mock_analysis_result = AnalysisResult(
            total_tokens=1000,
            segment_count=10,
            usage_percent=50.0,
            health_score=HealthScore(score=75.0, usage_percent=50.0, factors={}),
            recommendations=[],
        )
        app_state.context_manager.analyze_context = MagicMock(  # type: ignore[method-assign]
            return_value=mock_analysis_result
        )

        # Mock storage
        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Mock analysis engine
        mock_metrics = UsageMetrics(
            total_tokens=1000,
            total_segments=10,
            tokens_by_type={},
            segments_by_type={},
            tokens_by_task={},
            oldest_segment_age_hours=0.0,
            newest_segment_age_hours=0.0,
            pinned_segments_count=0,
            pinned_tokens=0,
            usage_percent=50.0,
            estimated_remaining_tokens=15000,
        )
        app_state.analysis_engine.analyze_context_usage = MagicMock(  # type: ignore[method-assign]
            return_value=mock_metrics
        )
        app_state.analysis_engine.generate_recommendations = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Mock GC engine
        app_state.gc_engine.analyze_pruning_candidates = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Act
        result = await handle_analyze_usage(
            app_state=app_state,
            context_descriptors=context_descriptors,
            project_id=project_id,
        )

        # Assert
        assert "error" not in result
        app_state.context_manager.analyze_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_usage_with_custom_token_limit(self) -> None:
        """Test analyze_usage with custom token limit."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        token_limit = 16000

        # Mock context manager
        mock_analysis_result = AnalysisResult(
            total_tokens=1000,
            segment_count=10,
            usage_percent=50.0,
            health_score=HealthScore(score=75.0, usage_percent=50.0, factors={}),
            recommendations=[],
        )
        app_state.context_manager.analyze_context = MagicMock(  # type: ignore[method-assign]
            return_value=mock_analysis_result
        )

        # Mock storage
        app_state.storage.load_segments = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Mock analysis engine
        mock_metrics = UsageMetrics(
            total_tokens=1000,
            total_segments=10,
            tokens_by_type={},
            segments_by_type={},
            tokens_by_task={},
            oldest_segment_age_hours=0.0,
            newest_segment_age_hours=0.0,
            pinned_segments_count=0,
            pinned_tokens=0,
            usage_percent=50.0,
            estimated_remaining_tokens=15000,
        )
        app_state.analysis_engine.analyze_context_usage = MagicMock(  # type: ignore[method-assign]
            return_value=mock_metrics
        )
        app_state.analysis_engine.generate_recommendations = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Mock GC engine
        app_state.gc_engine.analyze_pruning_candidates = MagicMock(  # type: ignore[method-assign]
            return_value=[]
        )

        # Act
        result = await handle_analyze_usage(
            app_state=app_state,
            project_id=project_id,
            token_limit=token_limit,
        )

        # Assert
        assert "error" not in result
        # Verify token_limit was used
        call_args = app_state.context_manager.analyze_context.call_args
        descriptors = call_args[1]["descriptors"]
        assert descriptors.token_usage.limit == token_limit


@pytest.mark.unit
class TestGetWorkingSet:
    """Test context_get_working_set tool handler."""

    @pytest.mark.asyncio
    async def test_get_working_set_with_valid_parameters(self) -> None:
        """Test get_working_set with valid parameters."""
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
        result = await handle_get_working_set(
            app_state=app_state,
            project_id=project_id,
        )

        # Assert
        assert "error" not in result
        assert "working_set" in result
        assert "segments" in result
        assert "total_tokens" in result
        assert "segment_count" in result
        assert result["total_tokens"] == 100
        assert result["segment_count"] == 1
        app_state.context_manager.get_working_set.assert_called_once_with(
            project_id=project_id, task_id=None
        )

    @pytest.mark.asyncio
    async def test_get_working_set_missing_project_id(self) -> None:
        """Test get_working_set with missing project_id."""
        # Arrange
        app_state = AppState()

        # Act
        result = await handle_get_working_set(app_state=app_state, project_id=None)

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"
        assert "project_id is required" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_get_working_set_with_task_id(self) -> None:
        """Test get_working_set with specific task_id."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"
        task_id = "test-task"

        mock_working_set = WorkingSet(
            segments=[],
            total_tokens=0,
            project_id=project_id,
            task_id=task_id,
            last_updated=datetime.now(),
        )

        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            return_value=mock_working_set
        )

        # Act
        result = await handle_get_working_set(
            app_state=app_state,
            project_id=project_id,
            task_id=task_id,
        )

        # Assert
        assert "error" not in result
        app_state.context_manager.get_working_set.assert_called_once_with(
            project_id=project_id, task_id=task_id
        )

    @pytest.mark.asyncio
    async def test_get_working_set_handles_value_error(self) -> None:
        """Test get_working_set handles ValueError from context manager."""
        # Arrange
        app_state = AppState()
        project_id = "test-project"

        app_state.context_manager.get_working_set = MagicMock(  # type: ignore[method-assign]
            side_effect=ValueError("Invalid project_id")
        )

        # Act
        result = await handle_get_working_set(
            app_state=app_state,
            project_id=project_id,
        )

        # Assert
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"


@pytest.mark.unit
class TestRegisterMonitoringTools:
    """Test monitoring tools registration."""

    def test_register_monitoring_tools(self) -> None:
        """Test that monitoring tools are registered correctly."""
        # Arrange
        registry = ToolRegistry()
        app_state = AppState()

        # Act
        register_monitoring_tools(registry, app_state)

        # Assert
        assert registry.get_tool("context_analyze_usage") is not None
        assert registry.get_tool("context_get_working_set") is not None

        # Verify descriptions
        analyze_tool = registry.get_tool("context_analyze_usage")
        assert analyze_tool is not None
        assert "Analyze current context usage" in analyze_tool.description

        working_set_tool = registry.get_tool("context_get_working_set")
        assert working_set_tool is not None
        assert "Get current working set segments" in working_set_tool.description

    @pytest.mark.asyncio
    async def test_registered_tools_can_be_dispatched(self) -> None:
        """Test that registered tools can be dispatched."""
        # Arrange
        registry = ToolRegistry()
        app_state = AppState()
        project_id = "test-project"

        # Mock context manager
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

        # Register tools
        register_monitoring_tools(registry, app_state)

        # Act - dispatch get_working_set
        result = await registry.dispatch(
            "context_get_working_set",
            {"project_id": project_id},
            app_state,
        )

        # Assert
        assert "error" not in result
        assert "working_set" in result
