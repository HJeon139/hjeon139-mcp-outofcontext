# Task 05: Context Manager Implementation

## Dependencies

- Task 02: Storage Layer Implementation
- Task 03: GC Engine Implementation
- Task 04: Analysis Engine Implementation

## Scope

Implement the context manager that orchestrates all context management operations. This includes:

- Implement `IContextManager` interface from [09_interfaces.md](../design/09_interfaces.md)
- Orchestrate GC Engine, Storage Layer, and Analysis Engine
- Manage project/task-scoped state
- Working set abstraction
- Coordinate context operations (analyze, stash, retrieve)

## Acceptance Criteria

- Context Manager coordinates all components correctly
- Project/task scoping works end-to-end
- Working sets reflect current task context
- Operations are atomic and consistent
- Error handling propagates correctly

## Implementation Details

### Context Manager Interface

Implement the `IContextManager` interface with the following methods:

- `analyze_context(descriptors: ContextDescriptors, project_id: str) -> AnalysisResult`
- `get_working_set(project_id: str, task_id: Optional[str]) -> WorkingSet`
- `stash_segments(segment_ids: List[str], project_id: str) -> StashResult`
- `retrieve_stashed(query: str, filters: Dict, project_id: str) -> List[ContextSegment]`

### Component Coordination

Context Manager coordinates:

1. **Storage Layer**: For segment storage and retrieval
2. **GC Engine**: For pruning analysis
3. **Analysis Engine**: For metrics and health scoring

### Project/Task Scoping

Maintain state per project and task:

```python
class ContextManager:
    def __init__(self, storage: IStorageLayer, gc_engine: IGCEngine, analysis_engine: IAnalysisEngine):
        self.storage = storage
        self.gc_engine = gc_engine
        self.analysis_engine = analysis_engine
        self.current_tasks: Dict[str, Optional[str]] = {}  # project_id -> task_id
        self.working_sets: Dict[str, Dict[str, WorkingSet]] = {}  # project_id -> task_id -> working_set
```

### Working Set Abstraction

Working set represents active context for current task:

```python
@dataclass
class WorkingSet:
    segments: List[ContextSegment]
    total_tokens: int
    task_id: Optional[str]
    project_id: str
    last_updated: datetime
```

Working set includes:
- Segments for current task
- Recent messages (last 10)
- Active file segments
- Pinned segments

### Analyze Context Operation

1. Receive context descriptors from platform
2. Convert descriptors to segments (if needed)
3. Store segments in storage
4. Compute metrics using analysis engine
5. Compute health score
6. Generate recommendations
7. Return analysis result

### Stash Segments Operation

1. Retrieve segments by IDs from storage
2. Move segments to stashed storage
3. Update indexes
4. Return stash result with token counts

### Retrieve Stashed Operation

1. Search stashed segments using storage layer
2. Filter by query and metadata
3. Return matching segments

### Error Handling

- Propagate errors from components with context
- Handle missing segments gracefully
- Handle storage errors (retry or fail clearly)
- Validate project_id and task_id

### Atomic Operations

Ensure operations are atomic:

- Stash operation: All segments stashed or none
- Analysis: Consistent snapshot of context state
- Working set updates: Atomic updates

## Testing Approach

### Unit Tests

- Test component coordination
- Test project/task scoping
- Test working set management
- Test error propagation

### Integration Tests

- Test full context operations end-to-end
- Test project isolation
- Test task switching
- Test concurrent operations (if applicable)

### Test Files

- `tests/test_context_manager.py` - Context manager tests

### Test Scenarios

1. Analyze context with various segment types
2. Stash segments and verify removal from active
3. Retrieve stashed segments by query
4. Switch tasks and verify working set updates
5. Test project isolation (segments don't mix)
6. Test error handling (missing segments, storage errors)
7. Test atomic operations (partial stash failure)

## References

- [Interfaces and Data Models](../design/09_interfaces.md) - Context Manager interface specification
- [Components](../design/04_components.md) - Context Manager component details
- [Integration Patterns](../design/05_integration_patterns.md) - How components integrate
- [Design Patterns](../design/06_design_patterns.md) - Working set and task-scoped patterns

