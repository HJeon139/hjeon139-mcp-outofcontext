# Scalability Analysis: Millions of Tokens

This document analyzes the current architecture for potential scalability issues when operating at millions of tokens instead of 32k-64k tokens.

**Date:** 2025-12-07 
**Scale Target:** Millions of tokens (previously 32k-64k)  
**Status:** Critical Issues Identified

---

## Executive Summary

The architecture was originally designed for 32k-64k token volumes. Scaling to millions of tokens reveals several critical bottlenecks:

1. **Critical Issues** (must address):
   - Linear search algorithms will be too slow
   - In-memory storage of all segments may exceed memory limits
   - Single JSON file persistence will be unwieldy
   - Token counting at scale may violate performance requirements

2. **Moderate Issues** (should address):
   - GC sweep phase sorting may be slow
   - No indexing for metadata filtering
   - JSON serialization/deserialization overhead

3. **Minor Issues** (can optimize later):
   - Reference graph traversal (mark phase) should be fine
   - Working set management should scale

---

## Critical Issues

### 1. Linear Search Performance

**Problem:**
The design explicitly uses linear search (O(n)) for keyword matching:

```python
# From requirements.md
def search_stashed(query: str) -> List[ContextSegment]:
    return [seg for seg in stashed_context.values() 
            if query.lower() in seg.text.lower() 
            or matches_metadata(seg, filters)]
```

**Impact:**
- With millions of tokens, this could mean scanning hundreds of thousands or millions of segments
- Performance requirement: "< 500ms for millions of tokens" is likely **unachievable** with linear search
- Example: 1M segments × 1ms per segment = 1000 seconds (16+ minutes)

**Recommendation:**
- **Immediate**: Add basic indexing (inverted index for keywords, hash maps for metadata)
- **Short-term**: Consider SQLite with FTS (Full-Text Search) for stashed context
- **Long-term**: Vector DB for semantic search (already deferred, but may become necessary)

**Migration Path:**
- Keep in-memory dict for active segments (smaller set)
- Use indexed storage for stashed segments
- Add incremental indexing as segments are stashed

---

### 2. In-Memory Storage Limits

**Problem:**
All active segments stored in memory as `Dict[str, ContextSegment]`:

```python
# From components.md
segments: dict[str, ContextSegment] = {}
```

**Impact:**
- Millions of tokens could mean:
  - 1M tokens ≈ 750KB text (rough estimate)
  - 10M tokens ≈ 7.5MB text
  - 100M tokens ≈ 75MB text
- With metadata overhead, could easily reach 100MB+ in memory
- May cause memory pressure, especially with multiple projects

**Recommendation:**
- **Immediate**: Implement segment eviction to disk when inactive
- **Short-term**: Use lazy loading - only load segments when accessed
- **Consider**: Hybrid approach - hot segments in memory, cold segments on disk

**Migration Path:**
- Add LRU cache for active segments
- Implement disk-backed storage for cold segments
- Monitor memory usage and add limits

---

### 3. Single JSON File Persistence

**Problem:**
All stashed segments stored in a single JSON file:

```python
# From requirements.md
# Structure:
# {
#   "segments": [
#     {
#       "segment_id": "...",
#       "text": "...",
#       "metadata": {...},
#       "timestamp": "..."
#     }
#   ]
# }
```

**Impact:**
- Loading/saving entire file on every stash operation will be slow
- File size could grow to hundreds of MB or GB
- JSON parsing/serialization overhead increases linearly
- Risk of data loss if file corruption occurs
- No incremental updates - must rewrite entire file

**Recommendation:**
- **Immediate**: Split into multiple files (by project, by date, or sharded)
- **Short-term**: Use append-only log format with periodic compaction
- **Long-term**: Migrate to SQLite or similar database

**Migration Path:**
- Implement file sharding (e.g., one file per project or per 100k segments)
- Add incremental save operations
- Design JSON structure to support migration to SQLite

---

### 4. Token Counting Performance

**Problem:**
Token counting using tiktoken for all segments:

```python
# From analysis_engine.md
def count_tokens(self, text: str) -> int:
    return len(self.encoding.encode(text))
```

**Impact:**
- Performance requirement: "< 100ms for typical context"
- With millions of tokens, counting all segments could take seconds
- Analysis operations require counting all segments
- No caching mentioned in design

