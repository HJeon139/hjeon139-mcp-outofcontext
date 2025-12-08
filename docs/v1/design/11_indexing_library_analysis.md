# Indexing Library Analysis: Handroll vs. Industry Libraries

**Date:** 2025-12-07  
**Question:** Should we handroll inverted index and indexing patterns or use industry-standard libraries?

---

## Executive Summary

**Recommendation:** **Handroll for MVP, with SQLite FTS as upgrade path**

- **Inverted Index**: Handroll (simple enough, ~100 lines of code)
- **Metadata Indexing**: Already using built-in dict/set (no library needed)
- **Full-Text Search**: Start with handrolled, SQLite FTS as optional enhancement (built-in, no external dependency)

**Rationale:** The indexing needs are simple enough that handrolling maintains the minimal dependency principle while providing sufficient performance. SQLite FTS (built into Python) offers a zero-dependency upgrade path if needed.

---

## Analysis by Pattern

### 1. Inverted Index for Keyword Search

#### Handrolled Approach

**Complexity:** Low (~100-150 lines of code)

**Implementation:**
```python
class InvertedIndex:
    def __init__(self):
        self.index: Dict[str, Set[str]] = {}  # word -> segment_ids
        self.segment_words: Dict[str, Set[str]] = {}  # segment_id -> words
    
    def add_segment(self, segment_id: str, text: str) -> None:
        words = self._tokenize(text)
        for word in words:
            self.index.setdefault(word, set()).add(segment_id)
        self.segment_words[segment_id] = words
    
    def search(self, query: str) -> Set[str]:
        query_words = self._tokenize(query)
        if not query_words:
            return set()
        result = self.index.get(query_words[0], set()).copy()
        for word in query_words[1:]:
            result &= self.index.get(word, set())
        return result
```

**Pros:**
- ✅ Zero dependencies
- ✅ Simple to understand and maintain
- ✅ Full control over behavior
- ✅ Lightweight (~1KB of code)
- ✅ Fast enough for millions of tokens (O(k) where k = query words)

**Cons:**
- ❌ No advanced features (fuzzy matching, stemming, ranking)
- ❌ Must implement tokenization ourselves
- ❌ No built-in optimization

#### Library Options

**Option A: Whoosh (Full-Text Search Library)**

```python
from whoosh import index, fields
from whoosh.qparser import QueryParser

# Setup
schema = fields.Schema(content=fields.TEXT(stored=True), segment_id=fields.ID(stored=True))
ix = index.create_in_memory(schema)

# Indexing
writer = ix.writer()
writer.add_document(content=text, segment_id=seg_id)
writer.commit()

# Searching
with ix.searcher() as searcher:
    query = QueryParser("content", ix.schema).parse("search query")
    results = searcher.search(query)
```

**Pros:**
- ✅ Battle-tested, optimized
- ✅ Advanced features (ranking, fuzzy matching, phrase queries)
- ✅ Good documentation

**Cons:**
- ❌ Additional dependency (~500KB)
- ❌ Overkill for simple keyword search
- ❌ More complex API
- ❌ Conflicts with minimal dependency principle

**Verdict:** ❌ **Too heavy for MVP** - adds dependency for features we don't need yet

---

**Option B: SQLite FTS (Full-Text Search)**

```python
import sqlite3

# Setup (built into Python, no external dependency)
conn = sqlite3.connect(':memory:')
conn.execute('''
    CREATE VIRTUAL TABLE segments_fts USING fts5(
        segment_id, text, content='segments'
    )
''')

# Indexing
conn.execute('INSERT INTO segments_fts(segment_id, text) VALUES (?, ?)', (seg_id, text))

# Searching
cursor = conn.execute('''
    SELECT segment_id FROM segments_fts 
    WHERE segments_fts MATCH ? 
    ORDER BY rank
''', (query,))
```

**Pros:**
- ✅ **Built into Python** (sqlite3 module) - **zero external dependencies**
- ✅ Battle-tested, optimized by SQLite team
- ✅ Advanced features (ranking, phrase matching, boolean operators)
- ✅ Persistent storage built-in
- ✅ Can replace JSON storage if needed

