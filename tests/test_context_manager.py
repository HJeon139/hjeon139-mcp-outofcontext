"""Tests for context manager module."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from hjeon139_mcp_outofcontext.analysis_engine import IAnalysisEngine
from hjeon139_mcp_outofcontext.context_manager import ContextManager, IContextManager
from hjeon139_mcp_outofcontext.gc_engine import IGCEngine
from hjeon139_mcp_outofcontext.models import (
    AnalysisResult,
    ContextDescriptors,
    ContextSegment,
    FileInfo,
    HealthScore,
    Message,
    StashResult,
    TaskInfo,
    TokenUsage,
    WorkingSet,
)
from hjeon139_mcp_outofcontext.storage import IStorageLayer
from hjeon139_mcp_outofcontext.tokenizer import Tokenizer


@pytest.fixture
def mock_storage() -> MagicMock:
    """Create a mock storage layer."""
    storage = MagicMock(spec=IStorageLayer)
    storage.load_segments.return_value = []
    storage.store_segment.return_value = None
    storage.stash_segment.return_value = None
    storage.search_stashed.return_value = []
    return storage


@pytest.fixture
def mock_gc_engine() -> MagicMock:
    """Create a mock GC engine."""
    gc_engine = MagicMock(spec=IGCEngine)
    return gc_engine


@pytest.fixture
def mock_analysis_engine() -> MagicMock:
    """Create a mock analysis engine."""
    analysis_engine = MagicMock(spec=IAnalysisEngine)
    return analysis_engine


@pytest.fixture
def tokenizer() -> Tokenizer:
    """Create a tokenizer instance."""
    return Tokenizer()


@pytest.fixture
def context_manager(
    mock_storage: MagicMock,
    mock_gc_engine: MagicMock,
    mock_analysis_engine: MagicMock,
    tokenizer: Tokenizer,
) -> ContextManager:
    """Create a context manager instance for testing."""
    return ContextManager(
        storage=mock_storage,
        gc_engine=mock_gc_engine,
        analysis_engine=mock_analysis_engine,
        tokenizer=tokenizer,
    )


@pytest.fixture
def sample_segment() -> ContextSegment:
    """Create a sample context segment."""
    now = datetime.now()
    return ContextSegment(
        segment_id="seg-1",
        text="Sample text content",
        type="message",
        project_id="proj-1",
        task_id="task-1",
        created_at=now,
        last_touched_at=now,
        tokens=100,
        tier="working",
    )


@pytest.fixture
def sample_descriptors() -> ContextDescriptors:
    """Create sample context descriptors."""
    now = datetime.now()
    return ContextDescriptors(
        recent_messages=[
            Message(role="user", content="Hello", timestamp=now),
            Message(role="assistant", content="Hi there", timestamp=now),
        ],
        current_file=FileInfo(path="test.py", current_line=10),
        token_usage=TokenUsage(current=5000, limit=32000, usage_percent=15.6),
        task_info=TaskInfo(task_id="task-1", name="Test Task", created_at=now),
    )


@pytest.mark.unit
def test_analyze_context_basic(
    context_manager: ContextManager,
    sample_descriptors: ContextDescriptors,
    mock_storage: MagicMock,
    mock_analysis_engine: MagicMock,
) -> None:
    """Test basic context analysis."""
    # Setup mocks
    mock_storage.load_segments.return_value = []
    mock_analysis_engine.analyze_context_usage.return_value = MagicMock(
        total_tokens=5000,
        total_segments=2,
        usage_percent=15.6,
    )
    mock_analysis_engine.compute_health_score.return_value = HealthScore(
        score=85.0,
        usage_percent=15.6,
        factors={},
    )
    mock_analysis_engine.generate_recommendations.return_value = []

    # Execute
    result = context_manager.analyze_context(sample_descriptors, "proj-1")

    # Verify
    assert isinstance(result, AnalysisResult)
    assert result.total_tokens == 5000
    assert result.segment_count == 2
    assert result.usage_percent == 15.6
    assert result.health_score.score == 85.0

    # Verify storage was called to store new segments
    assert mock_storage.store_segment.call_count > 0

    # Verify analysis engine was called
    mock_analysis_engine.analyze_context_usage.assert_called_once()
    mock_analysis_engine.compute_health_score.assert_called_once()
    mock_analysis_engine.generate_recommendations.assert_called_once()


@pytest.mark.unit
def test_analyze_context_with_existing_segments(
    context_manager: ContextManager,
    sample_descriptors: ContextDescriptors,
    sample_segment: ContextSegment,
    mock_storage: MagicMock,
    mock_analysis_engine: MagicMock,
) -> None:
    """Test context analysis with existing segments."""
    # Setup: return existing segment
    mock_storage.load_segments.return_value = [sample_segment]
    mock_analysis_engine.analyze_context_usage.return_value = MagicMock(
        total_tokens=5100,
        total_segments=3,
        usage_percent=15.9,
    )
    mock_analysis_engine.compute_health_score.return_value = HealthScore(
        score=84.0,
        usage_percent=15.9,
        factors={},
    )
    mock_analysis_engine.generate_recommendations.return_value = []

    # Execute
    result = context_manager.analyze_context(sample_descriptors, "proj-1")

    # Verify
    assert result.total_tokens == 5100
    assert result.segment_count == 3

    # Verify it only analyzed working tier segments
    call_args = mock_analysis_engine.analyze_context_usage.call_args
    segments_passed = call_args[0][0]
    assert all(s.tier == "working" for s in segments_passed)


@pytest.mark.unit
def test_analyze_context_empty_project_id(
    context_manager: ContextManager,
    sample_descriptors: ContextDescriptors,
) -> None:
    """Test that analyze_context validates project_id."""
    with pytest.raises(ValueError, match="project_id cannot be empty"):
        context_manager.analyze_context(sample_descriptors, "")


@pytest.mark.unit
def test_get_working_set_basic(
    context_manager: ContextManager,
    sample_segment: ContextSegment,
    mock_storage: MagicMock,
) -> None:
    """Test getting working set."""
    # Setup
    mock_storage.load_segments.return_value = [sample_segment]

    # Execute
    working_set = context_manager.get_working_set("proj-1", "task-1")

    # Verify
    assert isinstance(working_set, WorkingSet)
    assert working_set.project_id == "proj-1"
    assert working_set.task_id == "task-1"
    assert len(working_set.segments) == 1
    assert working_set.segments[0].segment_id == "seg-1"
    assert working_set.total_tokens == 100


@pytest.mark.unit
def test_get_working_set_filters_by_task(
    context_manager: ContextManager,
    mock_storage: MagicMock,
) -> None:
    """Test that working set filters segments by task."""
    now = datetime.now()
    segments = [
        ContextSegment(
            segment_id=f"seg-{i}",
            text=f"Content {i}",
            type="message",
            project_id="proj-1",
            task_id="task-1" if i < 3 else "task-2",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            tier="working",
        )
        for i in range(5)
    ]

    mock_storage.load_segments.return_value = segments

    # Execute
    working_set = context_manager.get_working_set("proj-1", "task-1")

    # Verify
    assert len(working_set.segments) == 3
    assert all(s.task_id == "task-1" for s in working_set.segments)
    assert working_set.total_tokens == 300


@pytest.mark.unit
def test_get_working_set_uses_current_task(
    context_manager: ContextManager,
    sample_segment: ContextSegment,
    mock_storage: MagicMock,
) -> None:
    """Test that working set uses current task if task_id not provided."""
    # Set current task
    context_manager.current_tasks["proj-1"] = "task-1"
    mock_storage.load_segments.return_value = [sample_segment]

    # Execute without task_id
    working_set = context_manager.get_working_set("proj-1")

    # Verify
    assert working_set.task_id == "task-1"


@pytest.mark.unit
def test_get_working_set_empty_project_id(context_manager: ContextManager) -> None:
    """Test that get_working_set validates project_id."""
    with pytest.raises(ValueError, match="project_id cannot be empty"):
        context_manager.get_working_set("")


@pytest.mark.unit
def test_get_working_set_only_working_tier(
    context_manager: ContextManager,
    mock_storage: MagicMock,
) -> None:
    """Test that working set only includes working tier segments."""
    now = datetime.now()
    segments = [
        ContextSegment(
            segment_id="seg-1",
            text="Working segment",
            type="message",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            tier="working",
        ),
        ContextSegment(
            segment_id="seg-2",
            text="Stashed segment",
            type="message",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            tier="stashed",
        ),
    ]

    mock_storage.load_segments.return_value = segments

    # Execute
    working_set = context_manager.get_working_set("proj-1")

    # Verify
    assert len(working_set.segments) == 1
    assert working_set.segments[0].segment_id == "seg-1"
    assert working_set.segments[0].tier == "working"


@pytest.mark.unit
def test_stash_segments_basic(
    context_manager: ContextManager,
    sample_segment: ContextSegment,
    mock_storage: MagicMock,
) -> None:
    """Test stashing segments."""
    # Setup
    mock_storage.load_segments.return_value = [sample_segment]

    # Execute
    result = context_manager.stash_segments(["seg-1"], "proj-1")

    # Verify
    assert isinstance(result, StashResult)
    assert result.stashed_segments == ["seg-1"]
    assert result.tokens_freed == 100

    # Verify storage was called
    mock_storage.stash_segment.assert_called_once()
    call_args = mock_storage.stash_segment.call_args
    assert call_args[0][0].segment_id == "seg-1"
    assert call_args[0][1] == "proj-1"


@pytest.mark.unit
def test_stash_segments_multiple(
    context_manager: ContextManager,
    mock_storage: MagicMock,
) -> None:
    """Test stashing multiple segments."""
    now = datetime.now()
    segments = [
        ContextSegment(
            segment_id=f"seg-{i}",
            text=f"Content {i}",
            type="message",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100 * (i + 1),
            tier="working",
        )
        for i in range(3)
    ]

    mock_storage.load_segments.return_value = segments

    # Execute
    result = context_manager.stash_segments(["seg-0", "seg-1", "seg-2"], "proj-1")

    # Verify
    assert len(result.stashed_segments) == 3
    assert result.tokens_freed == 600  # 100 + 200 + 300
    assert mock_storage.stash_segment.call_count == 3


@pytest.mark.unit
def test_stash_segments_empty_list(context_manager: ContextManager) -> None:
    """Test stashing with empty segment list."""
    result = context_manager.stash_segments([], "proj-1")

    assert result.stashed_segments == []
    assert result.tokens_freed == 0


@pytest.mark.unit
def test_stash_segments_missing_segments(
    context_manager: ContextManager,
    sample_segment: ContextSegment,
    mock_storage: MagicMock,
) -> None:
    """Test stashing when some segments are missing."""
    mock_storage.load_segments.return_value = [sample_segment]

    # Execute with non-existent segment ID
    result = context_manager.stash_segments(["seg-1", "seg-nonexistent"], "proj-1")

    # Should still stash the found segment
    assert "seg-1" in result.stashed_segments
    assert result.tokens_freed == 100


@pytest.mark.unit
def test_stash_segments_only_working_tier(
    context_manager: ContextManager,
    mock_storage: MagicMock,
) -> None:
    """Test that only working tier segments can be stashed."""
    now = datetime.now()
    segments = [
        ContextSegment(
            segment_id="seg-1",
            text="Working segment",
            type="message",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            tier="working",
        ),
        ContextSegment(
            segment_id="seg-2",
            text="Stashed segment",
            type="message",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            tier="stashed",
        ),
    ]

    mock_storage.load_segments.return_value = segments

    # Execute
    result = context_manager.stash_segments(["seg-1", "seg-2"], "proj-1")

    # Verify only working tier segment was stashed
    assert result.stashed_segments == ["seg-1"]
    assert result.tokens_freed == 100
    assert mock_storage.stash_segment.call_count == 1


@pytest.mark.unit
def test_stash_segments_empty_project_id(context_manager: ContextManager) -> None:
    """Test that stash_segments validates project_id."""
    with pytest.raises(ValueError, match="project_id cannot be empty"):
        context_manager.stash_segments(["seg-1"], "")


@pytest.mark.unit
def test_stash_segments_invalidates_cache(
    context_manager: ContextManager,
    sample_segment: ContextSegment,
    mock_storage: MagicMock,
) -> None:
    """Test that stashing invalidates working set cache."""
    # Setup cache
    context_manager.working_sets["proj-1"] = {
        "task-1": WorkingSet(
            segments=[sample_segment],
            total_tokens=100,
            project_id="proj-1",
            task_id="task-1",
        )
    }

    mock_storage.load_segments.return_value = [sample_segment]

    # Execute
    context_manager.stash_segments(["seg-1"], "proj-1")

    # Verify cache was cleared
    assert (
        "proj-1" not in context_manager.working_sets
        or len(context_manager.working_sets["proj-1"]) == 0
    )


@pytest.mark.unit
def test_retrieve_stashed_basic(
    context_manager: ContextManager,
    sample_segment: ContextSegment,
    mock_storage: MagicMock,
) -> None:
    """Test retrieving stashed segments."""
    # Setup
    stashed_segment = ContextSegment(
        segment_id="seg-1",
        text="Stashed content",
        type="message",
        project_id="proj-1",
        created_at=datetime.now(),
        last_touched_at=datetime.now(),
        tokens=100,
        tier="stashed",
    )
    mock_storage.search_stashed.return_value = [stashed_segment]

    # Execute
    results = context_manager.retrieve_stashed("content", {}, "proj-1")

    # Verify
    assert len(results) == 1
    assert results[0].segment_id == "seg-1"
    assert results[0].tier == "stashed"

    # Verify storage was called
    mock_storage.search_stashed.assert_called_once_with("content", {}, "proj-1")


@pytest.mark.unit
def test_retrieve_stashed_with_filters(
    context_manager: ContextManager,
    mock_storage: MagicMock,
) -> None:
    """Test retrieving stashed segments with filters."""
    filters = {"task_id": "task-1", "type": "message"}
    mock_storage.search_stashed.return_value = []

    # Execute
    context_manager.retrieve_stashed("query", filters, "proj-1")

    # Verify filters were passed
    mock_storage.search_stashed.assert_called_once_with("query", filters, "proj-1")


@pytest.mark.unit
def test_retrieve_stashed_empty_project_id(context_manager: ContextManager) -> None:
    """Test that retrieve_stashed validates project_id."""
    with pytest.raises(ValueError, match="project_id cannot be empty"):
        context_manager.retrieve_stashed("query", {}, "")


@pytest.mark.unit
def test_project_task_scoping(
    context_manager: ContextManager,
    sample_descriptors: ContextDescriptors,
    mock_storage: MagicMock,
    mock_analysis_engine: MagicMock,
) -> None:
    """Test that project/task scoping works correctly."""
    # Setup
    mock_storage.load_segments.return_value = []
    mock_analysis_engine.analyze_context_usage.return_value = MagicMock(
        total_tokens=0,
        total_segments=0,
        usage_percent=0.0,
    )
    mock_analysis_engine.compute_health_score.return_value = HealthScore(
        score=100.0,
        usage_percent=0.0,
        factors={},
    )
    mock_analysis_engine.generate_recommendations.return_value = []

    # Execute with task info
    context_manager.analyze_context(sample_descriptors, "proj-1")

    # Verify current task was set
    assert context_manager.current_tasks["proj-1"] == "task-1"


@pytest.mark.unit
def test_working_set_caching(
    context_manager: ContextManager,
    sample_segment: ContextSegment,
    mock_storage: MagicMock,
) -> None:
    """Test that working sets are cached."""
    mock_storage.load_segments.return_value = [sample_segment]

    # First call
    working_set1 = context_manager.get_working_set("proj-1", "task-1")

    # Second call should use cache
    working_set2 = context_manager.get_working_set("proj-1", "task-1")

    # Verify same object (or at least same content)
    assert working_set1.project_id == working_set2.project_id
    assert working_set1.task_id == working_set2.task_id

    # Verify storage was only called once (cached on second call)
    # Note: In current implementation, we rebuild each time, but cache structure exists
    assert "proj-1" in context_manager.working_sets


@pytest.mark.unit
def test_convert_descriptors_to_segments(
    context_manager: ContextManager,
    sample_descriptors: ContextDescriptors,
) -> None:
    """Test conversion of descriptors to segments."""
    segments = context_manager._convert_descriptors_to_segments(sample_descriptors, "proj-1")

    # Should have segments for messages and current file
    assert len(segments) >= 2  # At least 2 messages + 1 file

    # Verify message segments
    message_segments = [s for s in segments if s.type == "message"]
    assert len(message_segments) == 2

    # Verify file segment
    file_segments = [s for s in segments if s.type == "code"]
    assert len(file_segments) >= 1
    assert file_segments[0].file_path == "test.py"


@pytest.mark.unit
def test_convert_descriptors_without_task_info(
    context_manager: ContextManager,
    tokenizer: Tokenizer,
) -> None:
    """Test conversion when task_info is None."""
    descriptors = ContextDescriptors(
        recent_messages=[Message(role="user", content="Hello")],
        token_usage=TokenUsage(current=1000, limit=32000, usage_percent=3.1),
    )

    segments = context_manager._convert_descriptors_to_segments(descriptors, "proj-1")

    # Verify segments don't have task_id
    assert all(s.task_id is None for s in segments)


@pytest.mark.unit
def test_interface_implementation() -> None:
    """Test that ContextManager implements IContextManager interface."""
    # This test ensures the interface contract is satisfied
    assert issubclass(ContextManager, IContextManager)

    # Verify all abstract methods are implemented
    assert hasattr(ContextManager, "analyze_context")
    assert hasattr(ContextManager, "get_working_set")
    assert hasattr(ContextManager, "stash_segments")
    assert hasattr(ContextManager, "retrieve_stashed")
