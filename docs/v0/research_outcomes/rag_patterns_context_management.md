# Design: RAG Patterns for Context Management

## 1. Scope & Goals

### What This Design Covers

This design document outlines how Retrieval-Augmented Generation (RAG) patterns are applied to the Context Management MCP Server for storing, indexing, and retrieving stashed context segments. It covers the embedding generation, vector storage, semantic search, and retrieval strategies that enable agents to access previously archived context when needed.

### Non-Goals

- Not designing the pruning/stashing logic (covered in pruning strategy documents)
- Not designing the platform integration (covered in architecture_platform_integration.md)
- Not designing the embedding model training (we use pre-trained models)

## 2. RAG Pattern Overview

### Traditional RAG Pattern

**Standard RAG**:
```
1. Ingest documents → Generate embeddings → Store in vector DB
2. User query → Generate query embedding → Search vector DB
3. Retrieve top-K relevant documents → Augment prompt → Generate response
```

### RAG for Context Management

**Context Management RAG**:
```
1. Prune context segments → Generate embeddings → Store in vector DB
2. Agent needs context → Generate query embedding → Search vector DB
3. Retrieve relevant stashed segments → Merge back into active context
```

**Key Differences**:
- **Document source**: Context segments (messages, code, logs) instead of external documents
- **Storage purpose**: Temporary stashing for later retrieval, not permanent knowledge base
- **Retrieval goal**: Restore context continuity, not answer questions
- **Lifecycle**: Context segments may be temporary (expire, delete) vs. permanent docs

## 3. Architecture Overview

### RAG Components in Context Management

```
┌─────────────────────────────────────────────────────────────┐
│                    Context Pruning/Stashing                  │
│  - Identify context segments to stash                       │
│  - Extract text content from segments                       │
│  - Generate embeddings                                       │
│  - Store in vector DB with metadata                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Embeddings + Metadata
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    Vector Database Layer                     │
│  - FAISS / Qdrant / Chroma                                  │
│  - Index: segment_id → embedding                            │
│  - Metadata: timestamp, type, tokens, topic                 │
│  - Query interface: semantic search + filters               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Query + Retrieve
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  Context Retrieval Layer                     │
│  - Generate query embedding from current task                │
│  - Search for relevant stashed segments                     │
│  - Rank and filter results                                  │
│  - Return top-K relevant segments                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Retrieved Segments
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  Context Merging Layer                       │
│  - Merge retrieved segments into active context             │
│  - Handle duplicates and conflicts                          │
│  - Update context at platform level                         │
└─────────────────────────────────────────────────────────────┘
```

## 4. Context Segment Representation

### Segment Data Model

```python
@dataclass
class ContextSegment:
    """Represents a stashed context segment"""
    
    # Identity
    segment_id: str  # Unique identifier
    session_id: str  # Parent session identifier
    
    # Content
    text: str  # The actual text content
    type: SegmentType  # message, code_block, file_content, log, etc.
    
    # Metadata
    timestamp: datetime  # When segment was created
    stashed_at: datetime  # When segment was stashed
    tokens: int  # Token count
    topic: Optional[str]  # Topic/tag for filtering
    source: str  # Original source (file path, message ID, etc.)
    
    # Relationships
    references: List[str]  # IDs of referenced segments
    referenced_by: List[str]  # IDs that reference this segment
    
    # Embedding
    embedding: Optional[np.ndarray]  # Vector embedding (384 or 768 dim)
    embedding_model: str  # Model used to generate embedding
    
    # Lifecycle
    expires_at: Optional[datetime]  # Optional expiration
    protected: bool = False  # Protected from deletion
```

### Segment Types

```python
class SegmentType(Enum):
    MESSAGE = "message"  # Conversation messages
    CODE_BLOCK = "code_block"  # Code snippets
    FILE_CONTENT = "file_content"  # Full or partial file contents
    ERROR_LOG = "error_log"  # Error messages, stack traces
    DEBUG_OUTPUT = "debug_output"  # Debug output, logs
    TASK_STATE = "task_state"  # Current task/goal state
    DECISION = "decision"  # Decisions made, rationale
    RESEARCH = "research"  # Research findings, notes
```

## 5. Embedding Generation

### Embedding Strategy

**Model Selection** (from research findings):

1. **Primary: all-MiniLM-L6-v2** (sentence-transformers)
   - 384-dimensional vectors
   - Fast inference (~50ms per segment)
   - Good for general semantic similarity
   - Size: ~80MB

