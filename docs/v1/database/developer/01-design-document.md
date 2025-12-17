# Design Document: Semantic Search with Vector Embeddings

**Version:** 2.0  
**Date:** 2024-12-16  
**Author:** Developer Lead  
**Status:** Draft for Review

---

## Document Structure

This design follows a three-section structure:
1. **Context (WHY)** - Requirements, evidence, and research driving our decisions
2. **Solution (WHAT)** - What we're building and why these features
3. **Architecture (HOW)** - Patterns and principles guiding implementation

---

# Section 1: Context (WHY)

## 1.1 Problem Statement

**Current State:**  
The Out-of-Context MCP server stores contexts as `.mdc` files and uses substring search to find relevant contexts. This approach fails to capture semantic similarity - searching for "configure database" won't match contexts about "database setup" or "DB initialization."

**Evidence from Baseline Evaluation:**
- **Precision@5:** 0.255 (only 25.5% of top-5 results are relevant)
- **Primary failure mode:** Vocabulary mismatch (synonyms, paraphrases not matched)
- **Evaluation methodology:** 55-query test set with relevance judgments

**Success Criteria:**
- Precision@5 ≥ 0.332 (30% improvement, statistically significant)
- Query latency < 100ms p95
- Maintain Recall@5 ≥ 0.945

## 1.2 Requirements Summary

**Functional Requirements:**
- FR-1: Semantic search that finds contexts by meaning, not keywords
- FR-2: File-based source of truth (`.mdc` files remain authoritative)
- FR-3: Eventual consistency (< 10s from write to searchable)
- FR-4: Manual and automatic indexing

**Non-Functional Requirements:**
- NFR-1: Self-contained (no external services - Redis, PostgreSQL, Docker)
- NFR-2: STDIO transport (single process, MCP constraint)
- NFR-3: Local embeddings (no external APIs)
- NFR-4: Scale: 500k-1M tokens (1K-2K contexts initially, 2M future)

**Constraints:**
- STDIO transport limits architecture choices (no multi-process, no external services)
- All processing must be in-process or file-based
- Must work on developer laptops (no cloud dependencies)

## 1.3 Evidence Base

**[ANT-2024] Anthropic Contextual Retrieval:**
- Semantic search alone: 49% reduction in retrieval failures
- Hybrid (semantic + BM25): 67% reduction
- **Implication:** Semantic is high-value, hybrid is better but can be Phase 2

**Baseline Evaluation Results:**
- Query types: How-to (40%), Factual (31%), Troubleshooting (20%), Comparison (9%)
- Failure pattern: Vocabulary mismatch > Context ambiguity > Query vagueness
- **Implication:** Embeddings should excel at vocabulary mismatch (primary failure)

**Database Selection (Comprehensive Benchmark):**
- ChromaDB: 8.4ms p95 at 4K contexts (1.9x faster than LanceDB)
- Critical finding: Must test at max capacity, not average load
- See: `docs/v1/database/developer/00-database-choice-decision.md`

## 1.4 Embedding Model Landscape

**Key Insight:** Modern embedding models support 2K-8K token context lengths.

**Model Categories:**

| Model Class | Seq Length | Quality (SBERT) | Speed | Use Case |
|-------------|------------|-----------------|-------|----------|
| Short-context | 256-512 | 68-70 | 5-10ms | Short queries/docs |
| Mid-context | 512-2048 | 69-71 | 10-20ms | Most documents |
| Long-context | 2048-8192 | 69-72 | 20-40ms | Large documents |

**Examples (requires research/validation):**
- `all-MiniLM-L6-v2`: 256 tokens (too short for our contexts)
- `all-mpnet-base-v2`: 384 tokens (still requires chunking)
- Jina Embeddings v2: 8192 tokens (may handle full contexts)
- Nomic Embed: 8192 tokens (may handle full contexts)

**Design Implication:**  
Architecture must support:
1. **Model swapping** - Easy to try different models
2. **Chunking strategy** - If model context < document size
3. **Aggregation strategy** - If using chunks (mean pooling, max pooling, separate docs)

**Decision Deferred:** Specific model choice requires POC research (Dev 01-R).

## 1.5 Technical Context