**Recommendation:**
- **Immediate**: Cache token counts in segment metadata
- **Short-term**: Incremental counting - only count new/changed segments
- **Consider**: Batch token counting with tiktoken (if supported)

**Migration Path:**
- Add `tokens` field to `ContextSegment` model
- Cache counts on segment creation/update
- Only recompute when segment text changes

---

## Moderate Issues

### 5. GC Sweep Phase Sorting

**Problem:**
Sweep phase sorts all candidate segments:

```python
# From gc_heuristic_pruning_patterns.md
# Steps:
# 1. Build candidate list of non-root, non-pinned segments.
# 2. Sort by score (lowest first).
```

**Impact:**
- Sorting millions of segments is O(n log n)
- Could take several seconds for large context
- Performance requirement: "< 2s for millions of token contexts" may be tight

**Recommendation:**
- **Immediate**: Use partial sort (heap) to get top-k candidates only
- **Short-term**: Incremental GC - only sort recently changed segments
- **Consider**: Approximate sorting or sampling for very large sets

**Migration Path:**
- Replace full sort with heap-based top-k selection
- Implement incremental scoring updates
- Add batching for large candidate sets

---

### 6. No Indexing for Metadata Filtering

**Problem:**
Metadata filtering uses linear search:

```python
# From architectural_decisions.md
# Metadata Filters: File path, task ID, tags, time range, segment type
# Combined Scoring: Keyword matches + metadata relevance + recency
# Linear Search: Acceptable performance for stashed context volumes
```

**Impact:**
- Filtering by file path, task ID, tags requires scanning all segments
- Multiple filters compound the problem
- No mention of indexes in storage design

**Recommendation:**
- **Immediate**: Add hash-based indexes for common filters (file_path, task_id, tags)
- **Short-term**: Use SQLite indexes if migrating to database
- **Consider**: Composite indexes for common filter combinations

**Migration Path:**
- Add `Dict[str, Set[str]]` indexes (e.g., `by_file_path: Dict[str, Set[str]]`)
- Update indexes incrementally on segment changes
- Design to support SQLite migration

---

### 7. JSON Serialization Overhead

**Problem:**
JSON serialization/deserialization for large datasets:

**Impact:**
- JSON parsing is CPU-intensive for large files
- Memory usage doubles during load (original + parsed)
- No streaming support mentioned

**Recommendation:**
- **Immediate**: Use streaming JSON parser (ijson) for large files
- **Short-term**: Consider binary formats (MessagePack, Protocol Buffers)
- **Long-term**: Database eliminates this issue

**Migration Path:**
- Add streaming JSON loader
- Keep JSON for compatibility, add binary format option
- Design serialization layer to abstract format

---

## Minor Issues

### 8. Reference Graph Traversal (Mark Phase)

**Status:** Should be fine

**Analysis:**
- Mark phase uses DFS/BFS which is O(V + E)
- With millions of segments, graph may be sparse (few references per segment)
- Should complete in < 1s even for large graphs

**Recommendation:**
- Monitor performance in practice
- Consider iterative deepening if needed
- Add cycle detection if references can be circular

---

### 9. Working Set Management

**Status:** Should be fine

**Analysis:**
- Working sets are small subsets of total context
- Only includes recent messages, active files, pinned segments
- Should remain manageable even at scale

**Recommendation:**
- Monitor working set sizes
- Add limits if needed (e.g., max 10k segments per working set)

---

## Performance Requirements Re-evaluation

Current requirements may be unrealistic at millions of tokens:

| Requirement | Current Target | Feasibility at Millions of Tokens |
|------------|---------------|-----------------------------------|
| Context analysis | < 2s | **Questionable** - depends on segment count |
| Token counting | < 100ms | **Unrealistic** - needs caching |
| Keyword search | < 500ms | **Unrealistic** - needs indexing |
| Storage operations | Non-blocking | **Achievable** - with async I/O |

**Recommendation:**
- Re-evaluate performance targets based on actual segment counts, not just token counts
- Consider per-segment limits (e.g., max 100k segments per project)
- Add performance monitoring and adjust targets based on real-world data

---

## Recommended Immediate Actions

### Priority 1 (Critical - Block MVP at Scale)

1. **Add Token Count Caching**
   - Store token counts in segment metadata
   - Only recompute when text changes
   - Update analysis engine to use cached counts

