"""Tests for analysis engine module."""

from datetime import datetime, timedelta

import pytest

from hjeon139_mcp_outofcontext.analysis_engine import AnalysisEngine, IAnalysisEngine
from hjeon139_mcp_outofcontext.models import ContextSegment, UsageMetrics
from hjeon139_mcp_outofcontext.tokenizer import Tokenizer


@pytest.mark.unit
def test_analyze_context_usage_empty() -> None:
    """Test usage analysis with empty context."""
    engine = AnalysisEngine()
    metrics = engine.analyze_context_usage([])

    assert metrics.total_tokens == 0
    assert metrics.total_segments == 0
    assert metrics.usage_percent == 0.0
    assert metrics.estimated_remaining_tokens == 32000
    assert metrics.pinned_segments_count == 0
    assert metrics.pinned_tokens == 0


@pytest.mark.unit
def test_analyze_context_usage_single_segment() -> None:
    """Test usage analysis with single segment."""
    engine = AnalysisEngine()
    now = datetime.now()
    segment = ContextSegment(
        segment_id="seg-1",
        text="Test content",
        type="message",
        project_id="test-project",
        created_at=now,
        last_touched_at=now,
        tokens=100,
    )

    metrics = engine.analyze_context_usage([segment])

    assert metrics.total_tokens == 100
    assert metrics.total_segments == 1
    assert metrics.segments_by_type["message"] == 1
    assert metrics.tokens_by_type["message"] == 100
    assert metrics.usage_percent == (100 / 32000) * 100


@pytest.mark.unit
def test_analyze_context_usage_multiple_segments() -> None:
    """Test usage analysis with multiple segments."""
    engine = AnalysisEngine()
    now = datetime.now()
    segments = [
        ContextSegment(
            segment_id=f"seg-{i}",
            text=f"Content {i}",
            type="message" if i % 2 == 0 else "code",
            project_id="test-project",
            created_at=now,
            last_touched_at=now,
            tokens=50 * (i + 1),
        )
        for i in range(5)
    ]

    metrics = engine.analyze_context_usage(segments)

    assert metrics.total_segments == 5
    assert metrics.segments_by_type["message"] == 3  # 0, 2, 4
    assert metrics.segments_by_type["code"] == 2  # 1, 3
    assert metrics.total_tokens == sum(50 * (i + 1) for i in range(5))


@pytest.mark.unit
def test_analyze_context_usage_with_tasks() -> None:
    """Test usage analysis with task grouping."""
    engine = AnalysisEngine()
    now = datetime.now()
    segments = [
        ContextSegment(
            segment_id=f"seg-{i}",
            text=f"Content {i}",
            type="message",
            project_id="test-project",
            task_id="task-1" if i < 3 else "task-2",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )
        for i in range(5)
    ]

    metrics = engine.analyze_context_usage(segments)

    assert metrics.tokens_by_task["task-1"] == 300
    assert metrics.tokens_by_task["task-2"] == 200


@pytest.mark.unit
def test_analyze_context_usage_pinned_segments() -> None:
    """Test usage analysis with pinned segments."""
    engine = AnalysisEngine()
    now = datetime.now()
    segments = [
        ContextSegment(
            segment_id=f"seg-{i}",
            text=f"Content {i}",
            type="message",
            project_id="test-project",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            pinned=(i < 2),  # First 2 are pinned
        )
        for i in range(5)
    ]

    metrics = engine.analyze_context_usage(segments)

    assert metrics.pinned_segments_count == 2
    assert metrics.pinned_tokens == 200


@pytest.mark.unit
def test_analyze_context_usage_age_calculation() -> None:
    """Test age calculation in usage metrics."""
    engine = AnalysisEngine()
    now = datetime.now()
    old_time = now - timedelta(hours=48)
    new_time = now - timedelta(hours=1)

    segments = [
        ContextSegment(
            segment_id="old",
            text="Old content",
            type="message",
            project_id="test-project",
            created_at=old_time,
            last_touched_at=old_time,
            tokens=100,
        ),
        ContextSegment(
            segment_id="new",
            text="New content",
            type="message",
            project_id="test-project",
            created_at=new_time,
            last_touched_at=new_time,
            tokens=100,
        ),
    ]

    metrics = engine.analyze_context_usage(segments)

    assert metrics.oldest_segment_age_hours > 40  # Should be around 48
    assert metrics.newest_segment_age_hours < 2  # Should be around 1