**Cons:**
- ❌ Requires SQLite database (adds complexity)
- ❌ Different storage model (SQL vs. JSON)
- ❌ More setup code

**Verdict:** ✅ **Good upgrade path** - built-in, no external dependency, can migrate to later

---

**Option C: TinyDB with Search**

```python
from tinydb import TinyDB, Query

db = TinyDB('storage.json')
db.insert({'segment_id': seg_id, 'text': text})

# Search
Segment = Query()
results = db.search(Segment.text.search('query'))
```

**Pros:**
- ✅ Simple API
- ✅ JSON-based (fits current design)

**Cons:**
- ❌ Additional dependency
- ❌ Search is still linear (not truly indexed)
- ❌ Not optimized for millions of documents

**Verdict:** ❌ **Not suitable** - doesn't solve the performance problem

---

### 2. Metadata Indexing (File Path, Task ID, Tags)

#### Current Approach (Handrolled)

**Implementation:**
```python
# Already using built-in dict/set
metadata_indexes: Dict[str, Dict[str, Dict[str, Set[str]]]] = {}
# project_id -> {
#   'by_file': {file_path: set(segment_ids)},
#   'by_task': {task_id: set(segment_ids)},
#   'by_tag': {tag: set(segment_ids)}
# }
```

**Pros:**
- ✅ Zero dependencies (built-in Python)
- ✅ O(1) lookups
- ✅ Simple and efficient
- ✅ Already implemented

**Cons:**
- None - this is optimal

**Verdict:** ✅ **Keep as-is** - no library needed

---

### 3. Full-Text Search with Ranking

#### Handrolled Approach

**Complexity:** Medium (would need to add TF-IDF or similar)

**Implementation:**
```python
# Would need to add:
# - Term frequency calculation
# - Document frequency calculation
# - TF-IDF scoring
# - Result ranking
```

**Pros:**
- ✅ Zero dependencies
- ✅ Full control

**Cons:**
- ❌ More code to maintain (~300-500 lines)
- ❌ Must implement ranking algorithm
- ❌ Easy to get wrong

**Verdict:** ⚠️ **Consider SQLite FTS instead** - too much code for marginal benefit

---

## Recommendation Matrix

| Pattern | MVP Approach | Upgrade Path | Rationale |
|---------|-------------|--------------|-----------|
| **Inverted Index** | Handroll | SQLite FTS | Simple enough, ~100 lines |
| **Metadata Indexing** | Built-in dict/set | Keep as-is | Already optimal |
| **Full-Text Search** | Handrolled inverted index | SQLite FTS | Start simple, upgrade if needed |
| **Ranking/Relevance** | Simple (recency + match count) | SQLite FTS ranking | Defer complex ranking |

---

## Implementation Strategy

### Phase 1: MVP (Handrolled)

**Inverted Index:**
- Simple word-to-segment mapping
- Basic tokenization (alphanumeric words)
- Set intersection for multi-word queries
- ~100-150 lines of code

**Metadata Indexing:**
- Continue using dict/set (already optimal)

**Benefits:**
- Zero dependencies
- Simple to understand
- Fast enough for millions of tokens
- Easy to test and debug

### Phase 2: Optional Enhancement (SQLite FTS)

**If handrolled solution proves insufficient:**

1. **Migrate to SQLite FTS:**
   - Built into Python (no external dependency)
   - Better ranking and relevance
   - Advanced query features
   - Can replace JSON storage entirely

2. **Hybrid Approach:**
   - Keep metadata indexes (dict/set) for fast filtering
   - Use SQLite FTS for full-text search
   - Best of both worlds

**Migration Path:**
```python
# Can be added incrementally
class StorageLayer:
    def __init__(self, use_sqlite_fts: bool = False):
        if use_sqlite_fts:
            self.search_backend = SQLiteFTSSearch()
        else:
            self.search_backend = InvertedIndexSearch()
```

---

## Code Complexity Comparison

### Handrolled Inverted Index

