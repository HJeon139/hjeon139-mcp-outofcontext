"""Analysis Engine for context usage metrics, health scoring, and recommendations."""

import logging
import math
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING

from .models import ContextSegment, HealthScore, Recommendation, UsageMetrics
from .tokenizer import Tokenizer

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class IAnalysisEngine(ABC):
    """Interface for Analysis Engine operations."""

    @abstractmethod
    def analyze_context_usage(
        self,
        segments: list[ContextSegment],
        token_limit: int = 32000,
    ) -> UsageMetrics:
        """Analyze context usage and return metrics.

        Args:
            segments: List of context segments to analyze
            token_limit: Token limit for usage percentage calculation

        Returns:
            Usage metrics
        """

    @abstractmethod
    def compute_health_score(
        self,
        segments: list[ContextSegment],
        token_limit: int = 32000,
    ) -> HealthScore:
        """Compute context health score.

        Args:
            segments: List of context segments
            token_limit: Token limit for usage calculation

        Returns:
            Health score (0-100, higher = healthier)
        """

    @abstractmethod
    def generate_recommendations(
        self,
        metrics: UsageMetrics,
    ) -> list[Recommendation]:
        """Generate recommendations based on usage metrics.

        Args:
            metrics: Usage metrics to analyze

        Returns:
            List of recommendations
        """


