# Database Layer Requirements for Out-of-Context MCP Server

**Version:** 2.1.0 (Revised - Unlocked Model Choice)  
**Date:** 2024-12-16  
**Status:** Active for Implementation  
**Changelog:** See `.out_of_context/contexts/requirements-revision-changelog.mdc`

---

## Quick Reference for Developers

**What You're Building:**
Semantic search capability using local embeddings, integrated into the existing MCP server.

**Key Decisions:**
- 🔬 Embedding Model: Research required (Scientist 04) - Must support ≥512 tokens
- ✅ Consistency: Eventual (convergence < 10s target) + invalidation mechanism
- ✅ Scale: 500k-1M tokens (1K-2K contexts), future 2M tokens  
- ✅ Transport: Self-contained, STDIO compatible
- 🔧 Chunking: Optional/Recommended (Developer design choice)

**Your Design Decisions:**
- 🔧 Vector Database: ChromaDB selected (see Dev 00)
- 🔧 API Design: New `semantic_search` tool (keep existing `search_context`)
- 🔧 Database Schema: Must support vector + mtime tracking + invalidation
- 🔧 File Watcher: watchdog library (async file monitoring)
- 🔧 Chunking Strategy: IF model max_length < context length (integrate with sentence-transformers)
- 🔧 Invalidation Mechanism: Detect and handle stale index entries

**Success Targets:**
- Query latency: < 100ms p95
- Quality: >30% improvement over substring search (target, measure actual)
- Convergence: < 10s p95 for single file change

**What's NOT in MVP:**
- ❌ BM25 lexical search (Phase 2)
- ❌ Metadata filtering API (schema OK, query API later)
- ❌ Hybrid search (requires BM25 first)
- ❌ Advanced chunking optimization (basic chunking IS in MVP if needed)

---

## 1. MVP Scope

### In Scope (Phase 1 - MVP)

**MUST Implement:**
1. **Semantic search** via vector embeddings (FR-1)
2. **File synchronization** - detect .mdc changes, update index (FR-4)
3. **Index rebuild** - full rebuild from .mdc files on demand (FR-5)
4. **Integration** with existing MCP tool system (INT-1)

**Success Criteria:**
- Functional: Semantic search returns relevant results
- Performance: Query latency < 100ms p95 with 2K contexts
- Quality: Measurable improvement over substring baseline (target >30%)

### Out of Scope (Future Phases)

**Phase 2 - Hybrid Search:**
- BM25 lexical search (FR-2 SHOULD)
- Hybrid retrieval combining semantic + BM25
- Rank fusion algorithms

**Phase 3 - Advanced Features:**
- Metadata filtering API (FR-3 MAY)
- Query expansion via LLM
- Contextual retrieval (chunk-level context prepending)

**Explicitly NOT Planned:**
- Neural reranking models
- External API-based embeddings (local only)
- Distributed vector search
- Multi-language support (English only for MVP)

---

## 2. Executive Summary

### 2.1 Problem

Current substring search (`query_lower in text.lower()`) cannot capture semantic similarity, has no relevance ranking, and misses variations/synonyms.

### 2.2 Solution

Add database layer to index semantic embeddings from .mdc files, enabling vector similarity search while keeping .mdc files as source of truth.

### 2.3 Evidence Base

**[ANT-2024]** Anthropic Contextual Retrieval (Sept 2024) showed:
- Semantic embeddings: 49% reduction in retrieval failures
- Hybrid (semantic + BM25): 67% reduction (additional 18% improvement)

**Relevance:** Production validation at scale, quantitative metrics

See Appendix A for full evidence documentation.

---

## 3. Functional Requirements

### FR-1: Semantic Search (MUST)

**Requirement:** The system MUST support semantic search via vector embeddings.

**Constraints:**
- Embedding model: `all-MiniLM-L6-v2` (384 dimensions, sentence-transformers)
- Similarity metric: Cosine similarity
- Return: Top-K results ranked by similarity score

**Why:** Enables contextually relevant retrieval. Evidence [ANT-2024] shows 49% improvement.

**Acceptance:**
- [ ] Query text → embedding → top-K similar contexts returned
- [ ] Results include similarity scores (0.0-1.0)
- [ ] Query latency < 100ms p95 (including embedding generation)

