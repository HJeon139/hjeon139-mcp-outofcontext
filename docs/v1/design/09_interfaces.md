# Interfaces and Data Models

This document defines the core data models and interface contracts for components.

---

## Context Segment Model

**Core Data Model:**
```python
class ContextSegment(BaseModel):
    segment_id: str
    text: str
    type: Literal["message", "code", "log", "note", "decision", "summary"]
    
    # Metadata
    project_id: str
    task_id: Optional[str]
    created_at: datetime
    last_touched_at: datetime
    
    # GC Metadata
    pinned: bool = False
    generation: Literal["young", "old"] = "young"
    gc_survival_count: int = 0
    refcount: int = 0
    
    # Organization
    file_path: Optional[str] = None
    line_range: Optional[Tuple[int, int]] = None
    tags: List[str] = []
    topic_id: Optional[str] = None
    
    # Storage
    tokens: int
    tier: Literal["working", "stashed", "archive"] = "working"
```

---

## Interface Contracts

### Context Manager Interface

```python
class IContextManager(ABC):
    @abstractmethod
    def analyze_context(
        self, 
        descriptors: ContextDescriptors, 
        project_id: str
    ) -> AnalysisResult:
        """Analyze context and return usage metrics."""
        
    @abstractmethod
    def get_working_set(
        self, 
        project_id: str, 
        task_id: Optional[str]
    ) -> WorkingSet:
        """Get current working set segments."""
        
    @abstractmethod
    def stash_segments(
        self, 
        segment_ids: List[str], 
        project_id: str
    ) -> StashResult:
        """Move segments to stashed storage."""
        
    @abstractmethod
    def retrieve_stashed(
        self,
        query: str,
        filters: Dict,
        project_id: str
    ) -> List[ContextSegment]:
        """Retrieve stashed segments by keyword/metadata search."""
```

### GC Engine Interface

```python
class IGCEngine(ABC):
    @abstractmethod
    def analyze_pruning_candidates(
        self,
        segments: List[ContextSegment],
        roots: Set[str]
    ) -> List[PruningCandidate]:
        """Analyze segments and return pruning candidates."""
        
    @abstractmethod
    def compute_reachability(
        self,
        roots: Set[str],
        references: Dict[str, Set[str]]
    ) -> Set[str]:
        """Compute reachable segments from root set."""
        
    @abstractmethod
    def score_segment(
        self,
        segment: ContextSegment,
        now: datetime
    ) -> float:
        """Compute prune score for segment (lower = more likely to prune)."""
        
    @abstractmethod
    def generate_pruning_plan(
        self,
        candidates: List[PruningCandidate],
        target_tokens: int
    ) -> PruningPlan:
        """Generate pruning plan to free target tokens."""
```

### Storage Layer Interface

```python
class IStorageLayer(ABC):
    @abstractmethod
    def store_segment(
        self,
        segment: ContextSegment,
        project_id: str
    ) -> None:
        """Store segment in active storage."""
        
    @abstractmethod
    def load_segments(
        self,
        project_id: str
    ) -> List[ContextSegment]:
        """Load all segments for a project."""
        
    @abstractmethod
    def stash_segment(
        self,
        segment: ContextSegment,
        project_id: str
    ) -> None:
        """Move segment to stashed storage."""
        
    @abstractmethod
    def search_stashed(
        self,
        query: str,
        filters: Dict,
        project_id: str
    ) -> List[ContextSegment]:
        """Search stashed segments by keyword and metadata."""
        
    @abstractmethod
    def delete_segment(
        self,
        segment_id: str,
        project_id: str
    ) -> None:
        """Delete segment from storage."""
```

### Analysis Engine Interface

```python
class IAnalysisEngine(ABC):
    @abstractmethod
    def analyze_context_usage(
        self,
        segments: List[ContextSegment]
    ) -> UsageMetrics:
        """Analyze context usage and return metrics."""
        
    @abstractmethod
    def compute_health_score(
        self,
        segments: List[ContextSegment]
    ) -> HealthScore:
        """Compute context health score."""
        
    @abstractmethod
    def generate_recommendations(
        self,
        metrics: UsageMetrics
    ) -> List[Recommendation]:
        """Generate recommendations based on usage metrics."""
```

---

## Tool Interface Pattern

**Standard Tool Signature:**
```python
@mcp_tool("tool_name")
def tool_handler(
    # Context descriptors from platform
    context_descriptors: Optional[ContextDescriptors] = None,
    # Project/task scoping
    project_id: str,
    task_id: Optional[str] = None,
    # Tool-specific parameters
    **kwargs
) -> ToolResult:
    """
    Tool description explaining:
    - What it does
    - When to use it
    - Example usage
    """
    # Implementation delegates to Context Manager
    pass
```

---

## Supporting Data Models

### Context Descriptors

```python
@dataclass
class ContextDescriptors:
    recent_messages: List[Message]  # Last N messages
    current_file: Optional[FileInfo]  # Active file and location
    token_usage: TokenUsage  # Current token counts
    segment_summaries: List[SegmentSummary]  # High-level segment info
    task_info: Optional[TaskInfo]  # Current task metadata
```

### Pruning Recommendation

```python
@dataclass
class PruningRecommendation:
    segment_ids: List[str]  # Segments to prune
    action: Literal["stash", "delete"]  # What to do
    reason: str  # Why (e.g., "old + low refcount")
    tokens_freed: int  # Estimated tokens saved
```

---

## Implementation Notes

These interfaces define **contracts**, not implementations:
- Interfaces specify what operations are available
- Implementation details are flexible
- Multiple implementations can satisfy the same interface
- Enables dependency injection and testing

---

## References

- [Components](04_components.md) - Component specifications that implement these interfaces
- [Integration Patterns](05_integration_patterns.md) - How interfaces are used in tool integration