**Existing Architecture:**
- FastMCP server with STDIO transport
- Direct file operations for read/write (20-60x faster than MCP tools)
- File watcher auto-corrects metadata (created_at, name validation)
- Storage: `.out_of_context/contexts/*.mdc` (YAML frontmatter + markdown)

**Integration Points:**
- Must add new `semantic_search` MCP tool
- Keep existing `search_context` (substring) as fallback
- Reuse existing file operations for indexing

---

# Section 2: Solution (WHAT)

## 2.1 Core Feature: Semantic Search

**What we're building:**  
A semantic search capability that generates vector embeddings from context text, stores them in a vector database, and retrieves similar contexts by cosine similarity.

**User experience:**
```
User: semantic_search(query="how to configure database", limit=5)
→ Returns contexts about "database setup", "DB configuration", "initialization"
→ Works even if exact words don't match
```

**Why this matters:**
- Addresses primary failure mode (vocabulary mismatch)
- Expected 30%+ improvement in Precision@5
- Enables natural language queries

## 2.2 Supporting Features

### 2.2.1 Automatic File Synchronization (MVP)

**What:** File watcher monitors `.mdc` files, automatically generates embeddings, updates vector DB.

**Why:** Users shouldn't manually trigger indexing. Write → searchable should be automatic (< 10s).

**Scope:** 
- MVP: Basic file watching with debouncing
- Future: Incremental updates, error recovery, staleness detection

### 2.2.2 Manual Index Management (MVP)

**What:** Tools to rebuild entire index from `.mdc` files.

**Why:** 
- Initial index population
- Error recovery
- Model upgrades (re-embed with new model)

**Scope:**
- MVP: Bulk index rebuild command
- Future: Index health checks, partial rebuilds

### 2.2.3 Metadata Moderation (MVP)

**What:** Automatically validate and correct `.mdc` metadata during indexing.

**Why:** Ensure consistency without user intervention (auto-add `created_at`, validate `name`).

**Scope:**
- MVP: Basic validation and correction
- Future: Schema evolution, migration tools

## 2.3 Explicitly NOT in MVP

**Deferred to Phase 2:**
- BM25 lexical search
- Hybrid search (semantic + BM25 + metadata filters)
- Chunking optimization (if using long-context model, may not need)
- Query rewriting/expansion
- Result re-ranking
- Caching layer

**Rationale:** Semantic alone provides 49% improvement. Get that working first, add complexity later.

## 2.4 Phased Delivery Strategy

**Phase 1: Core Semantic Search**
- Embedding service (with model abstraction)
- Vector database layer (ChromaDB)
- Search tool (semantic_search)
- Manual indexing (bulk load)
- **Goal:** Query → Results works end-to-end

**Phase 2: Automatic Synchronization**
- File watcher service
- Metadata moderation
- Automatic index updates
- **Goal:** Write → Searchable automatically

**Phase 3: Quality & Optimization**
- Performance tuning
- Error handling refinement
- Monitoring/observability
- **Goal:** Production-ready

**Phase 4: Advanced Features** (Future)
- BM25 integration
- Hybrid search
- Advanced chunking
- **Goal:** Maximize quality

**Design Principle:** Each phase delivers working value. Fail fast if Phase 1 doesn't achieve quality targets.

## 2.5 Success Metrics

**Quality (Primary):**
- Precision@5 ≥ 0.332 (30% improvement over baseline)
- Statistical significance: p < 0.05
- Measured via: Scientist evaluation with 55-query test set

**Performance (Secondary):**
- Query latency: < 100ms p95 (expected: 10-50ms)
- Convergence time: < 10s p95 (write → searchable)
- Measured via: Developer benchmarks

**Acceptance Criteria:**
- Quality metric must pass
- Performance metrics should pass (can negotiate if quality is exceptional)
- All integration tests pass
- Design review approved (Scientist + User)

---

# Section 3: Architecture (HOW)

## 3.1 Architectural Principles

### Principle 1: Layered Architecture

**Pattern:** Strict layering with clear dependencies (top → bottom, never reverse).

```
Layer 4: MCP Tools (semantic_search, existing tools)
    ↓
Layer 3: Service Layer (EmbeddingService, SearchService)
    ↓
Layer 2: Data Layer (VectorDB, FileStorage)
    ↓
Layer 1: Infrastructure (ChromaDB, Watchdog, File System)
```