2. **Alternative: all-mpnet-base-v2** (sentence-transformers)
   - 768-dimensional vectors
   - Higher quality, slower inference
   - Better for nuanced semantic matching
   - Size: ~420MB

3. **Cloud: OpenAI text-embedding-3-small**
   - 1536-dimensional vectors
   - Excellent quality
   - API costs, network latency
   - Use for production if budget allows

**Recommendation**: Start with `all-MiniLM-L6-v2` for speed, upgrade to `all-mpnet-base-v2` if quality is insufficient.

### Embedding Generation Pipeline

```python
class EmbeddingGenerator:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a text segment"""
        # Normalize text
        normalized = self._normalize_text(text)
        
        # Generate embedding
        embedding = self.model.encode(
            normalized,
            normalize_embeddings=True,  # L2 normalization for cosine similarity
            show_progress_bar=False
        )
        
        return embedding
    
    def batch_generate(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts (more efficient)"""
        normalized = [self._normalize_text(t) for t in texts]
        embeddings = self.model.encode(
            normalized,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False
        )
        return embeddings
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for embedding generation"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Truncate if too long (model limits)
        max_length = 512  # tokens, approximate
        if len(text) > max_length * 4:  # rough char estimate
            text = text[:max_length * 4] + "..."
        return text.strip()
```

### Chunking Strategy

For long context segments (e.g., large files), chunk before embedding:

```python
def chunk_segment(segment: ContextSegment, chunk_size: int = 512) -> List[str]:
    """Split long segments into smaller chunks for embedding"""
    if segment.tokens <= chunk_size:
        return [segment.text]
    
    # Use token-aware chunking (from requirements)
    chunks = []
    # Implementation would use tokenizer to split at token boundaries
    # Preserve code structure, sentence boundaries
    return chunks
```

**Chunking Guidelines**:
- Preserve semantic boundaries (sentences, code blocks)
- Use token-aware splitting (respect tokenizer boundaries)
- Overlap chunks slightly to preserve context
- Store chunk relationships in metadata

## 6. Vector Database Architecture

### Database Selection

**Recommended: FAISS** (for MVP)
- Fast, efficient similarity search
- Python-friendly, well-documented
- Good performance at scale
- In-memory or on-disk indexes

**Alternative: Qdrant** (for production)
- Full-featured vector database
- Metadata filtering
- REST API
- Better for distributed systems

**Alternative: Chroma** (for development)
- Simple, embedded
- Easy setup
- Good for prototyping

### Vector DB Schema

```python
# FAISS Index Structure
class VectorStore:
    def __init__(self, dimension: int = 384):
        import faiss
        # Index for similarity search
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Metadata storage (separate from index)
        self.metadata: Dict[str, ContextSegment] = {}
        
        # Segment ID to index position mapping
        self.id_to_idx: Dict[str, int] = {}
        self.idx_to_id: Dict[int, str] = {}
    
    def add_segment(self, segment: ContextSegment) -> None:
        """Add a segment to the vector store"""
        if segment.embedding is None:
            raise ValueError("Segment must have embedding")
        
        # Add to FAISS index
        idx = self.index.ntotal  # Current number of vectors
        self.index.add(segment.embedding.reshape(1, -1))
        
        # Store metadata
        self.metadata[segment.segment_id] = segment
        self.id_to_idx[segment.segment_id] = idx
        self.idx_to_id[idx] = segment.segment_id
    
    def search(self, query_embedding: np.ndarray, top_k: int = 10, 
               filters: Optional[Dict] = None) -> List[SearchResult]:
        """Search for similar segments"""
        # Perform vector search
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1),
            top_k * 2  # Get more results for filtering
        )
        
        # Filter and rank results
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty results
                break
            
            segment_id = self.idx_to_id[idx]
            segment = self.metadata[segment_id]
            
            # Apply filters
            if filters and not self._matches_filters(segment, filters):
                continue
            
            results.append(SearchResult(
                segment=segment,
                similarity_score=float(distance),
                rank=len(results) + 1
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def _matches_filters(self, segment: ContextSegment, filters: Dict) -> bool:
        """Check if segment matches filter criteria"""
        # Filter by type
        if 'type' in filters and segment.type != filters['type']:
            return False
        
        # Filter by time range
        if 'start_time' in filters and segment.timestamp < filters['start_time']:
            return False
        if 'end_time' in filters and segment.timestamp > filters['end_time']:
            return False
        
        # Filter by topic
        if 'topic' in filters and segment.topic != filters['topic']:
            return False
        
        # Filter by session
        if 'session_id' in filters and segment.session_id != filters['session_id']:
            return False
        
        return True
```