---

### FR-2: Lexical Search (SHOULD - Phase 2)

**Requirement:** The system SHOULD support BM25 lexical search for future hybrid retrieval.

**Why:** Evidence [ANT-2024] shows hybrid (semantic + BM25) provides additional 18% improvement over semantic-only.

**MVP Status:** NOT in Phase 1. Semantic search provides substantial value (49%) alone. BM25 is incremental improvement for Phase 2.

**Acceptance (Phase 2):**
- [ ] BM25 index built from .mdc content
- [ ] Lexical search endpoint or parameter
- [ ] Preparation for hybrid rank fusion

---

### FR-3: Metadata Filtering (MAY - Future)

**Requirement:** The system MAY support metadata filtering on YAML frontmatter fields.

**Why:** Enables structured queries (e.g., by date, tags). However, no quantitative evidence found for significant benefit in LLM retrieval use cases.

**MVP Status:** NOT in Phase 1. Database schema MAY include basic metadata fields (created_at, tags) for future-proofing, but query API is deferred.

---

### FR-4: Index Synchronization (MUST)

**Requirement:** The system MUST detect .mdc file changes and update indices.

**Constraints:**
- Eventual consistency (not real-time)
- Target convergence: < 10 seconds p95
- Detection: File system watcher or mtime polling

**Why:** .mdc files remain source of truth and can be edited directly. Stale indices would return incorrect results.

**Acceptance:**
- [ ] File created → embedding generated → inserted into index
- [ ] File modified → re-embed → update index
- [ ] File deleted → remove from index
- [ ] Convergence time < 10s p95 measured

**Research:** RT-2 measures actual convergence time

---

### FR-5: Index Rebuild (MUST)

**Requirement:** The system MUST support full index rebuild from .mdc files.

**Why:** Recovery from corruption, schema changes, or embedding model upgrades.

**Constraints:**
- Must be non-destructive to .mdc files
- Target: < 30 seconds for 2K contexts

**Acceptance:**
- [ ] Command or API to trigger rebuild
- [ ] Rebuilds all embeddings from .mdc files
- [ ] Completes in < 30s for 2K contexts
- [ ] Validates rebuild success

---

## 4. Non-Functional Requirements

### NFR-1: Performance (MUST)

**Query Latency:**
- Target: < 100ms p95 for top-10 results
- Breakdown: < 50ms embedding generation + < 50ms vector search
- Scale: Must meet target with 1K-4K contexts

**Index Rebuild:**
- Target: < 30 seconds for 2K contexts
- Acceptable: Up to 60 seconds for 4K contexts

**Convergence:**
- Target: < 10 seconds p95 for single file change
- Acceptable: Up to 30 seconds for batch of 10 files

**Research:** RT-1 and RT-5 validate latency assumptions

---

### NFR-2: Scale (MUST / SHOULD)

**Current Target (MUST):**
- 500k-1M tokens stored (~2-4MB text)
- 1K-2K contexts at ~500 tokens/context
- 1K-2K embeddings at 384 dimensions
- Memory footprint: ~10MB for vectors + indices

**Future Target (SHOULD):**
- 2M tokens (~8MB text)
- 4K contexts
- 4K embeddings
- Memory footprint: ~20MB

**Why:** Scale defined by LLM context window capabilities (most support 200k-1M tokens).

---

### NFR-3: Consistency (MUST)

**Model:** Eventual consistency between .mdc files and database indices

**Why:** Enables async index updates without blocking writes. Simpler error handling.

**Guarantees:**
- File writes succeed immediately (no database dependency)
- Index updates happen asynchronously (background process)
- Queries may return stale results briefly (< 10s target)
- System converges to consistent state

---

### NFR-3A: Invalidation Mechanism (MUST)

**Requirement:** System MUST detect and handle stale index entries.

**Why:** Eventual consistency requires way to know if index is stale and how to handle it.

**Acceptable Approaches (Developer Choice):**

**Option 1: mtime Tracking (Recommended)**
- Store file mtime with embedding in vector DB
- On query: Compare current file mtime with indexed mtime
- If different: Re-index in background, optionally flag as stale

**Option 2: Content Hashing**
- Hash file content, store with embedding
- On query: Compare current hash with indexed hash
- More robust but higher overhead

