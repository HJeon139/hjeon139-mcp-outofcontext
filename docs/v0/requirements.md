# Context Management MCP Server Requirements

## Context

* This is an MCP (Model Context Protocol) server designed to help AI agents manage their session context
* The server provides tools for agents to proactively manage context, preventing context overflow and maintaining continuity across sessions
* The server must work with agents running in environments like Cursor, Claude Desktop, and other MCP-compatible clients
* The server will be packaged as a Python library following Hatch project standards

### Problem Statement

AI agents experience a "context lifecycle problem":

1. **Agent performs work** - debugging, implementing features, analyzing code
2. **Context fills up** - debugging sessions generate logs, error traces, code snippets, and conversation history
3. **Context limit reached** - agent hits token/context window limits
4. **Reset required** - user must start a new session, losing context continuity
5. **Context summarization attempted** - agent tries to summarize, but summaries lose nuance and alignment
6. **Re-alignment overhead** - user must re-explain current state and what was being worked on

This creates friction and breaks the flow of productive work. Unlike human intelligence, which naturally focuses on relevant information and discards details after moving on, AI agents accumulate all context indiscriminately.

### The Vision

An MCP server that enables agents to manage context more like human intelligence:

* **Selective focus** - Identify and retain important context tokens while removing less critical details
* **Dynamic pruning** - Remove or stash context that's no longer relevant to the current task
* **Continuity** - Maintain session continuity without hitting context limits
* **Proactive management** - Agent can proactively manage context before hitting limits

**Ideal outcome**: Session context never runs out through intelligent context management.

### Tools & Dependencies

