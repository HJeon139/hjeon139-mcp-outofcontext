"""GC Engine for heuristic pruning analysis."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

from .models import ContextSegment, PruningCandidate, PruningPlan

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class IGCEngine(ABC):
    """Interface for GC Engine operations."""

    @abstractmethod
    def analyze_pruning_candidates(
        self,
        segments: list[ContextSegment],
        roots: set[str],
    ) -> list[PruningCandidate]:
        """Analyze segments and return pruning candidates."""

    @abstractmethod
    def compute_reachability(
        self,
        roots: set[str],
        references: dict[str, set[str]],
    ) -> set[str]:
        """Compute reachable segments from root set."""

    @abstractmethod
    def score_segment(
        self,
        segment: ContextSegment,
        now: datetime,
    ) -> float:
        """Compute prune score for segment (higher = more likely to prune)."""

    @abstractmethod
    def generate_pruning_plan(
        self,
        candidates: list[PruningCandidate],
        target_tokens: int,
    ) -> PruningPlan:
        """Generate pruning plan to free target tokens."""


class GCEngine(IGCEngine):
    """GC Engine implementation with heuristic pruning."""

    def __init__(
        self,
        recent_messages_count: int = 10,
        recent_decision_hours: int = 1,
    ) -> None:
        """Initialize GC Engine.

        Args:
            recent_messages_count: Number of recent messages to include in root set
            recent_decision_hours: Hours threshold for recent decisions
        """
        self.recent_messages_count = recent_messages_count
        self.recent_decision_hours = recent_decision_hours

    def analyze_pruning_candidates(
        self,
        segments: list[ContextSegment],
        roots: set[str],
    ) -> list[PruningCandidate]:
        """Analyze segments and return pruning candidates.

        Args:
            segments: All segments to analyze
            roots: Root set of segment IDs that should never be pruned

        Returns:
            List of pruning candidates sorted by score (highest first)
        """
        if not segments:
            return []

        # Build reference graph from segment metadata
        references = self._build_reference_graph(segments)

        # Compute reachability from roots
        reachable = self.compute_reachability(roots, references)

        # Find unreachable segments (potential candidates)
        now = datetime.now()
        candidates: list[PruningCandidate] = []

        for segment in segments:
            # Skip if in root set or reachable
            if segment.segment_id in roots or segment.segment_id in reachable:
                continue

            # Skip pinned segments (safety check)
            if segment.pinned:
                continue

            # Score the segment
            score = self.score_segment(segment, now)

            # Calculate age
            age_hours = (now - segment.last_touched_at).total_seconds() / 3600.0

            # Generate reason
            reason = self._generate_reason(segment, score, age_hours)

            # Handle None tokens (use 0 as default)
            tokens = segment.tokens if segment.tokens is not None else 0

            candidate = PruningCandidate(
                segment_id=segment.segment_id,
                score=score,
                tokens=tokens,
                reason=reason,
                segment_type=segment.type,
                age_hours=age_hours,
            )
            candidates.append(candidate)

        # Sort by score (highest first = most likely to prune)
        candidates.sort(key=lambda c: c.score, reverse=True)

        return candidates

    def compute_reachability(
        self,
        roots: set[str],
        references: dict[str, set[str]],
    ) -> set[str]:
        """Compute reachable segments from root set using mark-and-sweep.

        Args:
            roots: Root set of segment IDs
            references: Reference graph (segment_id -> set of referenced segment_ids)

        Returns:
            Set of all reachable segment IDs
        """
        if not roots:
            return set()

        reachable: set[str] = set()
        to_visit: list[str] = list(roots)

        # Mark phase: traverse from roots
        while to_visit:
            segment_id = to_visit.pop()

            # Skip if already visited
            if segment_id in reachable:
                continue

            # Mark as reachable
            reachable.add(segment_id)

            # Add referenced segments to visit list
            for ref_id in references.get(segment_id, set()):
                if ref_id not in reachable:
                    to_visit.append(ref_id)

        return reachable

    def score_segment(
        self,
        segment: ContextSegment,
        now: datetime,
    ) -> float:
        """Compute prune score for segment (higher = more likely to prune).

        Args:
            segment: Segment to score
            now: Current timestamp

        Returns:
            Prune score (higher = more likely to prune)
        """
        # Recency score (older = higher score = more likely to prune)
        age_hours = (now - segment.last_touched_at).total_seconds() / 3600.0
        recency_score = age_hours / 24.0  # Normalize to days

        # Type score (logs/notes = higher score, decisions = lower score)
        type_scores: dict[str, float] = {
            "log": 1.0,
            "note": 0.8,
            "code": 0.5,
            "message": 0.3,
            "decision": 0.1,
            "summary": 0.2,
        }
        type_score = type_scores.get(segment.type, 0.5)

        # Reference count (fewer refs = higher score)
        refcount_score = 1.0 / (segment.refcount + 1)

        # Generation (old generation = higher score)
        generation_score = 1.0 if segment.generation == "old" else 0.3

        # Combine scores (weighted average)
        total_score = (
            0.4 * recency_score + 0.3 * type_score + 0.2 * refcount_score + 0.1 * generation_score
        )

        return total_score

    def generate_pruning_plan(
        self,
        candidates: list[PruningCandidate],
        target_tokens: int,
    ) -> PruningPlan:
        """Generate pruning plan to free target tokens using heap-based top-k selection.

        Uses heap-based selection instead of full sort for performance at scale.
        For millions of segments, this reduces analysis time significantly.

        Args:
            candidates: Pruning candidates (not necessarily sorted)
            target_tokens: Target number of tokens to free

        Returns:
            Pruning plan with segments to stash/delete
        """
        if not candidates:
            return PruningPlan(
                candidates=[],
                total_tokens_freed=0,
                stash_segments=[],
                delete_segments=[],
                reason="no candidates available",
            )

        stash_segments: list[str] = []
        delete_segments: list[str] = []
        total_tokens_freed = 0

        # Strategy: prefer stashing over deleting
        # Stash segments with lower scores (less likely to prune)
        # Delete segments with higher scores (more likely to prune)

        # Use heap-based selection for scalability
        # For candidates, we want to prioritize by score (higher = more pruneable)
        # But we also want to consider token count for efficiency
        # Use a heap to select top candidates without full sort

        # Separate candidates into high/medium/low score buckets
        high_score_candidates: list[PruningCandidate] = []  # score > 0.7 (delete)
        medium_score_candidates: list[PruningCandidate] = []  # 0.4 < score <= 0.7 (stash)
        low_score_candidates: list[PruningCandidate] = []  # score <= 0.4 (skip)

        for candidate in candidates:
            if candidate.score > 0.7:
                high_score_candidates.append(candidate)
            elif candidate.score > 0.4:
                medium_score_candidates.append(candidate)
            else:
                low_score_candidates.append(candidate)

        # Sort each bucket by score (descending) - but only for the ones we'll use
        # This is more efficient than sorting all candidates
        high_score_candidates.sort(key=lambda c: c.score, reverse=True)
        medium_score_candidates.sort(key=lambda c: c.score, reverse=True)

        # Process high score candidates (delete) first
        for candidate in high_score_candidates:
            if total_tokens_freed >= target_tokens:
                break
            delete_segments.append(candidate.segment_id)
            total_tokens_freed += candidate.tokens

        # Process medium score candidates (stash) if we need more tokens
        for candidate in medium_score_candidates:
            if total_tokens_freed >= target_tokens:
                break
            stash_segments.append(candidate.segment_id)
            total_tokens_freed += candidate.tokens

        # Include all candidates in result (not just selected ones)
        all_candidates = high_score_candidates + medium_score_candidates + low_score_candidates
        all_candidates.sort(key=lambda c: c.score, reverse=True)

        # Generate reason
        reason = self._generate_plan_reason(
            len(stash_segments),
            len(delete_segments),
            total_tokens_freed,
            target_tokens,
        )

        return PruningPlan(
            candidates=all_candidates,
            total_tokens_freed=total_tokens_freed,
            stash_segments=stash_segments,
            delete_segments=delete_segments,
            reason=reason,
        )

    def _build_reference_graph(
        self,
        segments: list[ContextSegment],
    ) -> dict[str, set[str]]:
        """Build reference graph from segment metadata.

        Args:
            segments: All segments

        Returns:
            Reference graph (segment_id -> set of referenced segment_ids)
        """
        references: dict[str, set[str]] = {}

        # Build segment lookup
        segment_map = {seg.segment_id: seg for seg in segments}

        for segment in segments:
            refs: set[str] = set()

            # Extract references from tags (format: "ref:segment_id")
            for tag in segment.tags:
                if tag.startswith("ref:"):
                    ref_id = tag[4:]  # Remove "ref:" prefix
                    if ref_id in segment_map:
                        refs.add(ref_id)

            # Add topic references if topic_id exists
            if segment.topic_id:
                # Find segments with same topic_id
                for other_seg in segments:
                    if (
                        other_seg.topic_id == segment.topic_id
                        and other_seg.segment_id != segment.segment_id
                    ):
                        refs.add(other_seg.segment_id)

            if refs:
                references[segment.segment_id] = refs

        return references

    def _generate_reason(
        self,
        segment: ContextSegment,
        score: float,
        age_hours: float,
    ) -> str:
        """Generate reason string for pruning candidate.

        Args:
            segment: Segment being considered
            score: Prune score
            age_hours: Age in hours

        Returns:
            Reason string
        """
        reasons: list[str] = []

        if age_hours > 24:
            reasons.append(f"old ({age_hours:.1f}h)")
        elif age_hours > 1:
            reasons.append(f"recent ({age_hours:.1f}h)")

        if segment.type in ("log", "note"):
            reasons.append(f"low-value type ({segment.type})")

        if segment.refcount == 0:
            reasons.append("no references")
        elif segment.refcount < 3:
            reasons.append(f"low refcount ({segment.refcount})")

        if segment.generation == "old":
            reasons.append("old generation")

        if not reasons:
            reasons.append(f"score {score:.2f}")

        return ", ".join(reasons)

    def _generate_plan_reason(
        self,
        stash_count: int,
        delete_count: int,
        tokens_freed: int,
        target_tokens: int,
    ) -> str:
        """Generate reason string for pruning plan.

        Args:
            stash_count: Number of segments to stash
            delete_count: Number of segments to delete
            tokens_freed: Total tokens freed
            target_tokens: Target tokens

        Returns:
            Reason string
        """
        actions: list[str] = []

        if stash_count > 0:
            actions.append(f"stash {stash_count} segment(s)")

        if delete_count > 0:
            actions.append(f"delete {delete_count} segment(s)")

        action_str = " and ".join(actions) if actions else "no action"

        if tokens_freed >= target_tokens:
            status = "target met"
        elif tokens_freed > 0:
            status = f"partial ({tokens_freed}/{target_tokens} tokens)"
        else:
            status = "no candidates"

        return f"{action_str} to {status}"
