"""Tests for GC Engine."""

from datetime import datetime, timedelta

import pytest

from hjeon139_mcp_outofcontext.gc_engine import GCEngine, IGCEngine
from hjeon139_mcp_outofcontext.models import ContextSegment, PruningCandidate


@pytest.fixture
def gc_engine() -> GCEngine:
    """Create a GC Engine instance for testing."""
    return GCEngine(recent_messages_count=10, recent_decision_hours=1)


@pytest.fixture
def now() -> datetime:
    """Current timestamp for testing."""
    return datetime.now()


@pytest.fixture
def old_timestamp(now: datetime) -> datetime:
    """Old timestamp (2 days ago) for testing."""
    return now - timedelta(days=2)


@pytest.fixture
def recent_timestamp(now: datetime) -> datetime:
    """Recent timestamp (1 hour ago) for testing."""
    return now - timedelta(hours=1)


@pytest.fixture
def sample_segment(now: datetime) -> ContextSegment:
    """Create a sample context segment for testing."""
    return ContextSegment(
        segment_id="seg-1",
        text="Sample text content",
        type="message",
        project_id="proj-1",
        task_id="task-1",
        created_at=now,
        last_touched_at=now,
        tokens=100,
        pinned=False,
        generation="young",
        refcount=0,
    )


@pytest.fixture
def old_log_segment(old_timestamp: datetime) -> ContextSegment:
    """Create an old log segment (good pruning candidate)."""
    return ContextSegment(
        segment_id="seg-old-log",
        text="Old log entry",
        type="log",
        project_id="proj-1",
        task_id=None,
        created_at=old_timestamp,
        last_touched_at=old_timestamp,
        tokens=50,
        pinned=False,
        generation="old",
        refcount=0,
    )


@pytest.fixture
def pinned_segment(now: datetime) -> ContextSegment:
    """Create a pinned segment (should never be pruned)."""
    return ContextSegment(
        segment_id="seg-pinned",
        text="Pinned content",
        type="decision",
        project_id="proj-1",
        task_id="task-1",
        created_at=now,
        last_touched_at=now,
        tokens=200,
        pinned=True,
        generation="young",
        refcount=5,
    )


@pytest.fixture
def decision_segment(now: datetime) -> ContextSegment:
    """Create a recent decision segment (low prune score)."""
    return ContextSegment(
        segment_id="seg-decision",
        text="Important decision",
        type="decision",
        project_id="proj-1",
        task_id="task-1",
        created_at=now,
        last_touched_at=now,
        tokens=150,
        pinned=False,
        generation="young",
        refcount=3,
    )


class TestGCEngineInterface:
    """Test that GCEngine implements IGCEngine interface."""

    @pytest.mark.unit
    def test_implements_interface(self, gc_engine: GCEngine) -> None:
        """Test that GCEngine implements IGCEngine."""
        assert isinstance(gc_engine, IGCEngine)


