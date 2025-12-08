# Task 07: Pruning Tools Implementation

## Dependencies

- Task 05: Context Manager Implementation
- Task 06a: Storage Layer Scalability Enhancements (for GC sweep optimization)

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
3. Call GC engine to analyze candidates (uses optimized heap-based selection)
4. Generate pruning plan if target_tokens provided
5. Return candidates and plan

**Scalability Note:** GC engine uses heap-based top-k selection instead of full sort for performance at scale (see Task 06a and scalability analysis).

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

## GC Engine Optimization

**Scalability Enhancement:** The GC engine sweep phase must use heap-based top-k selection instead of full sort for millions of tokens.

**Implementation in GC Engine:**

```python
import heapq

def generate_pruning_plan(candidates: List[PruningCandidate], target_tokens: int) -> PruningPlan:
    """Generate pruning plan using heap-based top-k selection."""
    # Use heap to get top-k lowest scores (best candidates to prune)
    # Instead of sorting all candidates (O(n log n)), use heap (O(n log k))
    
    if not candidates:
        return PruningPlan(segments=[], estimated_tokens_freed=0)
    
    # Use min-heap to get lowest scores (most pruneable)
    # Heap stores (-score, segment_id) to make it a max-heap for scores
    heap = []
    total_tokens = 0
    
    for candidate in candidates:
        # Push with negative score for max-heap behavior
        heapq.heappush(heap, (-candidate.score, candidate))
        total_tokens += candidate.tokens
        
        # If we have enough candidates to meet target, we can stop early
        if total_tokens >= target_tokens and len(heap) > 1000:
            # Keep only top candidates
            heap = heapq.nlargest(1000, heap)
            break
    
    # Extract top candidates (lowest scores = most pruneable)
    selected = []
    tokens_freed = 0
    
    # Pop from heap (lowest scores first)
    while heap and tokens_freed < target_tokens:
        neg_score, candidate = heapq.heappop(heap)
        selected.append(candidate)
        tokens_freed += candidate.tokens
    
    return PruningPlan(segments=selected, estimated_tokens_freed=tokens_freed)
```

**Performance Impact:**
- Full sort: O(n log n) for all candidates
- Heap-based: O(n log k) where k is number needed
- For millions of segments, this reduces analysis time significantly

## References

- [Integration Patterns](../design/05_integration_patterns.md) - Tool interface patterns
- [Components](../design/04_components.md) - GC Engine component
- [Design Patterns](../design/06_design_patterns.md) - GC-Inspired Pruning Pattern
- [Interfaces and Data Models](../design/09_interfaces.md) - Tool specifications
- [Scalability Analysis](../design/10_scalability_analysis.md) - GC sweep optimization
- [Storage Scalability Enhancements](06a_storage_scalability_enhancements.md) - Related enhancements