@pytest.mark.unit
def test_compute_health_score_empty() -> None:
    """Test health score with empty context."""
    engine = AnalysisEngine()
    score = engine.compute_health_score([])

    assert score.score == 100.0
    assert score.usage_percent == 0.0
    assert "usage" in score.factors


@pytest.mark.unit
def test_compute_health_score_low_usage() -> None:
    """Test health score with low usage."""
    engine = AnalysisEngine()
    now = datetime.now()
    segments = [
        ContextSegment(
            segment_id="seg-1",
            text="Content",
            type="message",
            project_id="test-project",
            created_at=now,
            last_touched_at=now,
            tokens=1000,  # Low usage
        )
    ]

    score = engine.compute_health_score(segments, token_limit=32000)

    assert score.score > 90.0  # Should be high for low usage
    assert score.usage_percent < 10.0


@pytest.mark.unit
def test_compute_health_score_high_usage() -> None:
    """Test health score with high usage."""
    engine = AnalysisEngine()
    now = datetime.now()
    segments = [
        ContextSegment(
            segment_id="seg-1",
            text="Content",
            type="message",
            project_id="test-project",
            created_at=now,
            last_touched_at=now,
            tokens=30000,  # High usage
        )
    ]

    score = engine.compute_health_score(segments, token_limit=32000)

    assert score.score < 50.0  # Should be low for high usage
    assert score.usage_percent > 90.0


@pytest.mark.unit
def test_compute_health_score_old_segments() -> None:
    """Test health score penalty for old segments."""
    engine = AnalysisEngine()
    now = datetime.now()
    old_time = now - timedelta(days=5)  # 5 days old

    segments = [
        ContextSegment(
            segment_id="seg-1",
            text="Content",
            type="message",
            project_id="test-project",
            created_at=old_time,
            last_touched_at=old_time,
            tokens=1000,
        )
    ]

    score = engine.compute_health_score(segments)

    # Should have age penalty
    assert "age_penalty" in score.factors
    assert score.factors["age_penalty"] < 0


@pytest.mark.unit
def test_compute_health_score_distribution() -> None:
    """Test health score includes distribution factor."""
    engine = AnalysisEngine()
    now = datetime.now()

    # Mix of types for good distribution
    segments = [
        ContextSegment(
            segment_id=f"seg-{i}",
            text="Content",
            type=["message", "code", "log"][i % 3],
            project_id="test-project",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )
        for i in range(6)
    ]

    score = engine.compute_health_score(segments)

    assert "distribution" in score.factors
    assert 0.0 <= score.factors["distribution"] <= 10.0


@pytest.mark.unit
def test_generate_recommendations_high_usage() -> None:
    """Test recommendations for high usage."""
    engine = AnalysisEngine()
    metrics = UsageMetrics(
        total_tokens=30000,
        total_segments=10,
        tokens_by_type={},
        segments_by_type={},
        tokens_by_task={},
        oldest_segment_age_hours=1.0,
        newest_segment_age_hours=0.5,
        pinned_segments_count=0,
        pinned_tokens=0,
        usage_percent=93.75,  # > 90%
        estimated_remaining_tokens=2000,
    )

    recommendations = engine.generate_recommendations(metrics)

    assert len(recommendations) > 0
    urgent_recs = [r for r in recommendations if r.priority == "urgent"]
    assert len(urgent_recs) > 0


@pytest.mark.unit
def test_generate_recommendations_medium_usage() -> None:
    """Test recommendations for medium usage."""
    engine = AnalysisEngine()
    metrics = UsageMetrics(
        total_tokens=26000,
        total_segments=10,
        tokens_by_type={},
        segments_by_type={},
        tokens_by_task={},
        oldest_segment_age_hours=1.0,
        newest_segment_age_hours=0.5,
        pinned_segments_count=0,
        pinned_tokens=0,
        usage_percent=81.25,  # > 80%
        estimated_remaining_tokens=6000,
    )

    recommendations = engine.generate_recommendations(metrics)

    assert len(recommendations) > 0
    high_recs = [r for r in recommendations if r.priority == "high"]
    assert len(high_recs) > 0


@pytest.mark.unit
def test_generate_recommendations_low_usage() -> None:
    """Test recommendations for low usage."""
    engine = AnalysisEngine()
    metrics = UsageMetrics(
        total_tokens=10000,
        total_segments=10,
        tokens_by_type={},
        segments_by_type={},
        tokens_by_task={},
        oldest_segment_age_hours=1.0,
        newest_segment_age_hours=0.5,
        pinned_segments_count=0,
        pinned_tokens=0,
        usage_percent=31.25,  # < 50%
        estimated_remaining_tokens=22000,
    )

    recommendations = engine.generate_recommendations(metrics)

    assert len(recommendations) > 0
    low_recs = [r for r in recommendations if r.priority == "low"]
    assert len(low_recs) > 0