**Option 3: Version Tagging**
- Increment version counter on each file change
- Store version with embedding
- Compare versions to detect staleness

**Response to Staleness (Developer Choice):**
- Option A: Return stale results + background re-index (fast, eventually correct)
- Option B: Wait for re-index up to timeout (slower, immediately correct)
- Option C: Hybrid (return stale if re-index > threshold, otherwise wait)

**Design Requirement:** Document chosen approach in design doc Section 3.7

**Time:** Part of Dev 01-R (6-8 hours total including chunking)

---

### NFR-4: Self-Containment (MUST)

**Requirement:** All database operations MUST occur within the single MCP server process.

**Why:** STDIO transport precludes external services, containers, or network dependencies.

**Acceptable Technologies:**
- ✅ Embedded databases: SQLite, ChromaDB (embedded), LanceDB
- ✅ In-process libraries: sentence-transformers, numpy, faiss
- ✅ File-based storage: All state persists to local files

**Unacceptable:**
- ❌ Redis, Memcached (external process)
- ❌ PostgreSQL, MySQL (external service)
- ❌ Docker sidecars (container required)
- ❌ Cloud vector DBs (network + API keys)

---

## 5. Technology Constraints

### TC-1: Embedding Model (Scientist Research Required)

**Constraint:** Model MUST support ≥512 token context length OR chunking strategy MUST be designed.

**Why Change from v2.0.0:** Original choice (`all-MiniLM-L6-v2`, 256 tokens) cannot handle our contexts (500-1000+ tokens). Scientist must research and recommend appropriate model.

**Research Task:** Scientist Action Item 04 - Embedding Model Selection
- Survey models with ≥512 token support (MTEB leaderboard)
- Benchmark top 3 candidates (quality, latency, context handling)
- Recommend model with evidence

**Selection Criteria:**
1. Context length: ≥512 tokens (prefer 2K-8K)
2. Quality: Comparable to all-MiniLM-L6-v2 (SBERT ≥68)
3. Speed: Embedding generation < 50ms for 500-token context
4. Size: < 500MB download (local deployment)
5. sentence-transformers compatible

**Deliverable:** `docs/v1/database/scientist/04-model-selection-research.md`

**Time:** 4-6 hours (0.5-1 day)

**Blocks:** Final design document, execution plan, implementation

---

### TC-1A: Chunking Strategy (Developer Design Choice)

**Requirement:** IF model max_length < context length, MUST implement chunking strategy.

**Recommendation:** Consider chunking even with long-context models for faster embedding (parallel processing of smaller segments).

**Design Requirements:**
- Must integrate with sentence-transformers library
- Must handle contexts of 500-1000+ tokens
- Should support overlap (e.g., 50-100 tokens) for context preservation
- Must include aggregation strategy (mean pooling, max pooling, or separate documents)

**Acceptable Approaches:**
1. Fixed-size chunking (e.g., 512 tokens with 50-token overlap)
2. Sentence-aware chunking (langchain, semantic-text-splitter)
3. Paragraph-based chunking (preserve semantic boundaries)

**Developer Decision:** Design chunking abstraction in Dev 01-R, document in design doc Section 3.

**Time:** Part of Dev 01-R (6-8 hours total including invalidation mechanism)

---

### TC-2: Vector Database (Selected: ChromaDB)

**Decision:** ChromaDB (embedded mode) selected via Developer Action Item 00.

**Constraints (ALL must be met):**
- ✅ Embedded (no external process)
- ✅ STDIO compatible
- ✅ Supports 1K-4K vectors comfortably
- ✅ Query latency contributes < 50ms to total
- ✅ File-based persistence

**Selection Criteria:**
1. Performance (must meet < 100ms total with embedding)
2. Simplicity (fewer dependencies better)
3. Documentation and community support

**Developer Decision:** Evaluate options via RT-3, choose based on criteria, document rationale.

**Initial Recommendation:** ChromaDB (embedded mode) - widely used in RAG systems, good docs. But validate with benchmark.

---

### TC-3: Configuration (MUST)

**Requirement:** System MUST be configurable via environment variables.

