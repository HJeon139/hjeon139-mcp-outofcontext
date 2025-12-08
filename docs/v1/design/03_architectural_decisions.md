# Architectural Decisions

This document documents key architectural decisions made after evaluating competing approaches from research.

See [Research Findings](02_research_findings.md) for the research that informed these decisions.

---

## Decision Area 1: Pruning Strategy

**Competing Approaches:**
1. GC-inspired heuristic pruning (lightweight, no ML)
2. Attention/embedding-based semantic pruning (RAG patterns)
3. Hybrid approach combining both

**Decision: Primary Strategy - GC-Inspired Heuristic Pruning**

**Rationale:**
- Aligns with lightweight dependency requirements (no embeddings, no vector DBs)
- Proven effectiveness for millions of token volumes
- Explainable decisions (agents can understand why segments were pruned)
- Fast execution (< 2s for analysis)
- Addresses the core requirement of identifying unused/irrelevant context

**Deferred:**
- Semantic embeddings for relevance scoring (v2 if keyword search insufficient)
- Vector database for similarity search (v2 for advanced retrieval)

**When Alternative Strategies Apply:**
- Semantic search deferred to v2 if keyword/metadata search proves insufficient in practice
- Hybrid approach can be added incrementally without refactoring core GC engine

---

## Decision Area 2: Storage Strategy

**Competing Approaches:**
1. In-memory + JSON file (lightweight)
2. Vector database for stashed context
3. SQLite for structured metadata

**Decision: Primary Strategy - In-Memory + JSON File Persistence**

**Rationale:**
- Meets millions of token volume requirement without database overhead
- Zero external dependencies for storage
- Fast enough for large volumes (linear search acceptable)
- Human-readable format for debugging
- Simple backup and recovery

**Storage Architecture:**
- **Active segments**: In-memory dictionary (`Dict[str, ContextSegment]`)
- **Stashed segments**: JSON file with metadata
- **Structure**: Single JSON file with segments array, metadata, and indexes
- **Persistence**: Write on stash, load on startup

**Deferred:**
- SQLite for structured queries (v2 if JSON becomes unwieldy)
- Vector database for semantic search (v2 if keyword search insufficient)

**Migration Path:**
- JSON structure designed to be easily migrated to SQLite if needed
- Vector indexing can be added as optional layer without changing core storage

---

## Decision Area 3: Compression Strategy

**Competing Approaches:**
1. LLM-driven compression (preserves recency)
2. Summarization (loses nuance)
3. Hybrid: compress some, summarize others

**Decision: Optional LLM-Driven Compression (Deferred for MVP)**

**Rationale:**
- LLM-driven compression is superior to summarization (preserves recency/metadata)
- However, adds complexity and LLM API dependency
- Core problem can be solved with pruning + stashing for MVP
- Can be added incrementally without refactoring

**Deferred to v2:**
- LLM-driven compression tool
- Automatic compression workflows
- Compression quality validation

**MVP Approach:**
- Focus on pruning and stashing
- Platforms can manually summarize if needed
- Compression can be added as optional tool in v2

---

## Decision Area 4: Platform Integration

**Competing Approaches:**
1. Extension/plugin architecture
2. API/webhook integration
3. File system monitoring
4. Hybrid approach

**Decision: Advisory Mode via MCP Tools (v1), Defer Platform Adapters**

**Rationale:**
- Minimize platform-specific code for v1
- MCP tools provide standard interface across platforms
- Platforms call tools with context metadata, server returns recommendations
- Simpler integration, works immediately across all MCP platforms
- Platform adapters can be added incrementally for deeper integration

**v1 Approach:**
- **Advisory Mode**: Server receives context descriptors via tool parameters
- **Tool-Based**: All operations exposed via MCP tools
- **Stateless Inputs**: Tools accept explicit context metadata (messages, token counts, file info)
- **Recommendations**: Server returns pruning/stashing recommendations
- **Platform Applies**: Platforms implement their own context modification logic

**Deferred to v2:**
- Platform-specific adapters (Cursor, Claude Desktop)
- Direct platform integration hooks
- Real-time context monitoring
- Automatic context modification

**Integration Pattern:**
```
Platform → Calls MCP Tool with Context Metadata → Server Analyzes → Returns Recommendations → Platform Applies Changes
```

---

## Decision Area 5: Retrieval Strategy

**Competing Approaches:**
1. Keyword/text matching (lightweight)
2. Semantic similarity search (embeddings + vector DB)
3. Metadata-based filtering

**Decision: Primary Strategy - Keyword + Metadata Filtering**

**Rationale:**
- Sufficient for millions of token volumes
- Zero ML dependencies
- Fast execution (< 500ms per search)
- Simple implementation and debugging
- Meets requirements for MVP

**Retrieval Architecture:**
- **Keyword Search**: Simple text matching (case-insensitive, substring)
- **Metadata Filters**: File path, task ID, tags, time range, segment type
- **Combined Scoring**: Keyword matches + metadata relevance + recency
- **Linear Search**: Acceptable performance for stashed context volumes

**Deferred to v2:**
- Semantic embeddings for similarity search
- Vector database for efficient retrieval
- Query expansion and relevance feedback

**When to Add Semantic Search:**
- Only if keyword search proves insufficient in real-world use
- When stashed context volumes grow significantly (>100k tokens)
- If user feedback indicates poor retrieval quality

---

## Decision Summary

| Decision Area | v1 Choice | Deferred to v2 |
|--------------|-----------|----------------|
| **Pruning** | GC-inspired heuristics | Semantic embeddings, hybrid approaches |
| **Storage** | In-memory + JSON | SQLite, vector databases |
| **Compression** | None (deferred) | LLM-driven compression |
| **Platform Integration** | Advisory mode (MCP tools) | Platform-specific adapters |
| **Retrieval** | Keyword + metadata | Semantic search, vector DB |

All decisions prioritize lightweight implementation and minimal dependencies for v1, while maintaining extensibility for future enhancements.

---

## References

- [Research Findings](02_research_findings.md) - Research that informed these decisions
- [GC Heuristic Pruning Design](../../v0/research_outcomes/gc_heuristic_pruning_patterns.md)
- [RAG Patterns Design](../../v0/research_outcomes/rag_patterns_context_management.md)
- [Platform Integration Design](../../v0/research_outcomes/architecture_platform_integration.md)

