# Task 06a: Storage Layer Scalability Enhancements

## Dependencies

- Task 02: Storage Layer Implementation (already completed)
- Task 04: Analysis Engine Implementation (already completed)

## Scope

Enhance the storage layer to support millions of tokens efficiently. This addresses critical scalability issues identified in [Scalability Analysis](../design/10_scalability_analysis.md). This includes:

- Implement token count caching in segment metadata
- Add comprehensive indexing (inverted index for keywords, hash maps for metadata)
- Implement JSON file sharding (split by project/date)
- Add incremental save operations
- Implement memory management (LRU eviction for active segments)

## Acceptance Criteria

- Token counts are cached and only recomputed when text changes
- Keyword search uses inverted index (not linear search)
- Metadata filtering uses hash-based indexes
- Stashed segments stored in sharded JSON files
- Active segments use LRU eviction to manage memory
- Search performance < 500ms for millions of tokens
- Storage operations remain non-blocking

## Implementation Details

### 1. Token Count Caching

**Problem:** Token counting for millions of tokens violates < 100ms requirement.

**Solution:** Cache token counts in segment metadata.

**Implementation:**

```python
# Update ContextSegment model to include cached tokens
class ContextSegment(BaseModel):
    segment_id: str
    text: str
    tokens: Optional[int] = None  # Cached token count
    tokens_computed_at: Optional[datetime] = None
    # ... other fields

# Update tokenizer to use cache
class Tokenizer:
    def count_segment_tokens(self, segment: ContextSegment, force_recompute: bool = False) -> int:
        """Count tokens, using cache if available."""
        if segment.tokens is not None and not force_recompute:
            # Check if text has changed (simple hash check)
            if segment.tokens_computed_at and not self._text_changed(segment):
                return segment.tokens
        
        # Compute and cache
        count = len(self.encoding.encode(segment.text))
        segment.tokens = count
        segment.tokens_computed_at = datetime.now()
        return count
    
    def _text_changed(self, segment: ContextSegment) -> bool:
        """Check if segment text has changed since last count."""
        # Simple implementation: store text hash
        # If hash changed, text changed
        pass
```

**Update Analysis Engine:**
- Use cached token counts from segments
- Only recompute when segment text changes
- Batch token counting for new segments

### 2. Inverted Index for Keyword Search

**Problem:** Linear search is O(n) and too slow for millions of tokens.

**Solution:** Implement handrolled inverted index for keyword search.

**Decision:** Handroll the inverted index (not use external library) to maintain minimal dependency principle. See [Indexing Library Analysis](../design/11_indexing_library_analysis.md) for rationale.

**Implementation:**

```python
class InvertedIndex:
    """Inverted index for keyword search."""
    
    def __init__(self):
        # word -> set of segment_ids containing that word
        self.index: Dict[str, Set[str]] = {}
        # segment_id -> set of words in that segment
        self.segment_words: Dict[str, Set[str]] = {}
    
    def add_segment(self, segment_id: str, text: str) -> None:
        """Add segment to index."""
        words = self._tokenize(text)
        self.segment_words[segment_id] = words
        
        for word in words:
            if word not in self.index:
                self.index[word] = set()
            self.index[word].add(segment_id)
    
    def remove_segment(self, segment_id: str) -> None:
        """Remove segment from index."""
        if segment_id not in self.segment_words:
            return
        
        words = self.segment_words[segment_id]
        for word in words:
            if word in self.index:
                self.index[word].discard(segment_id)
                if not self.index[word]:
                    del self.index[word]
        
        del self.segment_words[segment_id]
    
    def search(self, query: str) -> Set[str]:
        """Search for segments containing query words."""
        query_words = self._tokenize(query)
        if not query_words:
            return set()
        
        # Intersection of all word sets (AND search)
        result = self.index.get(query_words[0], set()).copy()
        for word in query_words[1:]:
            result &= self.index.get(word, set())
        
        return result
    
    def _tokenize(self, text: str) -> Set[str]:
        """Tokenize text into words (lowercase, alphanumeric)."""
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        return set(words)
```

**Integration with Storage Layer:**