### Metadata Storage

Store metadata separately from vectors (FAISS only stores vectors):

```python
# Metadata storage options:
# 1. In-memory dictionary (simple, fast, not persistent)
# 2. SQLite database (persistent, queryable)
# 3. JSON file (simple, human-readable)
# 4. Embedded in vector DB (Qdrant, Chroma support this)

class MetadataStore:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.db = sqlite3.connect(storage_path / "metadata.db")
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS segments (
                segment_id TEXT PRIMARY KEY,
                session_id TEXT,
                text TEXT,
                type TEXT,
                timestamp TEXT,
                stashed_at TEXT,
                tokens INTEGER,
                topic TEXT,
                source TEXT,
                embedding_model TEXT,
                expires_at TEXT,
                protected BOOLEAN
            )
        """)
```

## 7. Retrieval Strategies

### Query Generation

**Query Types**:

1. **Task-based query**: Current task/goal description
   ```python
   query = "Fix authentication bug in login endpoint"
   ```

2. **Semantic query**: What the agent is looking for
   ```python
   query = "Previous discussion about error handling"
   ```

3. **Contextual query**: Related to current conversation
   ```python
   query = "Code patterns similar to current file"
   ```

4. **Hybrid query**: Combine multiple signals
   ```python
   query = f"{current_task}\n{recent_messages}\n{active_file_context}"
   ```

### Retrieval Pipeline

```python
class ContextRetriever:
    def __init__(self, vector_store: VectorStore, embedder: EmbeddingGenerator):
        self.vector_store = vector_store
        self.embedder = embedder
    
    def retrieve_relevant(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None,
        min_similarity: float = 0.7
    ) -> List[ContextSegment]:
        """Retrieve relevant stashed context segments"""
        
        # 1. Generate query embedding
        query_embedding = self.embedder.generate_embedding(query)
        
        # 2. Search vector store
        search_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Get more for filtering
            filters=filters
        )
        
        # 3. Filter by similarity threshold
        relevant = [
            result.segment
            for result in search_results
            if result.similarity_score >= min_similarity
        ][:top_k]
        
        # 4. Deduplicate (if same content stashed multiple times)
        relevant = self._deduplicate(relevant)
        
        return relevant
    
    def retrieve_by_reference(
        self,
        segment_id: str,
        max_hops: int = 2
    ) -> List[ContextSegment]:
        """Retrieve segments referenced by a given segment"""
        # Follow reference chains to find related context
        visited = set()
        to_visit = [(segment_id, 0)]
        results = []
        
        while to_visit:
            current_id, hops = to_visit.pop(0)
            if current_id in visited or hops > max_hops:
                continue
            
            visited.add(current_id)
            segment = self.vector_store.metadata.get(current_id)
            if segment:
                results.append(segment)
                # Add referenced segments
                for ref_id in segment.references:
                    to_visit.append((ref_id, hops + 1))
        
        return results
    
    def _deduplicate(self, segments: List[ContextSegment]) -> List[ContextSegment]:
        """Remove duplicate segments (same content, different IDs)"""
        seen_content = set()
        unique = []
        
        for segment in segments:
            content_hash = hashlib.md5(segment.text.encode()).hexdigest()
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique.append(segment)
        
        return unique
```

### Ranking and Scoring

```python
@dataclass
class SearchResult:
    segment: ContextSegment
    similarity_score: float  # Cosine similarity (0-1)
    rank: int
    
    def combined_score(self) -> float:
        """Compute combined relevance score"""
        # Combine multiple signals
        similarity = self.similarity_score
        temporal = self._temporal_score()
        recency = self._recency_score()
        
        # Weighted combination
        return (
            0.6 * similarity +  # Semantic similarity (primary)
            0.2 * temporal +    # Temporal relevance
            0.2 * recency       # How recently stashed
        )
    
    def _temporal_score(self) -> float:
        """Score based on when segment was created"""
        # Prefer more recent context
        age_days = (datetime.now() - self.segment.timestamp).days
        return math.exp(-age_days / 30)  # Exponential decay
    
    def _recency_score(self) -> float:
        """Score based on when segment was stashed"""
        # Recent stashes might be more relevant
        stash_age_days = (datetime.now() - self.segment.stashed_at).days
        return math.exp(-stash_age_days / 7)  # Faster decay for stashed items
```