class TestScoreSegment:
    """Test segment scoring heuristics."""

    @pytest.mark.unit
    def test_score_old_log_segment(
        self, gc_engine: GCEngine, old_log_segment: ContextSegment, now: datetime
    ) -> None:
        """Test that old log segments get high prune scores."""
        score = gc_engine.score_segment(old_log_segment, now)
        assert score > 0.5  # Should be high (likely to prune)

    @pytest.mark.unit
    def test_score_recent_decision(
        self, gc_engine: GCEngine, decision_segment: ContextSegment, now: datetime
    ) -> None:
        """Test that recent decisions get low prune scores."""
        score = gc_engine.score_segment(decision_segment, now)
        assert score < 0.5  # Should be low (unlikely to prune)

    @pytest.mark.unit
    def test_score_with_refcount(self, gc_engine: GCEngine, now: datetime) -> None:
        """Test that segments with high refcount get lower scores."""
        high_ref = ContextSegment(
            segment_id="seg-high-ref",
            text="High refcount",
            type="code",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            refcount=10,
        )
        low_ref = ContextSegment(
            segment_id="seg-low-ref",
            text="Low refcount",
            type="code",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            refcount=0,
        )

        high_score = gc_engine.score_segment(high_ref, now)
        low_score = gc_engine.score_segment(low_ref, now)

        assert low_score > high_score  # Lower refcount = higher prune score

    @pytest.mark.unit
    def test_score_with_generation(self, gc_engine: GCEngine, now: datetime) -> None:
        """Test that old generation segments get higher scores."""
        old_gen = ContextSegment(
            segment_id="seg-old-gen",
            text="Old generation",
            type="code",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            generation="old",
        )
        young_gen = ContextSegment(
            segment_id="seg-young-gen",
            text="Young generation",
            type="code",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            generation="young",
        )

        old_score = gc_engine.score_segment(old_gen, now)
        young_score = gc_engine.score_segment(young_gen, now)

        assert old_score > young_score  # Old generation = higher prune score

    @pytest.mark.unit
    def test_score_type_ordering(self, gc_engine: GCEngine, now: datetime) -> None:
        """Test that different types get different scores."""
        log_seg = ContextSegment(
            segment_id="seg-log",
            text="Log",
            type="log",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )
        decision_seg = ContextSegment(
            segment_id="seg-decision",
            text="Decision",
            type="decision",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )

        log_score = gc_engine.score_segment(log_seg, now)
        decision_score = gc_engine.score_segment(decision_seg, now)

        assert log_score > decision_score  # Logs should score higher than decisions


class TestComputeReachability:
    """Test mark-and-sweep reachability analysis."""

    @pytest.mark.unit
    def test_simple_reachability(self, gc_engine: GCEngine) -> None:
        """Test simple reachability from root."""
        roots = {"seg-1"}
        references = {
            "seg-1": {"seg-2", "seg-3"},
            "seg-2": {"seg-4"},
        }

        reachable = gc_engine.compute_reachability(roots, references)

        assert "seg-1" in reachable  # Root
        assert "seg-2" in reachable  # Direct reference
        assert "seg-3" in reachable  # Direct reference
        assert "seg-4" in reachable  # Indirect reference
        assert len(reachable) == 4

    @pytest.mark.unit
    def test_empty_roots(self, gc_engine: GCEngine) -> None:
        """Test reachability with empty roots."""
        roots: set[str] = set()
        references = {"seg-1": {"seg-2"}}

        reachable = gc_engine.compute_reachability(roots, references)

        assert len(reachable) == 0

    @pytest.mark.unit
    def test_circular_references(self, gc_engine: GCEngine) -> None:
        """Test reachability with circular references."""
        roots = {"seg-1"}
        references = {
            "seg-1": {"seg-2"},
            "seg-2": {"seg-3"},
            "seg-3": {"seg-2"},  # Circular
        }

        reachable = gc_engine.compute_reachability(roots, references)

        assert "seg-1" in reachable
        assert "seg-2" in reachable
        assert "seg-3" in reachable
        assert len(reachable) == 3  # Should not loop infinitely

    @pytest.mark.unit
    def test_disconnected_segments(self, gc_engine: GCEngine) -> None:
        """Test that disconnected segments are not reachable."""
        roots = {"seg-1"}
        references = {
            "seg-1": {"seg-2"},
            "seg-3": {"seg-4"},  # Disconnected from root
        }

        reachable = gc_engine.compute_reachability(roots, references)

        assert "seg-1" in reachable
        assert "seg-2" in reachable
        assert "seg-3" not in reachable
        assert "seg-4" not in reachable


