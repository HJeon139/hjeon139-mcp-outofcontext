# Design Patterns

This section documents key design patterns applied in the architecture.

---

## GC-Inspired Pruning Pattern

**Pattern:** Apply garbage collection concepts (roots, reachability, reference counting) to context segments.

**Implementation:**
- **Roots**: Current task, active file, last N messages, pinned segments
- **Mark Phase**: Traverse references from roots to find reachable segments
- **Sweep Phase**: Identify unreachable or low-scoring segments for pruning
- **Scoring**: Combine recency, type, refcount, generation into prune score

**Application:**
- Primary pruning strategy for v1
- Runs incrementally during tool calls
- Full GC when approaching token limits

**References:** See [GC Heuristic Pruning Design](../../v0/research_outcomes/gc_heuristic_pruning_patterns.md)

---

## Human-Memory-Inspired Patterns

**Pattern:** Apply cognitive patterns (working memory, task organization, gist-before-prune) to context management.

**Implementations:**
- **Working Set**: Small set of active segments for current task
- **Task-Centric Organization**: Segments grouped by task_id
- **Gist Creation**: Create summary before pruning large segments
- **Task Snapshots**: Capture state before context switches
- **Tiered Storage**: Working → Recent Stash → Deep Archive

**Application:**
- Overlays on GC/pruning mechanisms
- Makes context management feel natural
- Improves agent understanding of context structure

**References:** See [Human-Memory Patterns Design](../../v0/research_outcomes/human_memory_inspired_context_patterns.md)

---

## Advisory Service Pattern

**Pattern:** Server provides recommendations; platforms apply decisions.

**Implementation:**
- Tools accept context descriptors (not direct platform access)
- Tools return recommendations (not direct context modifications)
- Platforms maintain control over their context windows
- Server maintains separate stashed context storage

**Application:**
- Enables platform-agnostic design
- Simplifies integration (no platform-specific hooks)
- Maintains separation of concerns

**References:** See [Platform Integration Design](../../v0/research_outcomes/architecture_platform_integration.md)

---

## Modular Tool Registry Pattern

**Pattern:** Self-contained tool modules registered dynamically.

**Implementation:**
- Each tool is a module with handler function and schema
- Tools register themselves at startup
- Tools can be enabled/disabled via configuration
- Tools are independent (no cross-tool dependencies)

**Application:**
- Enables feature flags
- Easy to add/remove capabilities
- Aligns with MCP tool-centric architecture

**References:** See [MCP Server Design Patterns](../../v0/research_outcomes/mcp_server_design_patterns.md)

---

## Project/Task-Scoped Memory Pattern

**Pattern:** Context state scoped to projects and tasks, not global.

**Implementation:**
- All segments belong to a project_id
- Segments optionally belong to a task_id
- Storage organized by project
- Working sets are task-scoped

**Application:**
- Prevents cross-project contamination
- Matches human workflow organization
- Enables project-specific context management

**References:** See [MCP Server Design Patterns](../../v0/research_outcomes/mcp_server_design_patterns.md)

---

## Incremental GC Pattern

**Pattern:** Run GC in small steps rather than full sweeps.

**Implementation:**
- Small GC steps on each tool call or every N messages
- Update ages and refcounts incrementally
- Prune small batches when above soft threshold
- Full GC only when approaching hard limits

**Application:**
- Keeps latency small and predictable
- Spreads GC cost over time
- Avoids "stop-the-world" pauses

---

## References

- [GC Heuristic Pruning Design](../../v0/research_outcomes/gc_heuristic_pruning_patterns.md)
- [Human-Memory Patterns Design](../../v0/research_outcomes/human_memory_inspired_context_patterns.md)
- [Platform Integration Design](../../v0/research_outcomes/architecture_platform_integration.md)
- [MCP Server Design Patterns](../../v0/research_outcomes/mcp_server_design_patterns.md)