**Benefits:**
- Clear separation of concerns
- Testable (mock layer boundaries)
- Swappable implementations (e.g., swap vector DB)

**Constraints:**
- Layer N can only depend on Layer N-1
- No circular dependencies
- Cross-layer calls only through interfaces

### Principle 2: File-Based Source of Truth

**Pattern:** Event sourcing variant where files are the source of truth, vector DB is a projection.

```
.mdc files (source of truth)
    → File events (create, modify, delete)
    → Projection: Vector DB (queryable index)
```

**Benefits:**
- Simple mental model (files are real, DB is cache)
- Easy recovery (rebuild from files)
- No dual-write problems

**Constraints:**
- Vector DB can be destroyed and rebuilt anytime
- Never trust vector DB over files (files win)
- Eventual consistency acceptable (< 10s)

### Principle 3: Plugin Architecture for Models

**Pattern:** Strategy pattern for embedding generation.

```
EmbeddingService (interface)
    ├─ MiniLMEmbedder (256 tokens + chunking)
    ├─ MPNetEmbedder (384 tokens + chunking)
    └─ LongContextEmbedder (8192 tokens, no chunking)
```

**Benefits:**
- Easy to swap models (configuration change)
- Easy to benchmark models (side-by-side comparison)
- Future-proof (add new models without architecture changes)

**Constraints:**
- All embedders must produce same dimensionality (or abstraction layer handles it)
- Embedders must handle their own chunking if needed
- Model version tracked in metadata (for re-indexing)

### Principle 4: Eventual Consistency by Design

**Pattern:** Write operations are async, reads are eventually consistent.

```
User writes .mdc file (immediate)
    → Background: File watcher (500ms debounce)
    → Background: Generate embeddings (10-50ms)
    → Background: Update vector DB (1-5ms)
    → Searchable (< 10s total)
```

**Benefits:**
- Fast write operations (no blocking)
- Simple error handling (retry in background)
- No distributed transactions

**Constraints:**
- Users see content immediately (file read)
- Semantic search may lag by < 10s
- Substring search always current (reads files directly)

## 3.2 Component Architecture

### 3.2.1 Embedding Service

**Responsibility:** Generate vector embeddings from text.

**Interface:**
- `embed_text(text: str) → List[float]` - Single embedding
- `embed_batch(texts: List[str]) → List[List[float]]` - Batch (efficient)
- `get_model_info() → ModelInfo` - Name, version, dimensions, max_length

**Design Patterns:**
- **Strategy Pattern:** Different embedders (MiniLM, MPNet, LongContext)
- **Template Method:** Common flow (validate input, chunk if needed, encode, aggregate)
- **Singleton:** Load model once at startup

**Key Design Decision:**  
Embedder handles its own chunking strategy. If model max_length < input length, embedder chunks and aggregates. Service interface remains simple.

**Extensibility Points:**
- New embedders: Implement interface
- New chunking strategies: Override template method
- New aggregation: Override aggregation step

### 3.2.2 Vector Database Layer

**Responsibility:** Store and search vector embeddings.

**Interface:**
- `upsert(id, embedding, metadata, document)` - Insert or update
- `search(query_embedding, limit, filters) → Results` - Similarity search
- `delete(id)` - Remove context
- `clear()` - Rebuild (delete all)
- `count() → int` - Total contexts

**Design Patterns:**
- **Repository Pattern:** Abstract database details
- **Adapter Pattern:** ChromaDB-specific implementation
- **Builder Pattern:** Complex query construction (for future hybrid search)

**Key Design Decision:**  
Use ChromaDB ephemeral client (in-memory). Vector DB is a *cache*, rebuilt from files on startup. Trades persistence for simplicity.

**Extensibility Points:**
- Swap to LanceDB: Implement same interface
- Add hybrid search: Extend interface with filter methods
- Add persistence: Use persistent ChromaDB client

### 3.2.3 File Watcher Service

**Responsibility:** Monitor `.mdc` files, trigger indexing on changes.