**Required Variables:**
- `OUT_OF_CONTEXT_STORAGE_PATH` - .mdc files location (existing)
- `OUT_OF_CONTEXT_INDEX_PATH` - database/index location (new)

**Optional Variables:**
- `OUT_OF_CONTEXT_EMBEDDING_MODEL` - model name (default: all-MiniLM-L6-v2)
- `OUT_OF_CONTEXT_VECTOR_DB` - database choice if supporting multiple

**Defaults:**
- INDEX_PATH: `{STORAGE_PATH}/../index`
- EMBEDDING_MODEL: `all-MiniLM-L6-v2`

---

## 6. Interface Requirements

These define HOW the database layer integrates with the existing system. Implementation details (API signatures, schemas) are developer's design responsibility.

### INT-1: MCP Tool Integration (MUST)

**Requirement:** Semantic search MUST be exposed as an MCP tool.

**Options (Developer Chooses):**
1. **Replace existing `search_context`** - Semantic search becomes default
2. **New tool `semantic_search_context`** - Keep both substring and semantic
3. **Parameter on `search_context`** - `method="semantic"|"substring"`

**Constraints:**
- MUST follow existing MCP tool patterns (`@mcp.tool()` decorator)
- MUST return structured results matching MCP conventions
- MUST handle errors gracefully (return error dicts, not exceptions)

**Developer Decision:** Choose integration approach based on user experience and backwards compatibility considerations.

---

### INT-2: Error Handling (MUST)

**Requirement:** System MUST return structured errors matching existing MCP patterns.

**Error Cases to Handle:**
- Database not initialized → `SERVICE_UNAVAILABLE`
- Embedding model not loaded → `SERVICE_UNAVAILABLE`  
- Invalid query (empty, etc.) → `INVALID_PARAMETER`
- Index corruption detected → `INTERNAL_ERROR` + trigger rebuild

**Pattern:**
```python
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable description"
    }
}
```

---

### INT-3: Observability (SHOULD)

**Requirement:** System SHOULD expose metrics for monitoring.

**Useful Metrics:**
- Query latency histogram (embedding time, search time, total time)
- Index size (number of contexts, memory usage)
- Convergence lag (time since last file change)
- Staleness rate (% of queries returning stale results)

**Implementation:** Log structured metrics, expose via status endpoint if feasible.

---

## 7. Evaluation Methodology

### 7.1 Quality Metrics

**Primary Metrics:**
- **Precision@5**: Of top-5 results, how many are relevant?
- **Recall@5**: Of all relevant contexts, how many in top-5?
- **MRR** (Mean Reciprocal Rank): Average of 1/rank of first relevant result
- **NDCG@10**: Normalized Discounted Cumulative Gain at 10 results

**Baseline:** Current substring search

**Target:** Statistically significant improvement (p < 0.05), with goal >30% relative improvement in Precision@5

---

### 7.2 Evaluation Test Set (RT-10)

**Requirement:** Scientist MUST create evaluation test set before claiming quality improvement.

**Specifications:**
- **Size:** Minimum 50 queries
- **Coverage:** Representative of actual LLM usage patterns
- **Relevance Judgments:** Binary (relevant/not relevant) per query-context pair
- **Diversity:** Include various query types (factual, conceptual, specific terms, broad topics)

**Format:**
```json
{
    "queries": [
        {
            "query": "How do I train a neural network?",
            "relevant_contexts": ["ml-basics", "training-guide"],
            "type": "how-to"
        }
    ]
}
```

**Process:**
1. Scientist creates test set from typical queries
2. Scientist provides relevance judgments
3. Developer runs baseline (substring) to get baseline metrics
4. Developer runs semantic search to compare
5. Report results with statistical significance

---

### 7.3 Acceptance Criteria

**Functional:**
- [ ] Semantic search returns results for all test queries
- [ ] Results include similarity scores
- [ ] No crashes or errors on test set

**Performance:**
- [ ] Query latency < 100ms p95 across test set
- [ ] Index rebuild completes in < 30s for full corpus
- [ ] Convergence < 10s p95 when file modified during testing

**Quality:**
- [ ] Precision@5 improvement over baseline
- [ ] Improvement is statistically significant (p < 0.05)
- [ ] Target: >30% relative improvement (if achievable, document if not)
- [ ] No major regressions (queries that worked before still work)