class AnalysisEngine(IAnalysisEngine):
    """Analysis Engine implementation."""

    def __init__(self, tokenizer: Tokenizer | None = None, model: str = "gpt-4") -> None:
        """Initialize Analysis Engine.

        Args:
            tokenizer: Tokenizer instance (creates new one if None)
            model: Model name for tokenizer (used if tokenizer is None)
        """
        self.tokenizer = tokenizer if tokenizer is not None else Tokenizer(model=model)

    def analyze_context_usage(
        self,
        segments: list[ContextSegment],
        token_limit: int = 32000,
    ) -> UsageMetrics:
        """Analyze context usage and return metrics.

        Args:
            segments: List of context segments to analyze
            token_limit: Token limit for usage percentage calculation

        Returns:
            Usage metrics
        """
        if not segments:
            return UsageMetrics(
                total_tokens=0,
                total_segments=0,
                tokens_by_type={},
                segments_by_type={},
                tokens_by_task={},
                oldest_segment_age_hours=0.0,
                newest_segment_age_hours=0.0,
                pinned_segments_count=0,
                pinned_tokens=0,
                usage_percent=0.0,
                estimated_remaining_tokens=token_limit,
            )

        now = datetime.now()

        # Aggregate metrics
        total_tokens = 0
        tokens_by_type: dict[str, int] = defaultdict(int)
        segments_by_type: dict[str, int] = defaultdict(int)
        tokens_by_task: dict[str, int] = defaultdict(int)
        pinned_segments_count = 0
        pinned_tokens = 0

        # Track ages
        ages_hours: list[float] = []

        for segment in segments:
            # Count tokens (use cached if available)
            tokens = self.tokenizer.count_segment_tokens(segment)
            total_tokens += tokens

            # By type
            tokens_by_type[segment.type] += tokens
            segments_by_type[segment.type] += 1

            # By task
            if segment.task_id:
                tokens_by_task[segment.task_id] += tokens

            # Pinned segments
            if segment.pinned:
                pinned_segments_count += 1
                pinned_tokens += tokens

            # Age calculation
            age_hours = (now - segment.last_touched_at).total_seconds() / 3600.0
            ages_hours.append(age_hours)

        # Calculate usage percentage
        usage_percent = (total_tokens / token_limit * 100.0) if token_limit > 0 else 0.0
        estimated_remaining_tokens = max(0, token_limit - total_tokens)

        # Age metrics
        oldest_segment_age_hours = max(ages_hours) if ages_hours else 0.0
        newest_segment_age_hours = min(ages_hours) if ages_hours else 0.0

        return UsageMetrics(
            total_tokens=total_tokens,
            total_segments=len(segments),
            tokens_by_type=dict(tokens_by_type),
            segments_by_type=dict(segments_by_type),
            tokens_by_task=dict(tokens_by_task),
            oldest_segment_age_hours=oldest_segment_age_hours,
            newest_segment_age_hours=newest_segment_age_hours,
            pinned_segments_count=pinned_segments_count,
            pinned_tokens=pinned_tokens,
            usage_percent=usage_percent,
            estimated_remaining_tokens=estimated_remaining_tokens,
        )

    def compute_health_score(
        self,
        segments: list[ContextSegment],
        token_limit: int = 32000,
    ) -> HealthScore:
        """Compute context health score (0-100, higher = healthier).

        Args:
            segments: List of context segments
            token_limit: Token limit for usage calculation

        Returns:
            Health score
        """
        if not segments:
            return HealthScore(
                score=100.0,
                usage_percent=0.0,
                factors={"usage": 100.0, "age_penalty": 0.0, "distribution": 0.0},
            )

        # Get usage metrics
        metrics = self.analyze_context_usage(segments, token_limit)
        usage_percent = metrics.usage_percent

        # Base score from usage (lower usage = higher score)
        usage_score = max(0.0, 100.0 - usage_percent)

        # Penalty for very old segments
        oldest_age_days = metrics.oldest_segment_age_hours / 24.0
        age_penalty = min(20.0, oldest_age_days * 2.0)  # Max 20 point penalty

        # Bonus for good distribution
        distribution_score = self._compute_distribution_score(segments)

        # Combine scores
        total_score = usage_score - age_penalty + distribution_score

        return HealthScore(
            score=min(100.0, max(0.0, total_score)),
            usage_percent=usage_percent,
            factors={
                "usage": usage_score,
                "age_penalty": -age_penalty,
                "distribution": distribution_score,
            },
        )

    def generate_recommendations(  # noqa: C901
        self,
        metrics: UsageMetrics,
    ) -> list[Recommendation]:
        """Generate recommendations based on usage metrics.

        Args:
            metrics: Usage metrics to analyze

        Returns:
            List of recommendations
        """
        recommendations: list[Recommendation] = []

        # High usage recommendations
        if metrics.usage_percent >= 90.0:
            recommendations.append(
                Recommendation(
                    priority="urgent",
                    message="Urgent: Prune context immediately",
                    action="prune",
                )
            )
        elif metrics.usage_percent >= 80.0:
            recommendations.append(
                Recommendation(
                    priority="high",
                    message="Consider pruning old segments to free space",
                    action="prune",
                )
            )
        elif metrics.usage_percent >= 60.0:
            recommendations.append(
                Recommendation(
                    priority="medium",
                    message="Context usage at 60%+ - monitor closely and consider stashing old segments",
                    action="stash",
                )
            )
        elif metrics.usage_percent < 50.0:
            recommendations.append(
                Recommendation(
                    priority="low",
                    message="Context usage is healthy, no action needed",
                    action=None,
                )
            )

        # Old segments recommendation
        if metrics.oldest_segment_age_hours > 24.0:
            recommendations.append(
                Recommendation(
                    priority="medium",
                    message="Stash segments older than 24 hours",
                    action="stash",
                )
            )

        # Distribution recommendations
        if metrics.total_segments > 0:
            # Check if distribution is unbalanced
            type_counts = list(metrics.segments_by_type.values())
            if len(type_counts) > 0:
                max_type_count = max(type_counts)
                total_segments = metrics.total_segments
                # If one type dominates (>60% of segments)
                if max_type_count / total_segments > 0.6:
                    dominant_type = max(metrics.segments_by_type.items(), key=lambda x: x[1])[0]
                    if dominant_type == "log":
                        recommendations.append(
                            Recommendation(
                                priority="medium",
                                message="Too many log segments, consider stashing",
                                action="stash",
                            )
                        )

        # All segments pinned recommendation
        if (
            metrics.pinned_segments_count > 0
            and metrics.pinned_segments_count == metrics.total_segments
        ):
            recommendations.append(
                Recommendation(
                    priority="low",
                    message="All segments are pinned, consider unpinning some",
                    action="unpin",
                )
            )

        return recommendations

    def _compute_distribution_score(self, segments: list[ContextSegment]) -> float:
        """Compute distribution score bonus (0-10 points).

        Args:
            segments: List of segments

        Returns:
            Distribution score (0-10, higher = better distribution)
        """
        if len(segments) <= 1:
            return 5.0  # Neutral score for single/empty

        # Count segments by type
        type_counts: dict[str, int] = defaultdict(int)
        for segment in segments:
            type_counts[segment.type] += 1

        # Calculate entropy (measure of diversity)
        # Shannon entropy: -sum(p * log2(p))
        total = len(segments)
        entropy = 0.0
        for count in type_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        # Normalize to 0-10 scale
        # Maximum entropy occurs when all types are equally distributed
        num_types = len(type_counts)
        if num_types > 1:
            max_entropy = math.log2(num_types)
            normalized = (entropy / max_entropy) * 10.0 if max_entropy > 0 else 5.0
        else:
            # Only one type = no diversity
            normalized = 0.0

        return min(10.0, max(0.0, normalized))