**Design Patterns:**
- **Observer Pattern:** File system is observable, watcher observes
- **Command Pattern:** File events become commands (IndexCommand, DeleteCommand)
- **Debouncing:** Wait 500ms after last change before processing

**Key Design Decision:**  
Metadata moderation happens *during* indexing, not as separate step. File watcher reads, corrects, writes back, then indexes. Single pass.

**Extensibility Points:**
- Pluggable validators: Add new metadata rules
- Pluggable moderators: Different correction strategies
- Pluggable event handlers: React to other file types

### 3.2.4 Search Service

**Responsibility:** Orchestrate query → embedding → search → results.

**Interface:**
- `semantic_search(query, limit) → Results` - End-to-end search

**Design Patterns:**
- **Facade Pattern:** Hide complexity of embedding + search
- **Decorator Pattern:** Add result formatting, scoring transforms
- **Chain of Responsibility:** Query preprocessing pipeline (future)

**Key Design Decision:**  
Service owns the query pipeline: preprocess → embed → search → postprocess. MCP tool is thin wrapper.

**Extensibility Points:**
- Query preprocessing: Rewriting, expansion
- Result postprocessing: Re-ranking, filtering
- Hybrid search: Combine semantic + BM25 results

## 3.3 Integration Architecture

### 3.3.1 MCP Tool Layer

**Integration approach:**  
Add new `semantic_search` tool alongside existing tools. Don't replace or modify existing tools.

**Rationale:**
- Minimize risk (existing tools keep working)
- A/B comparison (users can try both)
- Graceful fallback (if semantic fails, use substring)

**Tool interface:**
```
semantic_search(query: str, limit: int = 5) → SearchResults
```

### 3.3.2 Startup Sequence

**Bootstrap order matters:**

1. Load configuration
2. Initialize embedding service (load model - 2 seconds)
3. Initialize vector database (ephemeral client)
4. Rebuild index from `.mdc` files (bulk load - 10-30 seconds for 1K contexts)
5. Start file watcher (background monitoring)
6. Register MCP tools
7. Server ready

**Design Decision:**  
Startup rebuilds entire index. Trades startup time (10-30s) for simplicity (no persistent state to manage).

### 3.3.3 Error Handling Strategy

**Principle:** Fail fast for critical errors, retry for transient errors, degrade gracefully for non-critical.

**Critical errors (fail fast):**
- Model fails to load → Crash server with clear error
- Vector DB initialization fails → Crash server
- Configuration invalid → Crash server

**Transient errors (retry 3x with backoff):**
- File read fails → Retry
- Embedding generation fails → Retry
- Vector DB write fails → Retry

**Non-critical errors (log and continue):**
- Single file malformed → Skip file, log error
- Metadata correction fails → Use original metadata
- File watcher misses event → Will catch on next change

**Graceful degradation:**
- If semantic search unavailable → Fallback to substring search
- If embeddings take too long → Return empty results with timeout message

## 3.4 Data Flow

### 3.4.1 Indexing Flow

```
1. File Event (create/modify .mdc)
   ↓
2. Debounce (500ms wait for more changes)
   ↓
3. Read file (YAML + markdown)
   ↓
4. Moderate metadata (validate, correct, write back if needed)
   ↓
5. Generate embedding (chunk if needed, aggregate)
   ↓
6. Upsert to vector DB (with metadata)
   ↓
7. Context now searchable
```

**Performance:** ~10-50ms (embedding) + 1-5ms (DB) + 500ms (debounce) = < 10s p95

### 3.4.2 Query Flow

```
1. User calls semantic_search(query, limit)
   ↓
2. Search service receives query
   ↓
3. Generate query embedding (10-50ms)
   ↓
4. Search vector DB (1-5ms)
   ↓
5. Format results (convert distance to similarity, preview text)
   ↓
6. Return to user
```

**Performance:** ~10-50ms (embedding) + 1-5ms (search) + 1ms (format) = < 100ms p95

## 3.5 Extensibility Design

### 3.5.1 Model Swapping

**How to swap models:**
1. Update configuration (model name)
2. Restart server (loads new model)
3. Index rebuilds automatically (new embeddings)

**Why this works:**
- Embedding service abstracts model details
- Model version stored in metadata
- Can detect version mismatch and auto-rebuild