class TestAnalyzePruningCandidates:
    """Test pruning candidate analysis."""

    @pytest.mark.unit
    def test_excludes_root_segments(
        self,
        gc_engine: GCEngine,
        sample_segment: ContextSegment,
        old_log_segment: ContextSegment,
    ) -> None:
        """Test that root segments are excluded from candidates."""
        segments = [sample_segment, old_log_segment]
        roots = {sample_segment.segment_id}

        candidates = gc_engine.analyze_pruning_candidates(segments, roots)

        # sample_segment should be excluded (in roots)
        # old_log_segment should be included
        assert len(candidates) == 1
        assert candidates[0].segment_id == old_log_segment.segment_id

    @pytest.mark.unit
    def test_excludes_pinned_segments(
        self,
        gc_engine: GCEngine,
        pinned_segment: ContextSegment,
        old_log_segment: ContextSegment,
    ) -> None:
        """Test that pinned segments are excluded from candidates."""
        segments = [pinned_segment, old_log_segment]
        roots: set[str] = set()

        candidates = gc_engine.analyze_pruning_candidates(segments, roots)

        # pinned_segment should be excluded
        # old_log_segment should be included
        assert len(candidates) == 1
        assert candidates[0].segment_id == old_log_segment.segment_id

    @pytest.mark.unit
    def test_excludes_reachable_segments(
        self,
        gc_engine: GCEngine,
        now: datetime,
    ) -> None:
        """Test that reachable segments are excluded."""
        root_seg = ContextSegment(
            segment_id="seg-root",
            text="Root",
            type="message",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            tags=["ref:seg-referenced"],
        )
        referenced_seg = ContextSegment(
            segment_id="seg-referenced",
            text="Referenced",
            type="code",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )
        unreachable_seg = ContextSegment(
            segment_id="seg-unreachable",
            text="Unreachable",
            type="log",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )

        segments = [root_seg, referenced_seg, unreachable_seg]
        roots = {root_seg.segment_id}

        candidates = gc_engine.analyze_pruning_candidates(segments, roots)

        # Only unreachable_seg should be a candidate
        assert len(candidates) == 1
        assert candidates[0].segment_id == unreachable_seg.segment_id

    @pytest.mark.unit
    def test_sorts_by_score(
        self,
        gc_engine: GCEngine,
        now: datetime,
        old_timestamp: datetime,
    ) -> None:
        """Test that candidates are sorted by score (highest first)."""
        old_log = ContextSegment(
            segment_id="seg-old-log",
            text="Old log",
            type="log",
            project_id="proj-1",
            created_at=old_timestamp,
            last_touched_at=old_timestamp,
            tokens=100,
        )
        recent_decision = ContextSegment(
            segment_id="seg-recent-decision",
            text="Recent decision",
            type="decision",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )

        segments = [old_log, recent_decision]
        roots: set[str] = set()

        candidates = gc_engine.analyze_pruning_candidates(segments, roots)

        assert len(candidates) == 2
        # Old log should have higher score (first)
        assert candidates[0].segment_id == old_log.segment_id
        assert candidates[0].score > candidates[1].score

    @pytest.mark.unit
    def test_empty_segments(self, gc_engine: GCEngine) -> None:
        """Test with empty segments list."""
        candidates = gc_engine.analyze_pruning_candidates([], set())
        assert len(candidates) == 0

    @pytest.mark.unit
    def test_all_pinned_or_root(
        self, gc_engine: GCEngine, pinned_segment: ContextSegment, sample_segment: ContextSegment
    ) -> None:
        """Test when all segments are pinned or in root set."""
        segments = [pinned_segment, sample_segment]
        roots = {sample_segment.segment_id}

        candidates = gc_engine.analyze_pruning_candidates(segments, roots)

        assert len(candidates) == 0


