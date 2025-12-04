"""Unit tests for data models."""

from datetime import datetime

import pytest

from hjeon139_mcp_outofcontext.models import (
    AnalysisResult,
    ContextDescriptors,
    ContextSegment,
    FileInfo,
    Message,
    PruningRecommendation,
    StashResult,
    TokenUsage,
    WorkingSet,
)


@pytest.mark.unit
class TestTokenUsage:
    """Test TokenUsage model."""

    def test_valid_token_usage(self) -> None:
        """Test valid TokenUsage creation."""
        usage = TokenUsage(current=1000, limit=4000, usage_percent=25.0)
        assert usage.current == 1000
        assert usage.limit == 4000
        assert usage.usage_percent == 25.0

    def test_token_usage_serialization(self) -> None:
        """Test TokenUsage serialization."""
        usage = TokenUsage(current=1000, limit=4000, usage_percent=25.0)
        data = usage.model_dump()
        assert data["current"] == 1000
        assert data["limit"] == 4000

        # Test deserialization
        restored = TokenUsage.model_validate(data)
        assert restored.current == usage.current


@pytest.mark.unit
class TestFileInfo:
    """Test FileInfo model."""

    def test_valid_file_info(self) -> None:
        """Test valid FileInfo creation."""
        file_info = FileInfo(
            path="/path/to/file.py", name="file.py", extension=".py", line_count=100
        )
        assert file_info.path == "/path/to/file.py"
        assert file_info.name == "file.py"
        assert file_info.extension == ".py"
        assert file_info.line_count == 100

    def test_minimal_file_info(self) -> None:
        """Test FileInfo with minimal fields."""
        file_info = FileInfo(path="/path/to/file.py")
        assert file_info.path == "/path/to/file.py"
        assert file_info.name is None


@pytest.mark.unit
class TestMessage:
    """Test Message model."""

    def test_valid_message(self) -> None:
        """Test valid Message creation."""
        msg = Message(role="user", content="Hello, world!")
        assert msg.role == "user"
        assert msg.content == "Hello, world!"
        assert msg.timestamp is None

    def test_message_with_timestamp(self) -> None:
        """Test Message with timestamp."""
        now = datetime.now()
        msg = Message(role="assistant", content="Hi!", timestamp=now)
        assert msg.timestamp == now


@pytest.mark.unit
class TestContextSegment:
    """Test ContextSegment model."""

    def test_valid_context_segment(self) -> None:
        """Test valid ContextSegment creation."""
        now = datetime.now()
        segment = ContextSegment(
            segment_id="seg-1",
            text="Some text",
            type="message",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )
        assert segment.segment_id == "seg-1"
        assert segment.text == "Some text"
        assert segment.type == "message"
        assert segment.project_id == "proj-1"
        assert segment.tokens == 100
        assert segment.pinned is False
        assert segment.generation == "young"
        assert segment.tier == "working"

    def test_context_segment_defaults(self) -> None:
        """Test ContextSegment default values."""
        now = datetime.now()
        segment = ContextSegment(
            segment_id="seg-1",
            text="Some text",
            type="code",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )
        assert segment.pinned is False
        assert segment.generation == "young"
        assert segment.gc_survival_count == 0
        assert segment.refcount == 0
        assert segment.tags == []
        assert segment.tier == "working"

    def test_context_segment_serialization(self) -> None:
        """Test ContextSegment serialization."""
        now = datetime.now()
        segment = ContextSegment(
            segment_id="seg-1",
            text="Some text",
            type="message",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )
        data = segment.model_dump()
        assert data["segment_id"] == "seg-1"
        assert data["type"] == "message"

        # Test deserialization
        restored = ContextSegment.model_validate(data)
        assert restored.segment_id == segment.segment_id


@pytest.mark.unit
class TestContextDescriptors:
    """Test ContextDescriptors model."""

    def test_valid_context_descriptors(self) -> None:
        """Test valid ContextDescriptors creation."""
        token_usage = TokenUsage(current=1000, limit=4000, usage_percent=25.0)
        descriptors = ContextDescriptors(token_usage=token_usage)
        assert descriptors.token_usage == token_usage
        assert descriptors.recent_messages == []
        assert descriptors.segment_summaries == []
        assert descriptors.current_file is None
        assert descriptors.task_info is None

    def test_context_descriptors_with_data(self) -> None:
        """Test ContextDescriptors with full data."""
        token_usage = TokenUsage(current=1000, limit=4000, usage_percent=25.0)
        messages = [Message(role="user", content="Hello")]
        file_info = FileInfo(path="/path/to/file.py")
        descriptors = ContextDescriptors(
            token_usage=token_usage,
            recent_messages=messages,
            current_file=file_info,
        )
        assert len(descriptors.recent_messages) == 1
        assert descriptors.current_file is not None


@pytest.mark.unit
class TestPruningRecommendation:
    """Test PruningRecommendation model."""

    def test_valid_pruning_recommendation(self) -> None:
        """Test valid PruningRecommendation creation."""
        rec = PruningRecommendation(
            segment_ids=["seg-1", "seg-2"],
            action="stash",
            reason="Low refcount",
            tokens_freed=500,
        )
        assert len(rec.segment_ids) == 2
        assert rec.action == "stash"
        assert rec.reason == "Low refcount"
        assert rec.tokens_freed == 500


@pytest.mark.unit
class TestWorkingSet:
    """Test WorkingSet model."""

    def test_valid_working_set(self) -> None:
        """Test valid WorkingSet creation."""
        now = datetime.now()
        segments = [
            ContextSegment(
                segment_id="seg-1",
                text="Text 1",
                type="message",
                project_id="proj-1",
                created_at=now,
                last_touched_at=now,
                tokens=100,
            )
        ]
        working_set = WorkingSet(segments=segments, total_tokens=100, project_id="proj-1")
        assert len(working_set.segments) == 1
        assert working_set.total_tokens == 100
        assert working_set.project_id == "proj-1"


@pytest.mark.unit
class TestStashResult:
    """Test StashResult model."""

    def test_valid_stash_result(self) -> None:
        """Test valid StashResult creation."""
        result = StashResult(stashed_segments=["seg-1", "seg-2"], tokens_freed=200)
        assert len(result.stashed_segments) == 2
        assert result.tokens_freed == 200
        assert result.stash_location is None


@pytest.mark.unit
class TestAnalysisResult:
    """Test AnalysisResult model."""

    def test_valid_analysis_result(self) -> None:
        """Test valid AnalysisResult creation."""
        result = AnalysisResult(total_tokens=1000, segment_count=10, usage_percent=75.0)
        assert result.total_tokens == 1000
        assert result.segment_count == 10
        assert result.usage_percent == 75.0
        assert result.recommendations == []
