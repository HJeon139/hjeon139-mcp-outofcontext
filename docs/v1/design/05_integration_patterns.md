# Integration Patterns

This section specifies how the server integrates with MCP protocol and agent platforms.

See [Components](04_components.md) for component specifications that enable these integration patterns.

---

## MCP Protocol Integration

**Tool-Based Architecture:**
All functionality is exposed through MCP tools following the MCP specification. Tools accept structured parameters and return structured results.

**Tool Categories:**

1. **Monitoring Tools:**
   - `context_analyze_usage` - Analyze current context usage and health
   - `context_get_working_set` - Get current working set segments

2. **Pruning Tools:**
   - `context_gc_analyze` - Analyze pruning candidates using GC heuristics
   - `context_gc_prune` - Execute pruning plan (stash or delete segments)
   - `context_gc_pin` / `context_gc_unpin` - Manage protected segments

3. **Stashing Tools:**
   - `context_stash` - Move segments from active to stashed storage
   - `context_search_stashed` - Search stashed context by keyword/metadata
   - `context_retrieve_stashed` - Retrieve stashed segments for active context

4. **Management Tools:**
   - `context_create_task_snapshot` - Create task snapshot before context switch
   - `context_get_task_context` - Get context for specific task
   - `context_set_current_task` - Set active task ID

**Tool Interface Pattern:**
```python
@mcp_tool("context_analyze_usage")
def analyze_usage(
    context_descriptors: ContextDescriptors,  # Platform provides this
    project_id: str,
    task_id: Optional[str] = None
) -> UsageAnalysis:
    """Analyze context usage and return metrics and recommendations."""
    pass
```

**Resource Patterns (Optional):**
- Stashed segments could be exposed as MCP resources for browsing
- Task snapshots could be resources for retrieval
- Deferred to v2 if needed

---

## Platform Integration (Advisory Mode)

**Integration Pattern: Advisory Service**

The server operates in advisory mode: platforms call tools with context metadata, server analyzes and returns recommendations, platforms apply changes to their own context.

**Platform Responsibilities:**
- Track their own context (messages, files, token counts)
- Call MCP tools with context descriptors
- Apply server recommendations to their context
- Manage their own context window building

**Server Responsibilities:**
- Analyze provided context descriptors
- Maintain stashed context storage
- Provide pruning/stashing recommendations
- Track project/task-scoped state

**Context Descriptor Format:**
```python
@dataclass
class ContextDescriptors:
    recent_messages: List[Message]  # Last N messages
    current_file: Optional[FileInfo]  # Active file and location
    token_usage: TokenUsage  # Current token counts
    segment_summaries: List[SegmentSummary]  # High-level segment info
    task_info: Optional[TaskInfo]  # Current task metadata
```

**Recommendation Format:**
```python
@dataclass
class PruningRecommendation:
    segment_ids: List[str]  # Segments to prune
    action: Literal["stash", "delete"]  # What to do
    reason: str  # Why (e.g., "old + low refcount")
    tokens_freed: int  # Estimated tokens saved
```

---

## Agent Interaction Patterns

**Proactive Usage:**
- Agents discover tools through MCP tool discovery
- Tool descriptions explain context management problem
- Agents call tools proactively before hitting limits

**Tool Discovery:**
- Tools named clearly: `context_*` prefix
- Descriptions explain when and why to use
- Examples in tool descriptions show proactive usage

**Workflow Pattern:**
1. Agent calls `context_analyze_usage` periodically
2. If usage high, agent calls `context_gc_analyze`
3. Agent reviews candidates, calls `context_gc_prune`
4. Agent can `context_stash` segments for later
5. Agent can `context_search_stashed` when needed

**Error Handling:**
- Tools return structured errors
- Partial failures reported clearly
- Graceful degradation if operations fail

---

## Integration Flow

**Standard Workflow:**
```
1. Platform builds context from conversation, files, code
2. Platform calls MCP tool (e.g., context_analyze_usage) with context descriptors
3. Server analyzes context using GC Engine and Analysis Engine
4. Server returns recommendations (pruning candidates, health metrics)
5. Platform applies recommendations to its context window
6. Platform sends updated context to LLM
```

**Tool Call Example:**
```python
# Platform side
context_descriptors = ContextDescriptors(
    recent_messages=last_10_messages,
    current_file=active_file_info,
    token_usage=TokenUsage(current=25000, limit=32000),
    segment_summaries=segment_metadata,
    task_info=current_task
)

result = mcp_client.call_tool(
    "context_analyze_usage",
    {
        "context_descriptors": context_descriptors,
        "project_id": "project_123",
        "task_id": "task_456"
    }
)

# Server returns UsageAnalysis with:
# - current_tokens: 25000
# - usage_percent: 78
# - recommendations: ["Consider pruning old debug logs", ...]
# - pruning_candidates: [...]
```

---

## References

- [Architectural Decisions](03_architectural_decisions.md) - Decision to use advisory mode
- [Interfaces and Data Models](09_interfaces.md) - Tool interface contracts
- [Components](04_components.md) - Component specifications