**Scientific Honesty:** If 30% improvement not achieved, document actual improvement and investigate causes. Do not claim success without measurement.

---

## 8. Research Tasks

Research tasks validate that requirements are achievable. Some are scientist's responsibility (evaluation), others are developer's (implementation validation).

### RT-1: Validate Query Latency (Developer)

**Question:** Can we achieve < 100ms p95 latency at our scale?

**Method:**
1. Implement basic semantic search
2. Index 1K, 2K, 4K contexts
3. Run 100 test queries, measure p50/p95/p99
4. Break down: embedding time, search time, overhead

**Success:** p95 < 100ms at 2K contexts

**If Fails:** Optimize (batching, caching) or increase target to < 200ms

**Owner:** Developer (during implementation)

---

### RT-2: Measure Convergence Time (Developer)

**Question:** How long does eventual consistency actually take?

**Method:**
1. Modify .mdc file
2. Measure time until index updated (via query or status check)
3. Test: single file, batch of 10, batch of 50

**Success:** p95 < 10s for single file

**If Exceeds:** Acceptable up to 30s; document as limitation

**Owner:** Developer (during implementation)

---

### RT-3: Choose Vector Database (Developer)

**Question:** Which database best meets our constraints?

**Method:**
1. Implement POC with ChromaDB and LanceDB (skip SQLite unless others fail)
2. Measure query latency at 2K vectors
3. Evaluate installation size, dependencies
4. Compare API ergonomics

**Decision Criteria:**
1. Performance (< 50ms search contributes to < 100ms total)
2. Simplicity (fewer dependencies)
3. Documentation quality

**Success:** Select one, document rationale

**Owner:** Developer (before main implementation)

**Status:** BLOCKING for implementation

---

### RT-5: Benchmark Embedding Model (Developer)

**Question:** What is actual inference time for all-MiniLM-L6-v2 on target hardware?

**Method:**
1. Load model
2. Embed 100 sample contexts (100-1000 tokens each)
3. Measure p50/p95 embedding time

**Success:** Single query embedding < 50ms p95

**If Fails:** Try ONNX runtime optimization or accept < 100ms target may need adjustment

**Owner:** Developer (during implementation)

---

### RT-7: Measure Write Latency (Developer)

**Question:** Does eager indexing add acceptable latency to writes?

**Method:**
1. Implement file watcher with eager embedding
2. Measure `put_context` latency with vs without indexing
3. Test: single write, batch of 10

**Success:** Single write < 500ms p95

**If Exceeds:** Switch to async eager indexing (return immediately, index in background)

**Owner:** Developer (during implementation)

---

### RT-10: Create Evaluation Test Set (Scientist)

**Question:** What queries and relevance judgments define "good retrieval"?

**Method:**
1. Collect 50+ representative queries from intended usage
2. For each query, identify relevant contexts (gold standard)
3. Document query types and coverage
4. Validate test set with stakeholder

**Success:** Test set with 50+ queries, relevance judgments, documented

**Owner:** Scientist (before quality evaluation)

**Status:** BLOCKING for quality acceptance testing

---

## 9. Architecture Principles

These guide design but don't prescribe implementation.

### AP-1: Separation of Concerns

**Principle:** Database indexes .mdc files; it does not own content.

**Implications:**
- .mdc files remain authoritative source
- Database indices are derived data (can be rebuilt)
- Direct .mdc edits must trigger index updates
- Index corruption does not lose data

---

### AP-2: Fail-Safe Defaults

**Principle:** System degrades gracefully when database unavailable.

**Implications:**
- If index not built, system should still function (fallback to substring search OR build index lazily)
- If embedding fails, skip that context, continue with others
- If database corrupted, trigger rebuild, serve stale results temporarily

---

### AP-3: Measurability

**Principle:** All requirements must be measurable.

**Implications:**
- Performance: latency, throughput → benchmark
- Quality: precision, recall → evaluation test set
- Scale: token count, memory usage → measure
- No unmeasurable claims like "fast" or "good" without metrics

---

## 10. Non-Requirements (Explicit Scope Exclusions)

### What We're NOT Building

