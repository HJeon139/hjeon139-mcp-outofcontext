# Task 03: GC Engine Implementation

## Dependencies

- Task 02: Storage Layer Implementation

## Scope

Implement the GC (Garbage Collection) engine that performs heuristic pruning analysis on context segments. This includes:

- Implement `IGCEngine` interface from [09_interfaces.md](../design/09_interfaces.md)
- Root set computation (current task, active file, recent messages, pinned segments)
- Mark-and-sweep reachability analysis
- Segment scoring heuristics (recency, type, refcount, generation)
- Pruning candidate identification
- Pruning plan generation (target token reduction)

## Acceptance Criteria

- Root sets correctly identify essential context
- Reachability analysis finds all referenced segments
- Scoring function produces reasonable prune scores
- Pruning plans meet target token reduction
- Pinned segments are never pruned
- Performance: analysis completes in < 2s for 32k tokens

## Implementation Details

### GC Engine Interface

Implement the `IGCEngine` interface with the following methods:

- `analyze_pruning_candidates(segments: List[ContextSegment], roots: Set[str]) -> List[PruningCandidate]`
- `compute_reachability(roots: Set[str], references: Dict[str, Set[str]]) -> Set[str]`
- `score_segment(segment: ContextSegment, now: datetime) -> float`
- `generate_pruning_plan(candidates: List[PruningCandidate], target_tokens: int) -> PruningPlan`

### Root Set Computation

Identify essential context that should never be pruned:

1. **Current Task Segments**: All segments with `task_id` matching current task
2. **Active File Segments**: Segments with `file_path` matching current active file
3. **Recent Messages**: Last N messages (configurable, default 10)
4. **Pinned Segments**: All segments with `pinned=True`
5. **Recent Decisions**: Segments of type "decision" created in last hour

### Mark-and-Sweep Reachability

Traverse segment references to find all reachable segments:

1. **Mark Phase**: Start from root set, recursively mark all referenced segments
2. **Sweep Phase**: Identify unmarked segments as potential prune candidates
3. **Reference Graph**: Build from segment metadata (references stored in segment.tags or separate reference field)

### Segment Scoring

Compute prune score (lower = more likely to prune):

```python
def score_segment(segment: ContextSegment, now: datetime) -> float:
    # Recency score (older = higher score = more likely to prune)
    age_hours = (now - segment.last_touched_at).total_seconds() / 3600
    recency_score = age_hours / 24.0  # Normalize to days
    
    # Type score (logs/notes = higher score, decisions = lower score)
    type_scores = {
        "log": 1.0,
        "note": 0.8,
        "code": 0.5,
        "message": 0.3,
        "decision": 0.1,
        "summary": 0.2
    }
    type_score = type_scores.get(segment.type, 0.5)
    
    # Reference count (fewer refs = higher score)
    refcount_score = 1.0 / (segment.refcount + 1)
    
    # Generation (old generation = higher score)
    generation_score = 1.0 if segment.generation == "old" else 0.3
    
    # Combine scores (weighted average)
    total_score = (
        0.4 * recency_score +
        0.3 * type_score +
        0.2 * refcount_score +
        0.1 * generation_score
    )
    
    return total_score
```

### Pruning Candidate Identification

1. Compute reachability from roots
2. Score all unreachable segments
3. Sort by score (highest first)
4. Return top candidates

### Pruning Plan Generation

Generate plan to free target tokens:

1. Start with highest-scored candidates
2. Accumulate token counts until target reached
3. Group by action (stash vs delete)
4. Return plan with segment IDs and actions

### Pruning Plan Structure

```python
@dataclass
class PruningPlan:
    candidates: List[PruningCandidate]  # Sorted by score
    total_tokens_freed: int
    stash_segments: List[str]  # segment_ids to stash
    delete_segments: List[str]  # segment_ids to delete
    reason: str  # Explanation of plan
```

## Testing Approach

### Unit Tests

- Test root set computation (various scenarios)
- Test reachability analysis (simple and complex graphs)
- Test scoring function (verify score ranges and ordering)
- Test pruning plan generation (verify token targets met)

### Integration Tests

- Test full GC cycle with realistic context scenarios
- Test with various segment types and ages
- Test pinning behavior (pinned segments never pruned)
- Test reference tracking

### Performance Tests

- Test analysis time for 32k token context (< 2s requirement)
- Test with maximum expected segments (1000+ segments)
- Profile and optimize if needed

### Test Files

- `tests/test_gc_engine.py` - GC engine tests

### Test Scenarios

1. Simple root set (current task only)
2. Complex root set (task + file + messages + pinned)
3. Reachability with circular references
4. Scoring with various segment types and ages
5. Pruning plan generation for different token targets
6. Pinned segments excluded from pruning
7. Performance test with large context

## References

- [Interfaces and Data Models](../design/09_interfaces.md) - GC Engine interface specification
- [Components](../design/04_components.md) - GC Engine component details
- [Design Patterns](../design/06_design_patterns.md) - GC-Inspired Pruning Pattern
- [Architectural Decisions](../design/03_architectural_decisions.md) - Pruning strategy decision
- [GC Heuristic Pruning Design](../../v0/research_outcomes/gc_heuristic_pruning_patterns.md) - Detailed GC patterns