### 3.5.2 Future Hybrid Search

**Architecture ready for:**
- BM25 integration: Add lexical search service (parallel to vector search)
- Result fusion: Combine semantic + BM25 scores (Reciprocal Rank Fusion)
- Metadata filters: Vector DB already stores metadata, just expose in API

**Design Decision:**  
Don't build hybrid search now, but architecture shouldn't block it. Keep doors open.

### 3.5.3 Future Optimizations

**Architecture supports:**
- Caching: Add cache layer above embedding service
- Async indexing: File watcher already async
- Incremental updates: Vector DB supports upsert (already designed)
- Query routing: Add router to choose semantic vs substring vs hybrid

## 3.6 Testing Strategy

**Unit testing boundaries:**
- Embedding Service: Mock model, test chunking/aggregation logic
- Vector DB Layer: Use real ChromaDB ephemeral client (fast)
- File Watcher: Mock file system events
- Search Service: Mock embedding + vector DB

**Integration testing:**
- End-to-end: Write file → Wait → Query → Verify results
- Performance: Benchmark latency with real model + DB
- Quality: Run 55-query evaluation

**Why real ChromaDB in unit tests:**
- Ephemeral client is fast (< 10ms)
- Tests actual integration, not mocks
- Catches API changes

## 3.7 Open Questions & Research Needs

**Question 1: Which embedding model?**
- **Research needed:** POC to test 2-3 models (MiniLM+chunking, MPNet+chunking, long-context)
- **Metrics:** Quality (P@5), Latency, Complexity
- **Decision:** Dev 01-R (Research Task)

**Question 2: Chunking strategy (if needed)?**
- **Options:** Fixed-size, sentence-aware, overlap amount
- **Research needed:** Test different strategies with chosen model
- **Decision:** Part of Dev 01-R

**Question 3: Aggregation strategy (if chunking)?**
- **Options:** Mean pooling, max pooling, separate documents, weighted
- **Research needed:** Depends on model and chunking choice
- **Decision:** Part of Dev 01-R

**Question 4: Startup time acceptable?**
- **Current:** 10-30s to rebuild index on startup
- **Alternative:** Persist vector DB (adds complexity)
- **Decision:** Start with rebuild, optimize if users complain

---

## Appendix A: Design Rationale

### Why ChromaDB over LanceDB?

- 1.9x faster at max capacity (8.4ms vs 15.9ms p95)
- Built-in hybrid search (future-proof)
- Ephemeral client perfect for STDIO constraint
- See: `docs/v1/database/developer/00-database-choice-decision.md`

### Why Ephemeral over Persistent?

- **Pro:** Simple (no state management), fast (in-memory), STDIO-friendly
- **Con:** Rebuild on startup (10-30s)
- **Decision:** Simplicity wins. Optimize later if needed.

### Why Keep Substring Search?

- Different use case (exact phrase matching)
- Fallback if semantic unavailable
- Users can choose best tool for their need

### Why Not Hybrid in MVP?

- Semantic alone: 49% improvement (substantial)
- Hybrid: 67% improvement (incremental gain)
- **Decision:** Get 49% first, add 18% later

---

## Appendix B: References

- `docs/v1/database/requirements.md` - Full requirements (v2.0.0)
- `docs/v1/database/developer/00-database-choice-decision.md` - DB selection
- `docs/v1/database/scientist/baseline-analysis.md` - Baseline evaluation
- `docs/v1/database/scientist/evaluation-testset.json` - 55-query test set
- `.out_of_context/contexts/decision-database-chromadb.mdc` - ChromaDB decision
- `.out_of_context/contexts/history-decisions-phase0.mdc` - Phase 0 decisions

---

## Next Steps

1. **Dev 01-R: Research Task** - Model selection and chunking strategy POC (4-6 hours)
2. **Design Review** - User + Scientist review this document
3. **Dev 02: Execution Plan** - Break into implementable tasks (3-4 hours)
4. **Gate 1: Approval** - Go/No-Go decision
5. **Dev 03-09: Implementation** - Build it (2 weeks)

**Critical Path:** Dev 01-R must complete before finalizing execution plan. Can't estimate implementation without knowing model/chunking approach.

---

**END OF DESIGN DOCUMENT**