2. **Implement Basic Indexing**
   - Inverted index for keywords (for stashed segments)
   - Hash maps for metadata filters (file_path, task_id, tags)
   - Update indexes incrementally

3. **Split JSON Storage**
   - Shard stashed segments into multiple files
   - One file per project or per date range
   - Implement incremental saves

### Priority 2 (Important - Performance)

4. **Optimize GC Sweep**
   - Use heap-based top-k selection instead of full sort
   - Implement incremental scoring

5. **Add Memory Management**
   - Implement LRU eviction for active segments
   - Lazy loading for cold segments
   - Memory usage monitoring

### Priority 3 (Nice to Have)

6. **Streaming JSON Parser**
   - Use ijson for large file loading
   - Reduce memory footprint during startup

7. **Performance Monitoring**
   - Add metrics for operation times
   - Track segment counts and memory usage
   - Alert on performance degradation

---

## Architecture Modifications Needed

### Storage Layer Changes

**Current:**
```python
# Single in-memory dict
segments: dict[str, ContextSegment] = {}
# Single JSON file
stashed_segments: List[ContextSegment] = []
```

**Recommended:**
```python
# In-memory with eviction
active_segments: LRUCache[str, ContextSegment] = LRUCache(maxsize=10000)
# Indexed storage for stashed
stashed_index: InvertedIndex = InvertedIndex()
stashed_by_file: dict[str, set[str]] = {}
stashed_by_task: dict[str, set[str]] = {}
# Sharded JSON files
stashed_files: dict[str, Path] = {}  # project_id -> file path
```

### Search Implementation Changes

**Current:**
```python
# Linear search
def search_stashed(query: str) -> List[ContextSegment]:
    return [seg for seg in stashed_context.values() 
            if query.lower() in seg.text.lower()]
```

**Recommended:**
```python
# Indexed search
def search_stashed(query: str, filters: Dict) -> List[ContextSegment]:
    # Use inverted index for keywords
    candidate_ids = stashed_index.search(query)
    # Apply metadata filters using hash maps
    if 'file_path' in filters:
        candidate_ids &= stashed_by_file.get(filters['file_path'], set())
    # Load only matching segments
    return [load_segment(id) for id in candidate_ids]
```

---

## Migration Strategy

### Phase 1: Immediate Fixes (Before MVP)
- Add token count caching
- Implement basic keyword indexing for stashed segments
- Split JSON files by project

### Phase 2: Performance Optimization (Post-MVP)
- Optimize GC sweep with heap-based selection
- Add memory management and eviction
- Implement streaming JSON loading

### Phase 3: Scale Preparation (v2)
- Migrate to SQLite for stashed context
- Add vector DB for semantic search (if needed)
- Implement distributed storage (if multi-server)

---

## Testing at Scale

**Recommendation:** Add performance tests with realistic data:

```python
@pytest.mark.performance
def test_search_at_scale():
    """Test search performance with 1M segments."""
    segments = create_test_segments(count=1000000, tokens_per_segment=10)
    # Should complete in < 500ms with indexing
    results = search_stashed("test query")
    assert len(results) > 0

@pytest.mark.performance  
def test_gc_analysis_at_scale():
    """Test GC analysis with 1M segments."""
    segments = create_test_segments(count=1000000)
    # Should complete in < 2s with optimizations
    candidates = gc_engine.analyze_pruning_candidates(segments)
    assert len(candidates) > 0
```

---

## References

- [Architectural Decisions](03_architectural_decisions.md) - Original decisions made for smaller scale
- [Constraints and Requirements](07_constraints_requirements.md) - Performance requirements
- [GC Heuristic Pruning Design](../../v0/research_outcomes/gc_heuristic_pruning_patterns.md) - GC algorithm details
- [Storage Strategy](03_architectural_decisions.md#decision-area-2-storage-strategy) - Storage decisions

---

## Conclusion

The architecture needs **significant modifications** to operate efficiently at millions of tokens. The most critical issues are:

1. **Linear search must be replaced with indexing**
2. **In-memory storage needs eviction/lazy loading**
3. **Single JSON file must be sharded**
4. **Token counting must be cached**

These changes are feasible and can be implemented incrementally without major architectural refactoring. The design's modularity supports these enhancements.

**Recommendation:** Address Priority 1 issues before attempting to operate at millions of tokens. The current design will not meet performance requirements without these modifications.

