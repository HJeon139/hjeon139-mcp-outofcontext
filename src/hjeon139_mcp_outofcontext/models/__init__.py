"""Core data models for context management."""

# Analysis models
from .analysis import AnalysisResult, HealthScore, Recommendation, UsageMetrics

# Descriptor models
from .descriptors import (
    ContextDescriptors,
    FileInfo,
    Message,
    TaskInfo,
    TokenUsage,
)

# Parameter models
from .params import (
    AnalyzeUsageParams,
    CreateTaskSnapshotParams,
    GCAnalyzeParams,
    GCPinParams,
    GCPruneParams,
    GCUnpinParams,
    GetTaskContextParams,
    GetWorkingSetParams,
    RetrieveStashedParams,
    SearchStashedParams,
    SetCurrentTaskParams,
    StashParams,
)

# Pruning models
from .pruning import PruningCandidate, PruningPlan, PruningRecommendation

# Segment models
from .segments import ContextSegment, SegmentSummary

# Stashing models
from .stashing import StashResult

# Working set models
from .working_set import WorkingSet

__all__ = [
    "AnalysisResult",
    "AnalyzeUsageParams",
    "ContextDescriptors",
    "ContextSegment",
    "CreateTaskSnapshotParams",
    "FileInfo",
    "GCAnalyzeParams",
    "GCPinParams",
    "GCPruneParams",
    "GCUnpinParams",
    "GetTaskContextParams",
    "GetWorkingSetParams",
    "HealthScore",
    "Message",
    "PruningCandidate",
    "PruningPlan",
    "PruningRecommendation",
    "Recommendation",
    "RetrieveStashedParams",
    "SearchStashedParams",
    "SegmentSummary",
    "SetCurrentTaskParams",
    "StashParams",
    "StashResult",
    "TaskInfo",
    "TokenUsage",
    "UsageMetrics",
    "WorkingSet",
]
