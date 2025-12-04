# Constraints and Requirements

This document covers technical constraints, performance requirements, dependency minimization, and requirements coverage.

---

## Technical Constraints

### MCP Protocol Limitations

**Cannot directly inspect or modify LLM context windows:**
- Tools are the only integration surface
- No standard token counting or context introspection APIs
- Must rely on platforms providing context descriptors

### Platform Integration Constraints

**v1 uses advisory mode only:**
- No direct platform integration
- Platforms must implement their own context modification logic
- Server cannot automatically apply pruning decisions

### Storage Constraints

**32k-64k token volumes:**
- Small-medium scale
- In-memory + JSON sufficient, no database required
- Linear search acceptable for retrieval

---

## Performance Requirements

**From Requirements Document:**
- Context analysis: < 2 seconds for 32k-64k token contexts
- Token counting: < 100ms for typical context
- Storage operations: Non-blocking, async where possible
- Keyword search: < 500ms for 32k tokens

**Scalability Considerations:**
- Designed for 32k-64k token volumes
- Linear algorithms acceptable at this scale
- Architecture supports migration to more efficient algorithms if volumes grow

---

## Dependency Minimization

### Required Dependencies (MVP)

- `mcp` - MCP SDK (required for protocol)
- `pydantic` - Data validation (lightweight, industry standard)
- `tiktoken` - Token counting (small, fast, accurate)
- Built-in: `json`, `datetime`, `pathlib`, `typing`

**Total External Dependencies: 3** (minimal footprint)

**Why tiktoken over alternatives:**
- **vs. LangChain tokenizers**: LangChain is a framework, not a lightweight library. We explicitly avoid framework dependencies (see [leveraging_existing_tooling.md](../../v0/research_outcomes/leveraging_existing_tooling.md) D6: "Learn from LangChain Patterns, Don't Import Framework"). LangChain tokenizers would pull in unnecessary framework overhead.
- **vs. sentence-transformers tokenizers**: sentence-transformers is deferred to v2 (only needed for embeddings, not token counting). Its tokenizers are designed for embedding models, not OpenAI models. Adding it just for token counting would be overkill and conflicts with dependency minimization.
- **vs. transformers library**: The `transformers` library is much heavier (~500MB+ with model downloads) and slower for token counting. tiktoken is a pure Python implementation with no model downloads, meeting the < 100ms performance requirement.
- **tiktoken advantages**: Official OpenAI tokenizer (matches what platforms use), lightweight (~1MB), fast (pure Rust implementation), accurate (exact token counts for OpenAI models), well-maintained by OpenAI.

### Explicitly Deferred

- `sentence-transformers` - Embeddings (defer to v2)
- `faiss` / vector DBs - Semantic search (defer to v2)
- `openai` / LLM APIs - Compression (defer to v2)

---

## Requirements Coverage

### Functional Requirements Addressed

- ✅ Context monitoring tools (`context_analyze_usage`)
- ✅ Context pruning tools (`context_gc_*`)
- ✅ Context stashing and retrieval (`context_stash`, `context_search_stashed`)
- ✅ Protected segment management (`context_gc_pin`)
- ✅ Task-centric organization (`context_set_current_task`, task snapshots)
- ✅ Lightweight storage (in-memory + JSON)
- ✅ Keyword-based retrieval (metadata filtering)

### Technical Requirements Addressed

- ✅ MCP protocol implementation (tool-based)
- ✅ Performance targets met (lightweight algorithms)
- ✅ Minimal dependencies (3 external deps)
- ✅ Error handling (structured errors, graceful degradation)
- ✅ Configurable (environment variables, feature flags)

---

## References

- [Requirements Document](../../v0/requirements.md) - Full requirements specification
- [Architectural Decisions](03_architectural_decisions.md) - Decisions based on these constraints