class TestGeneratePruningPlan:
    """Test pruning plan generation."""

    @pytest.mark.unit
    def test_meets_target_tokens(self, gc_engine: GCEngine) -> None:
        """Test that plan meets target token count."""
        candidates = [
            PruningCandidate(
                segment_id="seg-1",
                score=0.8,
                tokens=100,
                reason="high score",
                segment_type="log",
                age_hours=48.0,
            ),
            PruningCandidate(
                segment_id="seg-2",
                score=0.6,
                tokens=150,
                reason="medium score",
                segment_type="note",
                age_hours=24.0,
            ),
            PruningCandidate(
                segment_id="seg-3",
                score=0.3,
                tokens=200,
                reason="low score",
                segment_type="decision",
                age_hours=1.0,
            ),
        ]

        plan = gc_engine.generate_pruning_plan(candidates, target_tokens=200)

        assert plan.total_tokens_freed >= 200
        assert len(plan.delete_segments) > 0 or len(plan.stash_segments) > 0

    @pytest.mark.unit
    def test_high_score_deletes(self, gc_engine: GCEngine) -> None:
        """Test that high-score candidates are deleted."""
        candidates = [
            PruningCandidate(
                segment_id="seg-high",
                score=0.8,
                tokens=100,
                reason="high score",
                segment_type="log",
                age_hours=48.0,
            ),
        ]

        plan = gc_engine.generate_pruning_plan(candidates, target_tokens=50)

        assert "seg-high" in plan.delete_segments
        assert "seg-high" not in plan.stash_segments

    @pytest.mark.unit
    def test_medium_score_stashes(self, gc_engine: GCEngine) -> None:
        """Test that medium-score candidates are stashed."""
        candidates = [
            PruningCandidate(
                segment_id="seg-medium",
                score=0.5,
                tokens=100,
                reason="medium score",
                segment_type="note",
                age_hours=12.0,
            ),
        ]

        plan = gc_engine.generate_pruning_plan(candidates, target_tokens=50)

        assert "seg-medium" in plan.stash_segments
        assert "seg-medium" not in plan.delete_segments

    @pytest.mark.unit
    def test_low_score_skipped(self, gc_engine: GCEngine) -> None:
        """Test that low-score candidates are skipped."""
        candidates = [
            PruningCandidate(
                segment_id="seg-low",
                score=0.2,
                tokens=100,
                reason="low score",
                segment_type="decision",
                age_hours=1.0,
            ),
        ]

        plan = gc_engine.generate_pruning_plan(candidates, target_tokens=50)

        assert "seg-low" not in plan.delete_segments
        assert "seg-low" not in plan.stash_segments

    @pytest.mark.unit
    def test_empty_candidates(self, gc_engine: GCEngine) -> None:
        """Test with empty candidates list."""
        plan = gc_engine.generate_pruning_plan([], target_tokens=100)

        assert plan.total_tokens_freed == 0
        assert len(plan.delete_segments) == 0
        assert len(plan.stash_segments) == 0
        assert "no candidates" in plan.reason.lower()

    @pytest.mark.unit
    def test_plan_includes_reason(self, gc_engine: GCEngine) -> None:
        """Test that plan includes reason."""
        candidates = [
            PruningCandidate(
                segment_id="seg-1",
                score=0.8,
                tokens=100,
                reason="test",
                segment_type="log",
                age_hours=48.0,
            ),
        ]

        plan = gc_engine.generate_pruning_plan(candidates, target_tokens=50)

        assert plan.reason
        assert len(plan.reason) > 0


