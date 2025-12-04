# Deferred Features

Features and approaches deferred to v2 with rationale.

---

## Semantic Search and Vector Databases

**Deferred:** Embedding-based semantic similarity search, vector databases (FAISS, Qdrant)

**Rationale:**
- Keyword + metadata search sufficient for 32k-64k token volumes
- Adds significant complexity and dependencies
- Can be added incrementally without refactoring core architecture
- Should only be added if keyword search proves insufficient

**When to Revisit:**
- User feedback indicates poor retrieval quality
- Stashed context volumes grow significantly (>100k tokens)
- Keyword search cannot find relevant context in real-world use

---

## LLM-Driven Compression

**Deferred:** LLM-driven compression tool, automatic compression workflows

**Rationale:**
- Core problem solvable with pruning + stashing for MVP
- Adds LLM API dependency and complexity
- Compression quality validation requires additional work
- Can be added as optional tool in v2

**When to Revisit:**
- Pruning + stashing insufficient for context management
- User feedback requests compression capabilities
- Performance analysis shows compression would significantly help

---

## Platform-Specific Adapters

**Deferred:** Direct platform integration (Cursor adapter, Claude Desktop adapter, VS Code extension)

**Rationale:**
- Advisory mode via MCP tools works across all platforms immediately
- Platform adapters require platform-specific code and maintenance
- Minimizes dependencies and complexity for v1
- Can be added incrementally per platform

**When to Revisit:**
- User feedback requests deeper platform integration
- Specific platforms show high adoption
- Features require direct platform access (e.g., real-time monitoring)

---

## Advanced GC Strategies

**Deferred:** Advanced GC algorithms (generational collection optimizations, incremental GC with background threads)

**Rationale:**
- Simple mark-and-sweep sufficient for 32k-64k tokens
- Advanced optimizations not needed at current scale
- Can be added when performance becomes bottleneck

---

## Multi-Strategy Hybrid Approaches

**Deferred:** Automatic hybrid pruning (GC + semantic scoring combined automatically)

**Rationale:**
- Start with single strategy (GC heuristics)
- Hybrid approaches add complexity
- Can be added incrementally
- Should be data-driven (add when single strategy insufficient)

---

## Resource-Based Context Exposure

**Deferred:** MCP resources for browsing stashed context, task snapshots

**Rationale:**
- Tools provide sufficient functionality for v1
- Resources add protocol complexity
- Can be added if tool-based access proves limiting

---

## Documentation Location

Future features documented for v2 consideration in research documents, can be formalized in `docs/v2/research/` if needed.

---

## References

- [Architectural Decisions](03_architectural_decisions.md) - Decisions that led to these deferrals
- [Research Findings](02_research_findings.md) - Research that supports these approaches

