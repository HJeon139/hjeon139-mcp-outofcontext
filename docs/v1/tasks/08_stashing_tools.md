# Task 08: Stashing and Retrieval Tools Implementation

## Dependencies

- Task 05: Context Manager Implementation
- Task 06a: Storage Layer Scalability Enhancements (for indexing implementation)

## Scope

Implement MCP tools for stashing context segments and retrieving them. This includes:

- Implement `context_stash` tool
- Implement `context_search_stashed` tool (keyword + metadata)
- Implement `context_retrieve_stashed` tool
- Keyword search implementation (case-insensitive, substring matching)
- Metadata filtering (file path, task ID, tags, time range)

## Acceptance Criteria

- Stashing moves segments to persistent storage
- Keyword search finds relevant segments
- Metadata filters work correctly
- Retrieval returns segments in correct format
- Search performance < 500ms for millions of tokens
- Search handles empty queries and no results gracefully

## Implementation Details

### Tool: `context_stash`

**Purpose:** Move segments from active context to stashed storage.

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
    "stashed_segments": List[str],  # segment_ids
    "tokens_stashed": int,
    "errors": List[str]  # If any segments not found
}
```

**Implementation:**
1. Validate segment IDs exist
2. Move segments to stashed storage via storage layer
3. Update indexes
4. Return results

### Tool: `context_search_stashed`

**Purpose:** Search stashed segments by keyword and metadata filters.

**Parameters:**
```python
{
    "project_id": str,  # Required
    "query": Optional[str],  # Keyword search
    "filters": {
        "file_path": Optional[str],
        "task_id": Optional[str],
        "tags": Optional[List[str]],
        "type": Optional[str],
        "created_after": Optional[str],  # ISO datetime
        "created_before": Optional[str]  # ISO datetime
    },
    "limit": Optional[int] = 50  # Max results
}
```

**Returns:**
```python
{
    "segments": List[ContextSegment],
    "total_matches": int,
    "query": str,
    "filters_applied": Dict
}
```

**Implementation:**
1. Validate parameters
2. Call storage layer search
3. Apply keyword matching
4. Apply metadata filters
5. Sort by relevance/recency
6. Limit results
7. Return matches

### Tool: `context_retrieve_stashed`

**Purpose:** Retrieve specific stashed segments by ID and optionally move back to active.

**Parameters:**
```python
{
    "project_id": str,  # Required
    "segment_ids": List[str],  # Required
    "move_to_active": bool = False  # Move back to active storage
}
```

**Returns:**
```python
{
    "retrieved_segments": List[ContextSegment],
    "moved_to_active": List[str]  # If move_to_active=True
}
```

**Implementation:**
1. Retrieve segments from stashed storage
2. If move_to_active, move segments back
3. Return segments

### Keyword Search Implementation

**Scalability Note:** Keyword search must use inverted index (from Task 06a), not linear search.

**Storage Layer Integration:**

The storage layer (enhanced in Task 06a) provides indexed search:

```python
# Storage layer uses inverted index internally
def search_stashed(self, query: str, filters: Dict, project_id: str) -> List[ContextSegment]:
    """Search using inverted index (not linear search)."""
    # Implementation in Task 06a uses InvertedIndex class
    # This provides O(1) lookup per word instead of O(n) linear scan
    pass
```

**Tool Implementation:**

```python
def context_search_stashed(params: Dict) -> Dict:
    """Search stashed segments using indexed search."""
    # Storage layer handles indexing internally
    # Tool just validates parameters and calls storage
    project_id = params["project_id"]
    query = params.get("query", "")
    filters = params.get("filters", {})
    
    segments = storage_layer.search_stashed(query, filters, project_id)
    return {"segments": segments, "total_matches": len(segments)}
```

**Performance:** With inverted index, search is O(k) where k is number of query words, not O(n) where n is total segments.

### Metadata Filtering

Filter by metadata fields:

```python
def apply_filters(segments: List[ContextSegment], filters: Dict) -> List[ContextSegment]:
    """Apply metadata filters to segments."""
    result = segments
    
    if filters.get("file_path"):
        result = [s for s in result if s.file_path == filters["file_path"]]
    
    if filters.get("task_id"):
        result = [s for s in result if s.task_id == filters["task_id"]]
    
    if filters.get("tags"):
        required_tags = set(filters["tags"])
        result = [s for s in result if required_tags.issubset(set(s.tags))]
    
    if filters.get("type"):
        result = [s for s in result if s.type == filters["type"]]
    
    if filters.get("created_after"):
        after = parse_datetime(filters["created_after"])
        result = [s for s in result if s.created_at >= after]
    
    if filters.get("created_before"):
        before = parse_datetime(filters["created_before"])
        result = [s for s in result if s.created_at <= before]
    
    return result
```

### Search Performance

**Critical:** Search must use indexing to meet < 500ms requirement for millions of tokens.

**Optimization Strategy:**

1. **Inverted Index for Keywords** (from Task 06a):
   - O(1) lookup per word instead of O(n) linear scan
   - Intersection of word sets for multi-word queries
   - Handles millions of segments efficiently

2. **Hash-based Metadata Indexes** (from Task 06a):
   - O(1) lookup for file_path, task_id, tags
   - Set intersection for multiple filters
   - No linear scanning required

3. **Result Limiting:**
   - Limit results to prevent large responses
   - Return top-k most relevant results

4. **Performance Target:**
   - < 500ms for millions of tokens (with indexing)
   - Linear search would take minutes, indexing makes it feasible

### Empty Query Handling

- Empty query returns all stashed segments (up to limit)
- No results returns empty list (not error)
- Invalid filters return error

## Testing Approach

### Unit Tests

- Test keyword search (various queries)
- Test metadata filtering (all filter types)
- Test search performance
- Test empty query handling

### Integration Tests

- Test stashing workflow (stash → search → retrieve)
- Test search with various filters
- Test retrieval and move to active
- Test error cases

### Performance Tests

- Test search performance (< 500ms for millions of tokens)
- Test with maximum expected segments
- Profile and optimize if needed

### Test Files

- `tests/test_tools_stashing.py` - Stashing tools tests
- `tests/test_search.py` - Search implementation tests

### Test Scenarios

1. Stash segments and verify persistence
2. Search by keyword (exact and partial matches)
3. Search by metadata filters (file, task, tag, time)
4. Combine keyword and metadata filters
5. Retrieve stashed segments
6. Move stashed segments back to active
7. Test empty query (returns all)
8. Test no results (empty list)
9. Performance test (search < 500ms)

## References

- [Integration Patterns](../design/05_integration_patterns.md) - Tool interface patterns
- [Components](../design/04_components.md) - Storage Layer component
- [Architectural Decisions](../design/03_architectural_decisions.md) - Retrieval strategy decision
- [Constraints and Requirements](../design/07_constraints_requirements.md) - Performance requirements
- [Scalability Analysis](../design/10_scalability_analysis.md) - Search performance issues
- [Storage Scalability Enhancements](06a_storage_scalability_enhancements.md) - Indexing implementation