```python
class StorageLayer:
    def __init__(self, storage_path: str):
        # ... existing initialization
        self.keyword_index: Dict[str, InvertedIndex] = {}  # project_id -> index
        self._init_indexes()
    
    def stash_segment(self, segment: ContextSegment, project_id: str) -> None:
        """Stash segment and update indexes."""
        # ... existing stash logic
        # Update keyword index
        if project_id not in self.keyword_index:
            self.keyword_index[project_id] = InvertedIndex()
        self.keyword_index[project_id].add_segment(segment.segment_id, segment.text)
    
    def search_stashed(self, query: str, filters: Dict, project_id: str) -> List[ContextSegment]:
        """Search using inverted index."""
        # Use index for keyword search
        if query and project_id in self.keyword_index:
            candidate_ids = self.keyword_index[project_id].search(query)
        else:
            # No query or no index: get all stashed segment IDs
            candidate_ids = set(self._get_all_stashed_ids(project_id))
        
        # Apply metadata filters using hash maps
        if 'file_path' in filters:
            candidate_ids &= self.metadata_indexes[project_id]['by_file'].get(
                filters['file_path'], set()
            )
        # ... apply other filters
        
        # Load only matching segments
        return [self._load_stashed_segment(seg_id, project_id) for seg_id in candidate_ids]
```

### 3. Metadata Indexing Enhancement

**Problem:** Metadata filtering uses linear search.

**Solution:** Enhance existing metadata indexes to use sets for O(1) lookups.

**Implementation:**

```python
class StorageLayer:
    def __init__(self, storage_path: str):
        # ... existing initialization
        # Enhanced metadata indexes (use sets instead of lists)
        self.metadata_indexes: Dict[str, Dict[str, Dict[str, Set[str]]]] = {}
        # project_id -> {
        #   'by_file': {file_path: set(segment_ids)},
        #   'by_task': {task_id: set(segment_ids)},
        #   'by_tag': {tag: set(segment_ids)},
        #   'by_type': {type: set(segment_ids)}
        # }
    
    def _update_metadata_indexes(self, segment: ContextSegment, project_id: str, add: bool = True):
        """Update metadata indexes for a segment."""
        if project_id not in self.metadata_indexes:
            self.metadata_indexes[project_id] = {
                'by_file': {},
                'by_task': {},
                'by_tag': {},
                'by_type': {}
            }
        
        indexes = self.metadata_indexes[project_id]
        op = indexes['by_file'].setdefault if add else indexes['by_file'].get
        
        # Update file_path index
        if segment.file_path:
            if add:
                indexes['by_file'].setdefault(segment.file_path, set()).add(segment.segment_id)
            else:
                indexes['by_file'].get(segment.file_path, set()).discard(segment.segment_id)
        
        # Update task_id index
        if segment.task_id:
            if add:
                indexes['by_task'].setdefault(segment.task_id, set()).add(segment.segment_id)
            else:
                indexes['by_task'].get(segment.task_id, set()).discard(segment.segment_id)
        
        # Update tags index
        for tag in segment.tags:
            if add:
                indexes['by_tag'].setdefault(tag, set()).add(segment.segment_id)
            else:
                indexes['by_tag'].get(tag, set()).discard(segment.segment_id)
        
        # Update type index
        if add:
            indexes['by_type'].setdefault(segment.type, set()).add(segment.segment_id)
        else:
            indexes['by_type'].get(segment.type, set()).discard(segment.segment_id)
```

### 4. JSON File Sharding

**Problem:** Single JSON file becomes unwieldy at millions of tokens.

**Solution:** Shard stashed segments into multiple files.

**Implementation:**

