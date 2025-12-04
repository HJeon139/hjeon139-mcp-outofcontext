# Task 07: Pruning Tools Implementation

## Dependencies

- Task 05: Context Manager Implementation

## Scope

Implement MCP tools for context pruning operations. This includes:

- Implement `context_gc_analyze` tool
- Implement `context_gc_prune` tool
- Implement `context_gc_pin` and `context_gc_unpin` tools
- Tool parameter validation
- Pruning recommendation formatting

## Acceptance Criteria

- `context_gc_analyze` returns pruning candidates with scores
- `context_gc_prune` executes pruning plan and returns results
- Pinning/unpinning works correctly
- Tools provide clear feedback on actions taken
- Tools handle edge cases (no candidates, all pinned, etc.)

## Implementation Details

### Tool: `context_gc_analyze`

**Purpose:** Analyze context and identify pruning candidates using GC heuristics.

**Parameters:**
```python
{
    "context_descriptors": ContextDescriptors,  # Optional
    "project_id": str,  # Required
    "task_id": Optional[str],  # Optional
    "target_tokens": Optional[int]  # Optional, analyze without target
}
```

**Returns:**
```python
{
    "pruning_candidates": List[PruningCandidate],
    "total_candidates": int,
    "estimated_tokens_freed": int,
    "pruning_plan": Optional[PruningPlan]  # If target_tokens provided
}
```

**Implementation:**
1. Get current segments from storage
2. Compute root set from context descriptors
3. Call GC engine to analyze candidates
4. Generate pruning plan if target_tokens provided
5. Return candidates and plan

### Tool: `context_gc_prune`

**Purpose:** Execute pruning plan to free context space.

**Parameters:**
```python
{
    "project_id": str,  # Required
    "segment_ids": List[str],  # Required, segments to prune
    "action": Literal["stash", "delete"],  # Required
    "confirm": bool = False  # Safety flag
}
```

**Returns:**
```python
{
    "pruned_segments": List[str],  # segment_ids
    "tokens_freed": int,
    "action": str,  # "stashed" or "deleted"
    "errors": List[str]  # Any errors encountered
}
```

**Implementation:**
1. Validate segment IDs exist
2. Check if segments are pinned (error if trying to prune pinned)
3. Execute action (stash or delete)
4. Update storage
5. Return results

### Tool: `context_gc_pin`

**Purpose:** Pin segments to protect them from pruning.

**Parameters:**
```python
{
    "project_id": str,  # Required
    "segment_ids": List[str]  # Required
}
```

**Returns:**
```python
{
    "pinned_segments": List[str],
    "errors": List[str]  # If any segments not found
}
```

### Tool: `context_gc_unpin`

**Purpose:** Unpin segments to allow pruning.

**Parameters:**
```python
{
    "project_id": str,  # Required
    "segment_ids": List[str]  # Required
}
```

**Returns:**
```python
{
    "unpinned_segments": List[str],
    "errors": List[str]
}
```

### Pruning Candidate Format

```python
@dataclass
class PruningCandidate:
    segment_id: str
    score: float  # Higher = more likely to prune
    tokens: int
    reason: str  # Why it's a candidate
    segment_type: str
    age_hours: float
```

### Safety Checks

- Never prune pinned segments (error if attempted)
- Require confirmation for delete actions
- Validate segment IDs exist
- Check permissions (if applicable)

### Error Handling

Handle edge cases:

- No candidates found: Return empty list with message
- All segments pinned: Return error suggesting unpin
- Segment not found: Include in errors list
- Target tokens too high: Return warning

## Testing Approach

### Unit Tests

- Test each tool handler
- Test parameter validation
- Test pruning plan generation
- Test pinning/unpinning
- Test error cases

### Integration Tests

- Test full pruning workflow (analyze → prune)
- Test with GC engine integration
- Test pinning behavior (pinned segments protected)
- Test edge cases (no candidates, all pinned)

### Test Files

- `tests/test_tools_pruning.py` - Pruning tools tests

### Test Scenarios

1. Analyze pruning candidates for context
2. Generate pruning plan with target tokens
3. Execute stash operation
4. Execute delete operation
5. Pin segments and verify protection
6. Attempt to prune pinned segment (error)
7. Test with no candidates (empty result)
8. Test with all segments pinned (error message)

## References

- [Integration Patterns](../design/05_integration_patterns.md) - Tool interface patterns
- [Components](../design/04_components.md) - GC Engine component
- [Design Patterns](../design/06_design_patterns.md) - GC-Inspired Pruning Pattern
- [Interfaces and Data Models](../design/09_interfaces.md) - Tool specifications