**Lines of Code:** ~100-150  
**Dependencies:** 0  
**Maintenance:** Low (simple logic)  
**Performance:** O(k) where k = query words  
**Features:** Basic keyword matching

### SQLite FTS

**Lines of Code:** ~50-100 (setup + queries)  
**Dependencies:** 0 (built-in)  
**Maintenance:** Low (SQLite handles it)  
**Performance:** Optimized by SQLite team  
**Features:** Full-text search, ranking, phrase matching, boolean operators

### Whoosh

**Lines of Code:** ~50-100  
**Dependencies:** 1 (whoosh, ~500KB)  
**Maintenance:** Medium (external library)  
**Performance:** Optimized  
**Features:** Full-text search, ranking, fuzzy matching, advanced queries

---

## Decision Framework Applied

Following the project's dependency minimization principle:

1. **Can we use built-in Python?** 
   - ✅ Metadata indexing: Yes (dict/set)
   - ✅ SQLite FTS: Yes (sqlite3 module)
   - ✅ Inverted index: Simple enough to handroll

2. **Is it a small, focused library?**
   - ⚠️ Whoosh: Medium-sized (~500KB), but adds dependency
   - ✅ SQLite: Built-in, zero external dependency

3. **Is it a large framework/library?**
   - ❌ Elasticsearch: Way too heavy
   - ❌ Whoosh: Medium, but unnecessary for MVP

4. **Does it solve a real problem at our scale?**
   - ✅ Handrolled inverted index: Yes, sufficient for millions of tokens
   - ✅ SQLite FTS: Yes, if we need advanced features later

---

## Final Recommendation

### For MVP: Handroll Inverted Index

**Rationale:**
1. **Simple enough:** ~100 lines of code, straightforward logic
2. **Zero dependencies:** Maintains minimal dependency principle
3. **Fast enough:** O(k) performance meets < 500ms requirement
4. **Easy to maintain:** Simple code is easier to debug and modify
5. **Sufficient features:** Basic keyword matching is enough for MVP

### Upgrade Path: SQLite FTS (Optional)

**When to consider:**
- If handrolled solution has performance issues (unlikely)
- If we need advanced features (ranking, phrase matching, fuzzy search)
- If we want to migrate from JSON to SQLite storage anyway

**Benefits:**
- Built into Python (no external dependency)
- Battle-tested and optimized
- Can replace both JSON storage and search indexing
- Advanced features available if needed

### Avoid: External Libraries (Whoosh, etc.)

**Rationale:**
- Conflicts with minimal dependency principle
- Overkill for MVP needs
- Can always add later if truly needed

---

## Implementation Plan

### Task 06a: Use Handrolled Inverted Index

```python
# Simple, handrolled implementation
class InvertedIndex:
    """Simple inverted index for keyword search."""
    # ~100 lines of code
    # Zero dependencies
    # Fast enough for millions of tokens
```

### Future Enhancement: SQLite FTS Migration

```python
# Optional enhancement (can be added later)
class SQLiteFTSSearch:
    """SQLite FTS-based search (built-in, no external dependency)."""
    # Can replace or complement inverted index
    # Better ranking and advanced features
```

---

## Conclusion

**Handroll the inverted index for MVP** - it's simple enough (~100 lines), maintains zero dependencies, and provides sufficient performance. 

**SQLite FTS is the ideal upgrade path** - built into Python (no external dependency), provides advanced features if needed, and can replace JSON storage entirely.

**Avoid external libraries** - they conflict with the minimal dependency principle and are unnecessary for MVP needs.

This approach balances:
- ✅ Minimal dependencies (core principle)
- ✅ Sufficient performance (meets requirements)
- ✅ Simple implementation (easy to maintain)
- ✅ Upgrade path (SQLite FTS if needed)

---

## References

- [Dependency Minimization](../design/07_constraints_requirements.md) - Project dependency principles
- [Requirements](../v0/requirements.md) - Dependency decision framework
- [Scalability Analysis](10_scalability_analysis.md) - Performance requirements
- [Storage Scalability Enhancements](../tasks/06a_storage_scalability_enhancements.md) - Implementation details