@pytest.mark.unit
def test_generate_recommendations_old_segments() -> None:
    """Test recommendations for old segments."""
    engine = AnalysisEngine()
    metrics = UsageMetrics(
        total_tokens=10000,
        total_segments=10,
        tokens_by_type={},
        segments_by_type={},
        tokens_by_task={},
        oldest_segment_age_hours=30.0,  # > 24 hours
        newest_segment_age_hours=1.0,
        pinned_segments_count=0,
        pinned_tokens=0,
        usage_percent=31.25,
        estimated_remaining_tokens=22000,
    )

    recommendations = engine.generate_recommendations(metrics)

    stash_recs = [r for r in recommendations if r.action == "stash"]
    assert len(stash_recs) > 0


@pytest.mark.unit
def test_generate_recommendations_unbalanced_distribution() -> None:
    """Test recommendations for unbalanced distribution."""
    engine = AnalysisEngine()
    metrics = UsageMetrics(
        total_tokens=10000,
        total_segments=10,
        tokens_by_type={},
        segments_by_type={"log": 7, "message": 2, "code": 1},  # Logs dominate
        tokens_by_task={},
        oldest_segment_age_hours=1.0,
        newest_segment_age_hours=0.5,
        pinned_segments_count=0,
        pinned_tokens=0,
        usage_percent=31.25,
        estimated_remaining_tokens=22000,
    )

    recommendations = engine.generate_recommendations(metrics)

    # Should recommend stashing logs
    log_recs = [r for r in recommendations if "log" in r.message.lower() and r.action == "stash"]
    assert len(log_recs) > 0


@pytest.mark.unit
def test_generate_recommendations_all_pinned() -> None:
    """Test recommendations when all segments are pinned."""
    engine = AnalysisEngine()
    metrics = UsageMetrics(
        total_tokens=10000,
        total_segments=5,
        tokens_by_type={},
        segments_by_type={},
        tokens_by_task={},
        oldest_segment_age_hours=1.0,
        newest_segment_age_hours=0.5,
        pinned_segments_count=5,  # All pinned
        pinned_tokens=10000,
        usage_percent=31.25,
        estimated_remaining_tokens=22000,
    )

    recommendations = engine.generate_recommendations(metrics)

    unpin_recs = [r for r in recommendations if r.action == "unpin"]
    assert len(unpin_recs) > 0


@pytest.mark.unit
def test_analysis_engine_interface() -> None:
    """Test that AnalysisEngine implements IAnalysisEngine interface."""
    engine = AnalysisEngine()
    assert isinstance(engine, IAnalysisEngine)


@pytest.mark.unit
def test_analysis_engine_custom_tokenizer() -> None:
    """Test AnalysisEngine with custom tokenizer."""
    tokenizer = Tokenizer()
    engine = AnalysisEngine(tokenizer=tokenizer)

    now = datetime.now()
    segment = ContextSegment(
        segment_id="seg-1",
        text="Test",
        type="message",
        project_id="test-project",
        created_at=now,
        last_touched_at=now,
        tokens=100,
    )

    metrics = engine.analyze_context_usage([segment])
    assert metrics.total_tokens == 100


@pytest.mark.unit
def test_compute_distribution_score_single_type() -> None:
    """Test distribution score for single segment type."""
    engine = AnalysisEngine()
    now = datetime.now()
    segments = [
        ContextSegment(
            segment_id=f"seg-{i}",
            text="Content",
            type="message",  # All same type
            project_id="test-project",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )
        for i in range(5)
    ]

    score = engine.compute_health_score(segments)
    # Single type should have lower distribution score
    assert "distribution" in score.factors


@pytest.mark.unit
def test_compute_distribution_score_mixed_types() -> None:
    """Test distribution score for mixed segment types."""
    engine = AnalysisEngine()
    now = datetime.now()
    types = ["message", "code", "log", "note"]
    segments = [
        ContextSegment(
            segment_id=f"seg-{i}",
            text="Content",
            type=types[i % len(types)],
            project_id="test-project",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )
        for i in range(8)
    ]

    score = engine.compute_health_score(segments)
    # Mixed types should have better distribution score
    assert "distribution" in score.factors
    assert score.factors["distribution"] >= 0.0
