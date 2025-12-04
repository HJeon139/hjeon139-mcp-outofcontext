# Task 09: Task Management Tools Implementation

## Dependencies

- Task 05: Context Manager Implementation

## Scope

Implement MCP tools for task-scoped context management. This includes:

- Implement `context_set_current_task` tool
- Implement `context_get_task_context` tool
- Implement `context_create_task_snapshot` tool
- Task-scoped working set management
- Task metadata tracking

## Acceptance Criteria

- Task switching updates working sets correctly
- Task snapshots capture current state
- Task context retrieval returns correct segments
- Task isolation works (segments scoped to tasks)

## Implementation Details

### Tool: `context_set_current_task`

**Purpose:** Set the active task ID for a project, updating the working set.

**Parameters:**
```python
{
    "project_id": str,  # Required
    "task_id": Optional[str]  # None to clear current task
}
```

**Returns:**
```python
{
    "previous_task_id": Optional[str],
    "current_task_id": Optional[str],
    "working_set_updated": bool
}
```

**Implementation:**
1. Update current task for project
2. Recompute working set for new task
3. Return previous and current task IDs

### Tool: `context_get_task_context`

**Purpose:** Get all context segments for a specific task.

**Parameters:**
```python
{
    "project_id": str,  # Required
    "task_id": Optional[str]  # None uses current task
}
```

**Returns:**
```python
{
    "task_id": str,
    "segments": List[ContextSegment],
    "total_tokens": int,
    "segment_count": int,
    "active": bool  # Is this the current task?
}
```

**Implementation:**
1. Get task_id (from param or current task)
2. Query storage for segments with task_id
3. Return task context

### Tool: `context_create_task_snapshot`

**Purpose:** Create a snapshot of current task state for later retrieval.

**Parameters:**
```python
{
    "project_id": str,  # Required
    "task_id": Optional[str],  # None uses current task
    "name": Optional[str]  # Optional snapshot name
}
```

**Returns:**
```python
{
    "snapshot_id": str,
    "task_id": str,
    "segments_captured": int,
    "tokens_captured": int,
    "created_at": str  # ISO datetime
}
```

**Implementation:**
1. Get current task segments
2. Create snapshot record with metadata
3. Store snapshot (can reuse stashed storage with snapshot tag)
4. Return snapshot ID

### Working Set Management

Working set automatically updates when task changes:

```python
def update_working_set(project_id: str, task_id: Optional[str]):
    """Update working set for current task."""
    if task_id is None:
        # Clear working set
        working_set = WorkingSet(segments=[], total_tokens=0, ...)
    else:
        # Get segments for task
        segments = get_task_segments(project_id, task_id)
        working_set = WorkingSet(segments=segments, ...)
    
    self.working_sets[project_id][task_id] = working_set
```

### Task Metadata Tracking

Track task metadata:

```python
@dataclass
class TaskMetadata:
    task_id: str
    project_id: str
    created_at: datetime
    last_accessed: datetime
    segment_count: int
    total_tokens: int
    snapshots: List[str]  # snapshot_ids
```

### Task Isolation

Ensure segments are properly scoped:

- Segments belong to a task_id (or None for untasked)
- Task switching doesn't affect other tasks' segments
- Working set only includes current task segments

## Testing Approach

### Unit Tests

- Test task switching
- Test working set updates
- Test task context retrieval
- Test snapshot creation

### Integration Tests

- Test task isolation (segments don't mix)
- Test working set across task switches
- Test snapshot retrieval
- Test concurrent tasks

### Test Files

- `tests/test_tools_tasks.py` - Task management tools tests

### Test Scenarios

1. Set current task and verify working set update
2. Switch tasks and verify working set changes
3. Get task context for specific task
4. Get task context for current task
5. Create task snapshot
6. Verify task isolation (segments don't mix between tasks)
7. Clear current task (set to None)
8. Test with multiple tasks in same project

## References

- [Integration Patterns](../design/05_integration_patterns.md) - Tool interface patterns
- [Design Patterns](../design/06_design_patterns.md) - Task-Centric Organization pattern
- [Components](../design/04_components.md) - Context Manager component
- [Interfaces and Data Models](../design/09_interfaces.md) - Task management interfaces