```python
class StorageLayer:
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        # Sharded storage: one file per project
        # Format: storage_path / "stashed" / f"{project_id}.json"
        self.stashed_dir = self.storage_path / "stashed"
        self.stashed_dir.mkdir(exist_ok=True)
    
    def _get_stashed_file_path(self, project_id: str) -> Path:
        """Get file path for project's stashed segments."""
        return self.stashed_dir / f"{project_id}.json"
    
    def stash_segment(self, segment: ContextSegment, project_id: str) -> None:
        """Stash segment to project-specific file."""
        file_path = self._get_stashed_file_path(project_id)
        
        # Load existing stashed segments
        stashed = self._load_stashed_file(file_path)
        
        # Add new segment
        stashed.append(segment.dict())
        
        # Save (incremental save - append or rewrite)
        self._save_stashed_file(file_path, stashed)
        
        # Update indexes
        self._update_indexes(segment, project_id, add=True)
    
    def _load_stashed_file(self, file_path: Path) -> List[Dict]:
        """Load stashed segments from file."""
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data.get('segments', [])
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading stashed file {file_path}: {e}")
            return []
    
    def _save_stashed_file(self, file_path: Path, segments: List[Dict]) -> None:
        """Save stashed segments to file (atomic write)."""
        # Atomic write pattern
        temp_path = file_path.with_suffix('.json.tmp')
        
        try:
            with open(temp_path, 'w') as f:
                json.dump({'segments': segments}, f, indent=2)
            temp_path.replace(file_path)  # Atomic rename
        except IOError as e:
            logger.error(f"Error saving stashed file {file_path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise
```

**Alternative: Date-based sharding (optional enhancement):**

```python
def _get_stashed_file_path(self, project_id: str, date: Optional[datetime] = None) -> Path:
    """Get file path with optional date-based sharding."""
    if date is None:
        date = datetime.now()
    
    # Shard by month: project_id_YYYY-MM.json
    date_str = date.strftime('%Y-%m')
    return self.stashed_dir / f"{project_id}_{date_str}.json"
```

### 5. Memory Management (LRU Eviction)

**Problem:** All active segments in memory may exceed memory limits.

**Solution:** Implement LRU cache with eviction to disk.

**Implementation:**

```python
from collections import OrderedDict
from typing import Optional

class LRUSegmentCache:
    """LRU cache for active segments with disk eviction."""
    
    def __init__(self, maxsize: int = 10000, storage: 'StorageLayer' = None):
        self.maxsize = maxsize
        self.storage = storage
        self.cache: OrderedDict[str, ContextSegment] = OrderedDict()
        self.evicted_to_disk: Set[str] = set()  # Track evicted segments
    
    def get(self, segment_id: str) -> Optional[ContextSegment]:
        """Get segment, loading from disk if evicted."""
        if segment_id in self.cache:
            # Move to end (most recently used)
            segment = self.cache.pop(segment_id)
            self.cache[segment_id] = segment
            return segment
        
        # Check if evicted to disk
        if segment_id in self.evicted_to_disk:
            # Load from disk
            segment = self.storage._load_evicted_segment(segment_id)
            if segment:
                self.put(segment_id, segment)
                return segment
        
        return None
    
    def put(self, segment_id: str, segment: ContextSegment) -> None:
        """Add segment, evicting LRU if needed."""
        if segment_id in self.cache:
            # Update existing
            self.cache.move_to_end(segment_id)
            self.cache[segment_id] = segment
            return
        
        # Add new segment
        if len(self.cache) >= self.maxsize:
            # Evict LRU
            evicted_id, evicted_segment = self.cache.popitem(last=False)
            self._evict_to_disk(evicted_id, evicted_segment)
        
        self.cache[segment_id] = segment
        self.evicted_to_disk.discard(segment_id)
    
    def _evict_to_disk(self, segment_id: str, segment: ContextSegment) -> None:
        """Evict segment to disk storage."""
        if self.storage:
            self.storage._save_evicted_segment(segment_id, segment)
            self.evicted_to_disk.add(segment_id)
```

**Integration with Storage Layer:**

```python
class StorageLayer:
    def __init__(self, storage_path: str, max_active_segments: int = 10000):
        # ... existing initialization
        # Use LRU cache for active segments
        self.active_segments: LRUSegmentCache = LRUSegmentCache(
            maxsize=max_active_segments,
            storage=self
        )
```

### 6. Incremental Save Operations

**Problem:** Rewriting entire JSON file on every stash is slow.

**Solution:** Implement append-only log with periodic compaction.

**Implementation (optional enhancement):**

