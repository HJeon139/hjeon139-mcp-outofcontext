# Task 04: Analysis Engine Implementation

## Dependencies

- Task 02: Storage Layer Implementation

## Scope

Implement the analysis engine that provides context usage metrics, health scoring, and recommendations. This includes:

- Implement `IAnalysisEngine` interface from [09_interfaces.md](../design/09_interfaces.md)
- Context usage metrics computation (token counts, segment counts, distribution)
- Health score calculation
- Recommendation generation based on metrics
- Token counting using tiktoken

## Acceptance Criteria

- Metrics accurately reflect context state
- Health scores correlate with usage levels
- Recommendations are actionable and clear
- Token counting is accurate and fast (< 100ms)
- Handles edge cases (empty context, single segment, etc.)

## Implementation Details

### Analysis Engine Interface

Implement the `IAnalysisEngine` interface with the following methods:

- `analyze_context_usage(segments: List[ContextSegment]) -> UsageMetrics`
- `compute_health_score(segments: List[ContextSegment]) -> HealthScore`
- `generate_recommendations(metrics: UsageMetrics) -> List[Recommendation]`

### Token Counting (`src/out_of_context/tokenizer.py`)

Create a wrapper around tiktoken:

```python
class Tokenizer:
    def __init__(self, model: str = "gpt-4"):
        self.encoding = tiktoken.encoding_for_model(model)
    
    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
    
    def count_segment_tokens(self, segment: ContextSegment) -> int:
        # Use cached token count if available, otherwise compute
        if segment.tokens is not None:
            return segment.tokens
        return self.count_tokens(segment.text)
```

### Usage Metrics

Compute comprehensive usage metrics:

```python
@dataclass
class UsageMetrics:
    total_tokens: int
    total_segments: int
    tokens_by_type: Dict[str, int]  # type -> token count
    segments_by_type: Dict[str, int]  # type -> segment count
    tokens_by_task: Dict[str, int]  # task_id -> token count
    oldest_segment_age_hours: float
    newest_segment_age_hours: float
    pinned_segments_count: int
    pinned_tokens: int
    usage_percent: float  # current / limit
    estimated_remaining_tokens: int
```

### Health Score

Compute health score (0-100, higher = healthier):

```python
def compute_health_score(segments: List[ContextSegment], limit: int = 32000) -> HealthScore:
    total_tokens = sum(seg.tokens for seg in segments)
    usage_percent = (total_tokens / limit) * 100
    
    # Base score from usage (lower usage = higher score)
    usage_score = max(0, 100 - usage_percent)
    
    # Penalty for very old segments
    oldest_age_days = max_age_hours(segments) / 24
    age_penalty = min(20, oldest_age_days * 2)  # Max 20 point penalty
    
    # Bonus for good distribution
    distribution_score = compute_distribution_score(segments)
    
    total_score = usage_score - age_penalty + distribution_score
    return HealthScore(
        score=min(100, max(0, total_score)),
        usage_percent=usage_percent,
        factors={
            "usage": usage_score,
            "age_penalty": -age_penalty,
            "distribution": distribution_score
        }
    )
```

### Recommendations

Generate actionable recommendations:

1. **High Usage (>80%)**: "Consider pruning old segments to free space"
2. **Many Old Segments**: "Stash segments older than 24 hours"
3. **Unbalanced Distribution**: "Too many log segments, consider stashing"
4. **Approaching Limit (>90%)**: "Urgent: Prune context immediately"
5. **Healthy (<50%)**: "Context usage is healthy, no action needed"

### Edge Cases

Handle gracefully:

- Empty context (all metrics zero, health score 100)
- Single segment (normal metrics, no distribution issues)
- All segments pinned (recommendation to unpin some)
- All segments same type (distribution warning)

## Testing Approach

### Unit Tests

- Test token counting accuracy (validate against known token counts)
- Test metrics computation (various segment distributions)
- Test health score calculation (various usage levels)
- Test recommendation generation (various scenarios)

### Integration Tests

- Test with realistic context scenarios
- Test edge cases (empty, single segment, all pinned)
- Test performance (token counting < 100ms)

### Test Files

- `tests/test_analysis_engine.py` - Analysis engine tests
- `tests/test_tokenizer.py` - Tokenizer tests

### Test Scenarios

1. Empty context (all zeros, health score 100)
2. Single segment (correct metrics)
3. High usage context (>90%, low health score)
4. Balanced context (good health score)
5. Token counting accuracy (compare with known values)
6. Performance test (token counting < 100ms for 10k tokens)

## References

- [Interfaces and Data Models](../design/09_interfaces.md) - Analysis Engine interface specification
- [Components](../design/04_components.md) - Analysis Engine component details
- [Constraints and Requirements](../design/07_constraints_requirements.md) - Performance requirements
- [tiktoken Documentation](https://github.com/openai/tiktoken) - Token counting library