## 8. Indexing and Maintenance

### Index Building

```python
class ContextIndexer:
    def __init__(self, vector_store: VectorStore, embedder: EmbeddingGenerator):
        self.vector_store = vector_store
        self.embedder = embedder
    
    def index_segment(self, segment: ContextSegment) -> None:
        """Index a single segment"""
        # Generate embedding if not present
        if segment.embedding is None:
            segment.embedding = self.embedder.generate_embedding(segment.text)
            segment.embedding_model = self.embedder.model_name
        
        # Add to vector store
        self.vector_store.add_segment(segment)
    
    def batch_index(self, segments: List[ContextSegment]) -> None:
        """Batch index multiple segments (more efficient)"""
        # Generate embeddings in batch
        texts = [seg.text for seg in segments]
        embeddings = self.embedder.batch_generate(texts)
        
        # Add to store
        for segment, embedding in zip(segments, embeddings):
            segment.embedding = embedding
            segment.embedding_model = self.embedder.model_name
            self.vector_store.add_segment(segment)
    
    def rebuild_index(self) -> None:
        """Rebuild entire index (e.g., after model change)"""
        # Collect all segments
        all_segments = list(self.vector_store.metadata.values())
        
        # Clear index
        self.vector_store.clear()
        
        # Re-index
        self.batch_index(all_segments)
```

### Index Maintenance

**Expiration and Cleanup**:

```python
class IndexMaintenance:
    def cleanup_expired(self, vector_store: VectorStore) -> int:
        """Remove expired segments from index"""
        now = datetime.now()
        expired_ids = []
        
        for segment_id, segment in vector_store.metadata.items():
            if segment.expires_at and segment.expires_at < now:
                if not segment.protected:
                    expired_ids.append(segment_id)
        
        # Remove from index
        for segment_id in expired_ids:
            self._remove_segment(vector_store, segment_id)
        
        return len(expired_ids)
    
    def cleanup_old(self, vector_store: VectorStore, max_age_days: int = 30) -> int:
        """Remove segments older than max_age_days"""
        cutoff = datetime.now() - timedelta(days=max_age_days)
        old_ids = []
        
        for segment_id, segment in vector_store.metadata.items():
            if segment.timestamp < cutoff and not segment.protected:
                old_ids.append(segment_id)
        
        for segment_id in old_ids:
            self._remove_segment(vector_store, segment_id)
        
        return len(old_ids)
```

**Index Optimization**:

```python
def optimize_index(vector_store: VectorStore) -> None:
    """Optimize vector index for better performance"""
    # For FAISS: Rebuild index if needed
    # For Qdrant: Optimize collection
    # For Chroma: Compact database
    
    # Remove deleted segments
    # Rebuild index structure
    pass
```

## 9. MCP Tool Integration

### Tool: stash_context

```python
@mcp_tool("stash_context")
def stash_context(
    segment_ids: List[str],
    expires_in_days: Optional[int] = None
) -> StashResult:
    """
    Stash context segments for later retrieval.
    
    Segments are removed from active context and stored in vector DB
    for semantic search and retrieval.
    """
    # 1. Get segments from platform context
    segments = platform_adapter.get_segments_by_ids(segment_ids)
    
    # 2. Generate embeddings
    embedder = EmbeddingGenerator()
    indexer = ContextIndexer(vector_store, embedder)
    
    # 3. Add metadata
    for segment in segments:
        segment.stashed_at = datetime.now()
        if expires_in_days:
            segment.expires_at = datetime.now() + timedelta(days=expires_in_days)
    
    # 4. Index segments
    indexer.batch_index(segments)
    
    # 5. Remove from active context
    platform_adapter.remove_segments(segment_ids)
    
    return StashResult(
        stashed_count=len(segments),
        segment_ids=[s.segment_id for s in segments],
        tokens_freed=sum(s.tokens for s in segments)
    )
```

### Tool: retrieve_stashed_context

```python
@mcp_tool("retrieve_stashed_context")
def retrieve_stashed_context(
    query: str,
    top_k: int = 5,
    min_similarity: float = 0.7,
    filters: Optional[Dict] = None
) -> RetrieveResult:
    """
    Retrieve stashed context segments relevant to the query.
    
    Uses semantic search to find context that matches the current task.
    """
    retriever = ContextRetriever(vector_store, embedder)
    
    # Retrieve relevant segments
    segments = retriever.retrieve_relevant(
        query=query,
        top_k=top_k,
        min_similarity=min_similarity,
        filters=filters
    )
    
    # Return results (agent decides whether to merge)
    return RetrieveResult(
        segments=[{
            "segment_id": s.segment_id,
            "text": s.text[:500] + "...",  # Preview
            "type": s.type.value,
            "similarity": retriever._last_similarity_score(s.segment_id),
            "timestamp": s.timestamp.isoformat()
        } for s in segments],
        total_found=len(segments)
    )
```