```python
class StorageLayer:
    def stash_segment(self, segment: ContextSegment, project_id: str) -> None:
        """Stash segment using append-only log."""
        log_file = self._get_stash_log_path(project_id)
        
        # Append to log file (fast)
        with open(log_file, 'a') as f:
            json.dump(segment.dict(), f)
            f.write('\n')  # Newline-delimited JSON
        
        # Update indexes
        self._update_indexes(segment, project_id, add=True)
        
        # Periodic compaction (every N segments or time-based)
        if self._should_compact(project_id):
            self._compact_stash_log(project_id)
    
    def _should_compact(self, project_id: str) -> bool:
        """Check if compaction is needed."""
        # Compact if log file > 100MB or every 1000 segments
        log_file = self._get_stash_log_path(project_id)
        if log_file.exists():
            size_mb = log_file.stat().st_size / (1024 * 1024)
            return size_mb > 100
        return False
    
    def _compact_stash_log(self, project_id: str) -> None:
        """Compact append-only log into single JSON file."""
        # Read all segments from log
        # Write to single JSON file
        # Clear log file
        pass
```

## Testing Approach

### Unit Tests

- Test token count caching (cache hit/miss, invalidation)
- Test inverted index (add, remove, search)
- Test metadata indexes (filtering performance)
- Test file sharding (multiple projects, file isolation)
- Test LRU eviction (eviction order, disk loading)

### Integration Tests

- Test search performance with indexing (< 500ms for 1M segments)
- Test token counting performance with caching (< 100ms)
- Test file sharding across multiple projects
- Test memory management (eviction triggers, disk loading)

### Performance Tests

```python
@pytest.mark.performance
def test_search_with_indexing():
    """Test search performance with inverted index."""
    # Create 1M segments
    segments = create_test_segments(count=1000000)
    storage = StorageLayer("/tmp/test")
    
    # Index all segments
    for seg in segments:
        storage.stash_segment(seg, "test_project")
    
    # Search should be fast
    start = time.time()
    results = storage.search_stashed("test query", {}, "test_project")
    duration = time.time() - start
    
    assert duration < 0.5  # < 500ms
    assert len(results) > 0

@pytest.mark.performance
def test_token_counting_with_cache():
    """Test token counting uses cache."""
    segment = ContextSegment(segment_id="1", text="test " * 1000)
    
    tokenizer = Tokenizer()
    
    # First count (no cache)
    start = time.time()
    count1 = tokenizer.count_segment_tokens(segment)
    duration1 = time.time() - start
    
    # Second count (cached)
    start = time.time()
    count2 = tokenizer.count_segment_tokens(segment)
    duration2 = time.time() - start
    
    assert count1 == count2
    assert duration2 < duration1  # Cached should be faster
    assert duration2 < 0.001  # Cache lookup should be < 1ms
```

### Test Files

- `tests/test_storage_scalability.py` - Scalability enhancements tests
- `tests/test_indexing.py` - Indexing implementation tests
- `tests/test_token_caching.py` - Token caching tests

## Migration Strategy

### Backward Compatibility

- Existing single JSON file format should still work
- Add migration script to convert single file to sharded format
- Indexes can be rebuilt from existing data on first load

### Gradual Rollout

1. **Phase 1:** Add token caching (non-breaking)
2. **Phase 2:** Add indexing (backward compatible, can disable)
3. **Phase 3:** Add file sharding (migration script)
4. **Phase 4:** Add LRU eviction (configurable)

## Upgrade Path: SQLite FTS (Optional)

**Future Enhancement:** If handrolled inverted index proves insufficient, SQLite FTS (built into Python) provides a zero-dependency upgrade path with advanced features (ranking, phrase matching, boolean operators).

**When to Consider:**
- If handrolled solution has performance issues (unlikely)
- If advanced features needed (ranking, fuzzy search)
- If migrating from JSON to SQLite storage anyway

See [Indexing Library Analysis](../design/11_indexing_library_analysis.md) for detailed comparison.

## References

- [Scalability Analysis](../design/10_scalability_analysis.md) - Critical issues and recommendations
- [Storage Layer Task](02_storage_layer.md) - Original storage implementation
- [Architectural Decisions](../design/03_architectural_decisions.md) - Storage strategy
- [Indexing Library Analysis](../design/11_indexing_library_analysis.md) - Handroll vs. library decision