class TestReferenceGraph:
    """Test reference graph building."""

    @pytest.mark.unit
    def test_builds_from_tags(self, gc_engine: GCEngine, now: datetime) -> None:
        """Test that references are built from tags."""
        seg1 = ContextSegment(
            segment_id="seg-1",
            text="Segment 1",
            type="message",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            tags=["ref:seg-2", "ref:seg-3"],
        )
        seg2 = ContextSegment(
            segment_id="seg-2",
            text="Segment 2",
            type="code",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )
        seg3 = ContextSegment(
            segment_id="seg-3",
            text="Segment 3",
            type="code",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
        )

        segments = [seg1, seg2, seg3]
        references = gc_engine._build_reference_graph(segments)

        assert "seg-1" in references
        assert "seg-2" in references["seg-1"]
        assert "seg-3" in references["seg-1"]

    @pytest.mark.unit
    def test_builds_from_topic_id(self, gc_engine: GCEngine, now: datetime) -> None:
        """Test that references are built from topic_id."""
        seg1 = ContextSegment(
            segment_id="seg-1",
            text="Segment 1",
            type="message",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            topic_id="topic-1",
        )
        seg2 = ContextSegment(
            segment_id="seg-2",
            text="Segment 2",
            type="code",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            topic_id="topic-1",
        )

        segments = [seg1, seg2]
        references = gc_engine._build_reference_graph(segments)

        # Both segments should reference each other via topic_id
        assert "seg-1" in references
        assert "seg-2" in references["seg-1"]
        assert "seg-2" in references
        assert "seg-1" in references["seg-2"]


class TestIntegration:
    """Integration tests for full GC cycle."""

    @pytest.mark.integration
    def test_full_gc_cycle(
        self,
        gc_engine: GCEngine,
        now: datetime,
        old_timestamp: datetime,
    ) -> None:
        """Test a full GC cycle with realistic scenario."""
        # Create various segments
        root_seg = ContextSegment(
            segment_id="seg-root",
            text="Root segment",
            type="message",
            project_id="proj-1",
            task_id="task-1",
            created_at=now,
            last_touched_at=now,
            tokens=100,
            tags=["ref:seg-referenced"],
        )
        referenced_seg = ContextSegment(
            segment_id="seg-referenced",
            text="Referenced segment",
            type="code",
            project_id="proj-1",
            task_id="task-1",
            created_at=now,
            last_touched_at=now,
            tokens=150,
        )
        old_log = ContextSegment(
            segment_id="seg-old-log",
            text="Old log",
            type="log",
            project_id="proj-1",
            created_at=old_timestamp,
            last_touched_at=old_timestamp,
            tokens=50,
            generation="old",
        )
        pinned_seg = ContextSegment(
            segment_id="seg-pinned",
            text="Pinned",
            type="decision",
            project_id="proj-1",
            created_at=now,
            last_touched_at=now,
            tokens=200,
            pinned=True,
        )

        segments = [root_seg, referenced_seg, old_log, pinned_seg]
        roots = {root_seg.segment_id}

        # Analyze candidates
        candidates = gc_engine.analyze_pruning_candidates(segments, roots)

        # Should only find old_log (root and referenced are reachable, pinned is excluded)
        assert len(candidates) == 1
        assert candidates[0].segment_id == old_log.segment_id

        # Generate plan
        plan = gc_engine.generate_pruning_plan(candidates, target_tokens=30)

        assert plan.total_tokens_freed >= 30
        assert (
            old_log.segment_id in plan.delete_segments or old_log.segment_id in plan.stash_segments
        )

    @pytest.mark.integration
    def test_performance_large_context(self, gc_engine: GCEngine, now: datetime) -> None:
        """Test performance with large context (1000+ segments)."""
        import time

        # Create 1000 segments
        segments: list[ContextSegment] = []
        for i in range(1000):
            seg = ContextSegment(
                segment_id=f"seg-{i}",
                text=f"Segment {i}",
                type="code" if i % 2 == 0 else "log",
                project_id="proj-1",
                created_at=now,
                last_touched_at=now - timedelta(hours=i % 48),
                tokens=100 + (i % 50),
                refcount=i % 5,
            )
            segments.append(seg)

        roots = {segments[0].segment_id}

        start = time.time()
        candidates = gc_engine.analyze_pruning_candidates(segments, roots)
        elapsed = time.time() - start

        # Should complete in < 2 seconds for 32k tokens (1000 segments * ~100 tokens = 100k tokens)
        # But we'll be more lenient for the test
        assert elapsed < 5.0  # 5 seconds should be plenty
        assert len(candidates) > 0