### Tool: merge_stashed_context

```python
@mcp_tool("merge_stashed_context")
def merge_stashed_context(
    segment_ids: List[str]
) -> MergeResult:
    """
    Merge retrieved stashed segments back into active context.
    """
    # 1. Get segments from vector store
    segments = [vector_store.metadata[sid] for sid in segment_ids]
    
    # 2. Merge into active context
    platform_adapter.add_segments(segments)
    
    # 3. Optionally remove from stash (if not needed anymore)
    # Or keep for future retrieval
    
    return MergeResult(
        merged_count=len(segments),
        tokens_added=sum(s.tokens for s in segments)
    )
```

## 10. Performance Considerations

### Embedding Generation Performance

- **Batch processing**: Generate embeddings in batches (32-64 at a time)
- **Async generation**: Use async/background tasks for large batches
- **Caching**: Cache embeddings for unchanged segments
- **Model selection**: Faster models for real-time, better models for batch

### Vector Search Performance

- **Index type**: Use appropriate FAISS index (FlatIP for small, IVF for large)
- **Pre-filtering**: Apply metadata filters before vector search when possible
- **Top-K scaling**: Retrieve more results than needed, filter after
- **Index optimization**: Periodically optimize/rebuild index

### Storage Considerations

- **Embedding storage**: Store embeddings separately (they're large)
- **Compression**: Compress embeddings if storage is limited
- **Metadata**: Use efficient storage format (SQLite, Parquet)
- **Cleanup**: Regular cleanup of expired/old segments

## 11. Decisions Summary

- **D1: Semantic Embeddings as Primary Relevance Signal**
  - **Rationale**: Effective proxy for attention/relevance, proven in RAG systems

- **D2: FAISS for MVP, Qdrant for Production**
  - **Rationale**: FAISS is fast and simple, Qdrant provides metadata filtering

- **D3: all-MiniLM-L6-v2 as Default Embedding Model**
  - **Rationale**: Good balance of speed and quality, small model size

- **D4: Separate Vector and Metadata Storage**
  - **Rationale**: FAISS only stores vectors, need separate metadata store

- **D5: Batch Embedding Generation**
  - **Rationale**: More efficient than one-at-a-time, better throughput

- **D6: Multi-Signal Ranking (Similarity + Temporal + Recency)**
  - **Rationale**: Semantic similarity alone insufficient, temporal factors matter

- **D7: Stash-on-Prune Strategy**
  - **Rationale**: Automatically stash when pruning, enables later retrieval

## 12. Implementation Phases

### Phase 1: Basic RAG (MVP)
- Embedding generation with all-MiniLM-L6-v2
- FAISS vector store
- Basic semantic search
- Simple stash/retrieve tools

### Phase 2: Enhanced Retrieval
- Metadata filtering
- Multi-signal ranking
- Reference chain following
- Deduplication

### Phase 3: Production Optimizations
- Qdrant migration (if needed)
- Batch processing
- Index optimization
- Expiration and cleanup

### Phase 4: Advanced Features
- Multi-embedding models (different for different segment types)
- Query expansion
- Relevance feedback
- Context summarization on retrieval

## 13. Open Questions

1. **Embedding Model Updates**: How to handle when changing embedding models? (rebuild index?)
2. **Multi-Modal Context**: How to handle images, code structures? (separate embeddings?)
3. **Cross-Session Retrieval**: Should stashed context persist across sessions?
4. **Embedding Storage**: Store embeddings in vector DB or separately?
5. **Query Optimization**: How to optimize queries for better retrieval?
6. **Privacy**: How to handle sensitive context in vector storage?

## 14. References

- **Attention Pruning Research**: `docs/research/attention_pruning_transformer_patterns.md`
- **FAISS Documentation**: https://github.com/facebookresearch/faiss
- **Sentence Transformers**: https://www.sbert.net/
- **Qdrant Documentation**: https://qdrant.tech/documentation/
- **RAG Pattern Papers**: Retrieval-Augmented Generation research