1. **Distributed Search** - Single process only (STDIO constraint)
2. **External API Embeddings** - Local model only (self-contained constraint)
3. **Full CRUD via Database** - .mdc files remain write path
4. **Real-Time Consistency** - Eventual only (< 10s convergence acceptable)
5. **Chunking** - Full-document embedding only (simplicity)
6. **Neural Reranking** - Future feature if evidence emerges
7. **Query Expansion** - Future feature if evidence emerges

### Why Not

These features either:
- Violate constraints (distributed, external APIs)
- Add complexity without strong evidence (chunking, reranking, expansion)
- Are out of MVP scope (to be revisited in future phases)

---

## Appendix A: Evidence Documentation

### [ANT-2024] Anthropic Contextual Retrieval

**Source:** Anthropic Engineering Blog (September 2024)  
**URL:** https://www.anthropic.com/news/contextual-retrieval  
**Type:** Industry Research - Production Deployment

**Key Findings:**
1. **Semantic Embeddings:** 49% reduction in retrieval failures (baseline → semantic)
2. **Hybrid Search:** 67% reduction (baseline → semantic + BM25)
   - Semantic alone: 51% → 25.7% failure rate
   - Hybrid: 51% → 16.8% failure rate
   - Incremental benefit of BM25: 18% additional improvement

3. **Contextual Retrieval:** 35% additional improvement (prepending context to chunks)
   - Hybrid: 16.8% → 10.9% failure rate
   - Requires LLM to generate context per chunk

**Relevance:** Quantitative evidence from production RAG system at scale. Demonstrates:
- Semantic search provides substantial value alone (49%)
- Hybrid search provides additional value (18% more)
- Contextual retrieval provides incremental value (35% on top of hybrid)

**Limitations:**
- Different corpus and use case than ours
- Their baseline may differ from our substring search
- Results may not generalize exactly to our scale

**Application to Requirements:**
- FR-1 (semantic): MUST based on 49% improvement
- FR-2 (BM25): SHOULD based on 18% additional improvement (Phase 2)
- FF-1 (contextual): Future feature based on 35% improvement (Phase 3)

---

### [ST-2024] Sentence-Transformers all-MiniLM-L6-v2

**Source:** Sentence-Transformers Model Card  
**URL:** https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2  
**Type:** Model Documentation

**Characteristics:**
- **Model Size:** 80.4 MB
- **Dimensions:** 384
- **Performance:** ~2,800 sentences/sec (CPU, hardware-dependent)
- **Quality:** 68.06 on STSb benchmark (semantic textual similarity)
- **Training:** 1B+ sentence pairs

**Relevance:** Validates choice of embedding model balances speed, quality, size.

**Application:**
- TC-1: Specifies all-MiniLM-L6-v2 as embedding model
- NFR-1: Informs latency assumptions (~350 μs/sentence → ~50ms for query)

---

### Evidence Gaps

**Areas Where Evidence is Weak or Missing:**

1. **100ms Latency Target:** User-specified constraint, not validated with benchmarks at our scale
   - Mitigation: RT-1 measures actual latency

2. **Metadata Filtering Benefit:** No quantitative evidence found for impact on retrieval quality
   - Mitigation: Marked as MAY, deferred to future if evidence emerges

3. **Chunking Strategy:** No evidence for optimal chunk size at our document sizes (~500 tokens)
   - Mitigation: Use full-document embedding, revisit if contexts grow larger

4. **Query Expansion:** No quantitative evidence for LLM-based expansion benefit
   - Mitigation: Marked as future feature, requires research (out of MVP scope)

---

## Document Revision History

**v2.0.0 (2024-12-16):** Major revision based on developer critique
- Added Quick Reference section
- Added explicit MVP Scope section
- Moved detailed evidence to appendix
- Reduced research tasks from 9 to 6
- Added evaluation methodology
- Added interface requirements
- Clarified decision ownership (scientist vs developer)
- Removed implementation prescriptions (API signatures, schemas)

**v1.0.0 (2024-12-16):** Initial evidence-based requirements document

---

**End of Requirements Document**

**Next Steps:**
1. Scientist: Execute RT-10 (create evaluation test set)
2. Developer: Execute RT-3 (choose vector database)
3. Developer: Begin Phase 1 implementation
4. Both: Validate quality and performance against acceptance criteria