* [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) - Protocol specification and SDK
* [Hatch](https://hatch.pypa.io/latest/) - Python project management and packaging
* [Pydantic](https://docs.pydantic.dev/) - Data validation and serialization for MCP tool schemas
* Token counting: `tiktoken` (lightweight, fast, accurate)
* Storage: JSON file or in-memory (lightweight for 32k-64k token volumes)
* Embedding model (optional): Only if needed for semantic search; prioritize simple text matching first

### Key References

* Research documents in `docs/research/` will explore:
  - MCP protocol capabilities and limitations
  - Agent awareness mechanisms for context limits
  - Existing solutions and competitive landscape
  - Garbage collection patterns for context management
  - Transformer-style attention pruning approaches
  - Context summarization and compression techniques
  - Human memory models for inspiration

## Functional Requirements

### Core Context Management

1. **WHEN** an agent wants to check context usage, the server **MUST** provide a tool to query current context statistics (token count, percentage used, estimated remaining capacity)

2. **WHEN** an agent wants to remove context, the server **MUST** provide a tool to:
   - Identify context segments that are low relevance to current task
   - Archive/stash context segments for later retrieval
   - Permanently remove context segments that are no longer needed

3. **WHEN** an agent wants to preserve important context, the server **MUST** provide a tool to:
   - Mark context segments as "high priority" or "essential"
   - Protect marked segments from pruning/removal
   - Extract and store key information for later reference

4. **WHEN** an agent wants to retrieve stashed context, the server **MUST** provide a tool to:
   - Search stashed context by keywords/text matching (primary approach)
   - Retrieve specific archived context segments by ID or metadata
   - Merge retrieved context back into active session
   - **Semantic similarity search is optional** (only if keyword search insufficient)

5. **WHEN** context approaches limits, the server **MUST** provide proactive suggestions/notifications to the agent about what can be pruned

### Context Analysis & Pruning

6. **WHEN** analyzing context for pruning, the server **SHOULD**:
   - Start with simple heuristics (recent vs. old, keyword matching, metadata filters)
   - Use LLM-driven compression for intelligent paraphrasing (preserve recency)
   - Consider temporal factors (recent context vs. older context)
   - Respect user-defined priorities and protected segments
   - **Only add semantic embeddings if simple heuristics prove insufficient**

7. The server **SHOULD** support simple pruning strategies (prioritize lightweight):
   - Temporal pruning (remove old context beyond threshold)
   - Keyword-based relevance (simple text matching)
   - Metadata-based filtering (type, tags, time range)
   - LLM-driven compression (paraphrase verbose segments)
   - **Defer complex strategies** (semantic clustering, attention-based) until proven necessary

8. **WHEN** pruning context, the server **MUST** preserve essential context including:
   - Current task/goal state
   - Recent decisions and rationale
   - Active code/file context
   - Protected user-specified segments

### Context Storage & Retrieval

9. The server **MUST** maintain a lightweight storage layer for stashed/archived context segments:
   - **Primary**: In-memory storage with optional JSON file persistence
   - **Rationale**: For 32k-64k token volumes, full database systems are overkill
   - Store: Stashed segments, basic metadata (timestamp, type, tags)
   - **Avoid**: Heavy databases (SQL, vector DBs) unless volumes grow significantly

10. **WHEN** storing context, the server **SHOULD**:
    - Store metadata (timestamp, source, type, tags)
    - Use simple text matching for retrieval (keyword search)
    - Only add embeddings/vector search if simple matching proves insufficient
    - Keep storage format simple (JSON files, in-memory dicts)

11. The server **SHOULD** support querying stored context by:
    - Exact match or keyword search (primary approach)
    - Metadata filters (time range, type, tags)
    - Semantic similarity (only if keyword search is insufficient for use cases)

### MCP Protocol Integration

12. The server **MUST** expose all functionality through MCP tools that follow the MCP specification

13. **WHEN** an agent queries for available tools, the server **MUST** provide clear descriptions that encourage context management:
    - Tool descriptions should explain the context management problem
    - Tool names should be intuitive and discoverable
    - Tools should be organized by category (monitoring, pruning, retrieval, etc.)

14. The server **MUST** support both synchronous and asynchronous tool execution where appropriate

15. **WHEN** tools are called, the server **MUST** provide clear feedback about:
    - What context was affected
    - Estimated impact on context usage
    - Recommendations for next steps

### Agent Awareness & Proactive Management

16. The server **SHOULD** provide mechanisms for agents to become aware of context limits:
    - Context usage monitoring tool
    - Warnings when approaching limits
    - Suggestions for proactive pruning

17. **WHEN** an agent is unaware of context limits, the server **SHOULD** still function correctly (graceful degradation)

18. The server **MUST** support both proactive (agent-initiated) and reactive (threshold-triggered) context management

## Technical Constraints

1. The server **MUST** be packaged using Hatch and follow project standards:
   - pytest for unit/integration tests
   - ruff for linting
   - mypy for type checking
   - 80% target test coverage

2. The server **MUST** implement the MCP protocol specification correctly

3. The server **MUST** be performant:
   - Context analysis operations should complete in < 2 seconds for 32k-64k token contexts
   - Token counting should be fast (< 100ms for typical context)
   - Storage operations should not block tool execution
   - Simple keyword search should be fast enough (< 500ms for 32k tokens)

4. The server **MUST** handle errors gracefully:
   - Invalid tool parameters should return clear error messages
   - Storage failures should not crash the server
   - Partial failures should be reported clearly
   - Graceful degradation if optional features unavailable

5. The server **SHOULD** be configurable (but start simple):
   - Pruning strategies should be configurable (start with simple temporal/keyword)
   - Storage location configurable (JSON file path)
   - Advanced features (embeddings, vector DB) optional and configurable if added

6. The server **MUST** maintain data consistency:
   - Context operations should be atomic where possible
   - Stored context should be recoverable after server restart (via JSON file persistence)
   - Relationships between context segments should be preserved (simple references)

7. The server **MUST** prioritize lightweight solutions:
   - Minimize dependencies (avoid heavy libraries when simple alternatives exist)
   - Use built-in Python libraries where possible (json, sqlite3, pathlib)
   - Only add complex dependencies (vector DBs, embedding models) if proven necessary
   - Design for 32k-64k token volumes (optimize for small-medium context sizes)

## Non-Goals

1. **NOT** a replacement for the agent's native context management - this is a complementary tool
2. **NOT** a general-purpose memory system - focused specifically on session context management
3. **NOT** a code generation tool - context management only, not task execution
4. **NOT** responsible for agent-to-agent communication - single agent focus
5. **NOT** a solution for all context problems - focuses on the overflow and continuity problem
6. **NOT** a replacement for context summarization - may use summarization but not the primary approach
7. **NOT** handling file system or codebase operations directly - works with context strings/segments

## Design Constraints & Cost-Benefit Analysis

### Token Volume Assumptions

**Expected Context Sizes**: 32k-64k tokens total
- Typical session: 20k-40k tokens
- Stashed context: 10k-20k tokens
- **Implication**: Solutions designed for millions of tokens are overkill

**Scale Considerations**:
- Small enough for in-memory processing
- Simple file-based persistence sufficient
- No need for distributed systems
- Linear search acceptable for retrieval

### Dependency Minimization Principle

**Principle**: Only add dependencies when cost (complexity, size, maintenance) < benefit (functionality, performance)

**Decision Framework**:
1. **Can we use built-in Python?** (json, sqlite3, pathlib) → Prefer this
2. **Is it a small, focused library?** (tiktoken) → Consider including
3. **Is it a large framework/library?** (FAISS, sentence-transformers) → Defer, only add if proven necessary
4. **Does it solve a real problem at our scale?** → Test with simple solution first

### Cost-Benefit Analysis by Component

#### Storage Solutions

| Solution | Cost | Benefit at 32k-64k | Decision |
|----------|------|-------------------|----------|
| **In-memory dict** | Very Low | High (fast, simple) | ✅ **MVP** |
| **JSON file** | Very Low | High (persistence, no deps) | ✅ **MVP** |
| **SQLite** | Low | Medium (structured queries) | ❌ **DEFER** - JSON sufficient |
| **PostgreSQL/MySQL** | High | Low (overkill for volume) | ❌ **AVOID** |
| **Vector DB (FAISS)** | High | Low-Medium (unnecessary for small volume) | ❌ **DEFER** - Start simple |
| **Vector DB (Qdrant)** | Very High | Low (overkill) | ❌ **AVOID** |

**Rationale**: For 32k-64k tokens, in-memory + JSON files are sufficient. Vector DBs add significant complexity for minimal benefit.

#### Retrieval Solutions

| Solution | Cost | Benefit | Decision |
|----------|------|---------|----------|
| **Keyword/text matching** | Very Low | High (works for most cases) | ✅ **MVP** |
| **Metadata filtering** | Very Low | High (simple, effective) | ✅ **MVP** |
| **Semantic embeddings** | High (large model) | Medium (better matching) | ❌ **DEFER** - Test keyword first |
| **Vector similarity search** | High (DB + model) | Medium | ❌ **DEFER** - Only if keyword insufficient |

**Rationale**: Keyword matching is sufficient for 32k tokens. Semantic search can be added later if needed.

#### Embedding Solutions

| Solution | Cost | Benefit | Decision |
|----------|------|---------|----------|
| **No embeddings (keyword only)** | None | High (simplicity) | ✅ **MVP** |
| **Sentence Transformers** | High (80-420MB models) | Medium | ❌ **DEFER** - Add only if proven necessary |
| **OpenAI Embeddings API** | Medium (API costs) | High (quality) | ❌ **DEFER** - Costs accumulate |

**Rationale**: Start without embeddings. Only add if keyword search proves insufficient in real use.

### Simplified MVP Storage Strategy

**Approach for 32k-64k tokens**:

```python
# In-memory storage (fast, simple)
stashed_context: Dict[str, ContextSegment] = {}

# JSON file persistence (lightweight)
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

# Simple retrieval
def search_stashed(query: str) -> List[ContextSegment]:
    # Keyword matching in text
    # Metadata filtering
    # Simple linear search (fast enough for 32k tokens)
    return [seg for seg in stashed_context.values() 
            if query.lower() in seg.text.lower() 
            or matches_metadata(seg, filters)]
```

**Benefits**:
- Zero external dependencies for storage
- Fast enough for small volumes
- Human-readable (JSON)
- Easy to debug and maintain

### Dependency Decisions

**✅ Include (MVP)**:
- `mcp` - MCP SDK (required for protocol)
- `pydantic` - Data validation (industry standard, lightweight)
- `tiktoken` - Token counting (small, fast, accurate)
- Built-in: `json`, `sqlite3`, `pathlib`, `datetime`

**❌ Defer (Only if Needed)**:
- `sentence-transformers` - Embeddings (large, only if keyword search insufficient)
- `faiss-cpu` - Vector DB (complex, only if volumes grow significantly)
- `chromadb` - Vector DB (only if needed)
- `openai` - Embeddings API (only if local embeddings insufficient)

**❌ Avoid**:
- Heavy databases (PostgreSQL, MySQL)
- Large ML frameworks (PyTorch, TensorFlow) unless absolutely needed
- Complex orchestration systems

### Feature Prioritization

**Must Have (MVP)** - Solve core problem:
- Token counting and monitoring (tiktoken)
- Simple context pruning (remove by ID, keywords, metadata)
- Lightweight storage (in-memory + JSON file)
- Keyword-based retrieval
- LLM-driven compression (preserve recency)

**Should Have (Phase 2)** - Enhance usability:
- Metadata-based filtering
- Temporal pruning heuristics
- Protected segment management
- Simple relevance scoring

**Nice to Have (Phase 3)** - Only if proven necessary:
- Embedding-based semantic search
- Vector database storage
- Advanced compression strategies

### Complexity vs. Value Trade-offs

**Principle**: Start simple, add complexity only when needed.

**Simple First Approach**:
1. **Storage**: Start with JSON files, only add DB if JSON becomes unwieldy
2. **Retrieval**: Start with keyword search, only add embeddings if insufficient
3. **Analysis**: Start with simple heuristics, only add ML if needed
4. **Compression**: Start with LLM-driven paraphrasing, defer automatic summarization

**Validation Threshold**:
- Add complexity only when:
  - Simple solution doesn't meet user needs
  - Performance becomes a bottleneck
  - Volumes grow significantly (>100k tokens)

### Estimated Dependencies (MVP)

**Minimal Dependencies**:
```toml
[project.dependencies]
mcp = ">=1.0.0"           # MCP protocol (required)
pydantic = ">=2.0.0"      # Data validation (lightweight)
tiktoken = ">=0.5.0"      # Token counting (small, fast)
# json - built-in
# sqlite3 - built-in (optional, for metadata if needed)
```

**Total External Dependencies**: 3 (minimal footprint)

**Future Optional Dependencies**:
- Embedding models (only if keyword search insufficient)
- Vector DBs (only if volumes grow)
- Compression libraries (only if LLM compression insufficient)

## Open Questions (To be resolved in research phase)

1. How does MCP protocol support context management? What interfaces are available?
2. Do agents know when they're approaching context limits? What mechanisms exist?
3. What existing solutions address this problem? What's the competitive landscape?
4. **Is keyword/text matching sufficient for retrieval, or do we need semantic search?**
5. **What's the simplest storage solution that meets our needs?**
6. How do we balance context retention vs. removal? What heuristics work best?
7. Should the server be passive (tool-based) or active (proactive notifications)?
8. **What's the minimum viable feature set that solves the core problem?**

## Success Criteria

* An agent can successfully manage context to avoid overflow
* Context continuity is maintained across long-running sessions
* Pruned context can be retrieved when needed (high recall)
* Pruning decisions preserve important context (high precision)
* Tools are discoverable and usable by agents
* Server performance meets technical constraints

