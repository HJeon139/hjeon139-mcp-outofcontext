# Core Components

This section defines the primary architectural components, their responsibilities, and interactions.

See [Architectural Decisions](03_architectural_decisions.md) for decisions that shaped these components.

---

## Component Overview

The system consists of the following core components:

1. **Context Manager** - Core orchestration and state management
2. **GC Engine** - Heuristic pruning and reachability analysis
3. **Storage Layer** - In-memory and persistent storage
4. **Tool Registry** - MCP tool registration and dispatch
5. **Analysis Engine** - Context analysis and scoring

---

## Context Manager

**Purpose:** Central orchestration component that coordinates context management operations and maintains server state.

**Responsibilities:**
- Maintain project/task-scoped context state
- Coordinate between GC Engine, Storage Layer, and Analysis Engine
- Manage working set abstraction
- Track context segments and metadata
- Provide unified interface for context operations

**Owns:**
- Project/task registry
- Active context segments (in-memory)
- Working set state
- Task metadata and hierarchies

**Interfaces:**
- `analyze_context(context_descriptors: ContextDescriptors) -> AnalysisResult`
- `get_working_set(project_id: str, task_id: Optional[str]) -> WorkingSet`
- `stash_segments(segment_ids: List[str], project_id: str) -> StashResult`
- `retrieve_stashed(query: str, filters: Dict, project_id: str) -> List[ContextSegment]`

**Dependencies:**
- GC Engine (for pruning analysis)
- Storage Layer (for persistence)
- Analysis Engine (for scoring)

---

## GC Engine

**Purpose:** Implements GC-inspired heuristic pruning to identify segments for removal or stashing.

**Responsibilities:**
- Compute root sets (essential context)
- Perform mark-and-sweep reachability analysis
- Score segments using heuristics (recency, type, refcount, generation)
- Generate pruning recommendations
- Execute incremental GC steps

**Owns:**
- Reference graph (segment relationships)
- GC metadata (generations, refcounts, last-touched times)
- Pruning policies and thresholds

**Interfaces:**
- `analyze_pruning_candidates(segments: List[ContextSegment], roots: Set[str]) -> List[PruningCandidate]`
- `compute_reachability(roots: Set[str], references: Dict) -> Set[str]`
- `score_segment(segment: ContextSegment, now: datetime) -> float`
- `generate_pruning_plan(candidates: List[PruningCandidate], target_tokens: int) -> PruningPlan`

**Dependencies:**
- Context Manager (for segment metadata)
- Storage Layer (for reference tracking)

---

## Storage Layer

**Purpose:** Manages persistent and in-memory storage of context segments and metadata.

**Responsibilities:**
- Store active segments in memory
- Persist stashed segments to JSON file
- Load persisted data on startup
- Provide search and retrieval operations
- Manage storage lifecycle (cleanup, expiration)

**Owns:**
- In-memory segment dictionary
- JSON file persistence
- Metadata indexes (by project, task, file, tag)

**Interfaces:**
- `store_segment(segment: ContextSegment, project_id: str) -> None`
- `load_segments(project_id: str) -> List[ContextSegment]`
- `stash_segment(segment: ContextSegment, project_id: str) -> None`
- `search_stashed(query: str, filters: Dict, project_id: str) -> List[ContextSegment]`
- `delete_segment(segment_id: str, project_id: str) -> None`

**Dependencies:**
- None (low-level storage abstraction)

---

## Tool Registry

**Purpose:** Manages MCP tool registration and dispatches tool calls to appropriate handlers.

**Responsibilities:**
- Register context management tools with MCP server
- Dispatch tool calls to handler functions
- Validate tool parameters using Pydantic schemas
- Handle tool errors and return structured responses
- Provide tool discovery metadata

**Owns:**
- Tool registry (name -> handler mapping)
- Tool schemas and parameter validation
- Error handling logic

**Interfaces:**
- `register_tool(name: str, handler: Callable, schema: ToolSchema) -> None`
- `handle_tool_call(name: str, arguments: Dict) -> ToolResult`
- `list_tools() -> List[ToolMetadata]`

**Dependencies:**
- Context Manager (delegates operations)
- MCP SDK (for protocol integration)

---

## Analysis Engine

**Purpose:** Provides context analysis, scoring, and health metrics.

**Responsibilities:**
- Analyze context usage and health
- Compute context metrics (token counts, segment counts, task distribution)
- Generate context health reports
- Provide recommendations based on analysis

**Owns:**
- Analysis algorithms and scoring functions
- Metrics computation logic

**Interfaces:**
- `analyze_context_usage(segments: List[ContextSegment]) -> UsageMetrics`
- `compute_health_score(segments: List[ContextSegment]) -> HealthScore`
- `generate_recommendations(metrics: UsageMetrics) -> List[Recommendation]`

**Dependencies:**
- Context Manager (for segment data)

---

## Component Interactions

**Data Flow Pattern:**
```
Platform → Tool Registry → Context Manager → [GC Engine | Storage Layer | Analysis Engine]
                                    ↓
                            Storage Layer (persistence)
```

**Communication Patterns:**
- **Synchronous**: Tool calls processed synchronously, return results immediately
- **Stateless Tool Inputs**: Tools receive explicit context descriptors, not direct platform access
- **Stateful Server**: Server maintains project/task-scoped state internally

**Component Boundaries:**
- **Context Manager**: Orchestration only, delegates to specialized engines
- **GC Engine**: Pure pruning logic, no storage or tool concerns
- **Storage Layer**: Pure storage abstraction, no business logic
- **Tool Registry**: Protocol integration only, delegates to Context Manager

---

## References

- [Interfaces and Data Models](09_interfaces.md) - Interface contracts for components
- [Integration Patterns](05_integration_patterns.md) - How components integrate with MCP protocol
- [Design Patterns](06_design_patterns.md) - Patterns applied in component design

