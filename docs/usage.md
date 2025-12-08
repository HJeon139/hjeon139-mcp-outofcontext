# Usage Guide

This guide explains how to use the Out of Context MCP server to manage large context windows in AI agent platforms.

---

## Overview

The Out of Context server helps AI agents manage context that exceeds token limits by:

- **Analyzing context usage** - Monitor token counts, segment distribution, and health
- **Pruning context** - Identify and remove old or unused segments using garbage collection heuristics
- **Stashing context** - Archive segments for later retrieval
- **Task management** - Organize context by tasks and switch between them

### When to Use

Use this server when:

- Your context window approaches token limits (60%+ usage)
- You need to manage context across multiple tasks or sessions
- You want to preserve important context while freeing space
- You're working with long debugging sessions or multi-file refactoring

### Key Concepts

- **Segments**: Individual pieces of context (messages, code, logs, etc.)
- **Working Set**: Active segments currently in use
- **Stashed Storage**: Archived segments that can be retrieved later
- **Projects**: Isolated context spaces (typically one per codebase)
- **Tasks**: Sub-divisions within a project for organizing work

---

## Tool Reference

### Monitoring Tools

#### `context_analyze_usage`

Analyze current context usage and return metrics, health score, and recommendations.

**Parameters:**
- `project_id` (required): Project identifier
- `context_descriptors` (optional): Context metadata from platform (JSON string or dict)
- `task_id` (optional): Task identifier
- `token_limit` (optional): Token limit (default: from config, typically 1 million)

**Returns:**
- `usage_metrics`: Token counts, segment counts, distribution by type/task
- `health_score`: Health score (0-100, higher = healthier)
- `recommendations`: List of recommendations for context management
- `warnings`: Threshold-based warnings (60%, 80%, 90%)
- `suggested_actions`: Suggested tools to call
- `impact_summary`: Estimated impact of pruning
- `pruning_candidates_count`: Number of segments that could be pruned

**Example:**
```json
{
  "project_id": "my-project",
  "token_limit": 1000000
}
```

**When to use:**
- Periodically to monitor context usage
- Before hitting token limits
- After making significant context changes
- When usage > 60% to get recommendations

#### `context_get_working_set`

Get current working set segments for the active task.

**Parameters:**
- `project_id` (required): Project identifier
- `task_id` (optional): Task identifier (uses current task if not provided)

**Returns:**
- `working_set`: Working set metadata
- `segments`: List of active segments
- `total_tokens`: Total token count
- `segment_count`: Number of segments

**Example:**
```json
{
  "project_id": "my-project"
}
```

**When to use:**
- To see what segments are currently active
- Before stashing to identify candidates
- To inspect segment metadata

---

### Pruning Tools

#### `context_gc_analyze`

Analyze context and identify pruning candidates using GC heuristics.

**Parameters:**
- `project_id` (required): Project identifier
- `context_descriptors` (optional): Context metadata from platform
- `task_id` (optional): Task identifier
- `target_tokens` (optional): Target tokens to free (generates pruning plan if provided)

**Returns:**
- `pruning_candidates`: List of candidates with scores and reasons
- `total_candidates`: Total number of candidates
- `estimated_tokens_freed`: Estimated tokens that could be freed
- `pruning_plan`: Pruning plan (if target_tokens provided)

**Example:**
```json
{
  "project_id": "my-project",
  "target_tokens": 100000
}
```

**When to use:**
- When usage is high (>80%) and you need to free space
- Before pruning to review candidates
- To generate a pruning plan for a specific token target

#### `context_gc_prune`

Execute pruning plan to free context space.

**Parameters:**
- `project_id` (required): Project identifier
- `segment_ids` (required): List of segment IDs to prune
- `action` (required): "stash" or "delete"
- `confirm` (optional): Must be `true` for delete actions

**Returns:**
- `pruned_segments`: List of segment IDs that were pruned
- `tokens_freed`: Total tokens freed
- `action`: Action taken ("stashed" or "deleted")
- `errors`: Any errors encountered

**Example:**
```json
{
  "project_id": "my-project",
  "segment_ids": ["seg1", "seg2"],
  "action": "stash"
}
```

**When to use:**
- After analyzing candidates with `context_gc_analyze`
- To free space by stashing or deleting segments
- **Note:** Pinned segments cannot be pruned

#### `context_gc_pin`

Pin segments to protect them from pruning.

**Parameters:**
- `project_id` (required): Project identifier
- `segment_ids` (required): List of segment IDs to pin

**Returns:**
- `pinned_segments`: List of segment IDs that were pinned
- `errors`: Any errors encountered

**Example:**
```json
{
  "project_id": "my-project",
  "segment_ids": ["seg1", "seg2"]
}
```

**When to use:**
- To protect important segments from being pruned
- Before running automatic pruning operations

#### `context_gc_unpin`

Unpin segments to allow pruning.

**Parameters:**
- `project_id` (required): Project identifier
- `segment_ids` (required): List of segment IDs to unpin

**Returns:**
- `unpinned_segments`: List of segment IDs that were unpinned
- `errors`: Any errors encountered

**Example:**
```json
{
  "project_id": "my-project",
  "segment_ids": ["seg1", "seg2"]
}
```

**When to use:**
- To allow previously pinned segments to be pruned
- When segments are no longer critical

---

### Stashing Tools

#### `context_stash`

Move segments from active context to stashed storage by filtering.

**Parameters:**
- `project_id` (optional): Project identifier (defaults to 'default', avoid when possible)
- `query` (optional): Keyword to match segment text
- `filters` (optional): Metadata filters (dict or JSON string):
  - `file_path`: File path filter
  - `task_id`: Task ID filter
  - `tags`: List of tags
  - `type`: Segment type ("message", "code", "log", "note", "decision", "summary")
  - `created_after`: ISO datetime string
  - `created_before`: ISO datetime string

**Returns:**
- `stashed_segments`: List of segment IDs that were stashed
- `tokens_stashed`: Total tokens stashed
- `segments_matched`: Number of segments that matched criteria
- `errors`: Any errors encountered

**Example:**
```json
{
  "query": "old documentation",
  "filters": {
    "type": "note",
    "created_before": "2024-01-01T00:00:00Z"
  }
}
```

**When to use:**
- When context usage is high (>80%) and you need to free space
- To archive old or unused segments
- To stash segments matching specific criteria
- **Note:** Only stashes segments from active/working tier

#### `context_search_stashed`

Search stashed segments by keyword and metadata filters (read-only).

**Parameters:**
- `project_id` (optional): Project identifier (omit to search all projects)
- `query` (optional): Keyword search in segment text
- `filters` (optional): Metadata filters (same as `context_stash`)
- `limit` (optional): Maximum results (default: 50)

**Returns:**
- `segments`: List of matching segments
- `total_matches`: Total number of matches
- `query`: Query that was used
- `filters_applied`: Filters that were applied

**Example:**
```json
{
  "query": "function",
  "filters": {
    "file_path": "src/main.py"
  },
  "limit": 20
}
```

**When to use:**
- To explore what's in stashed storage
- To find segments before retrieving them
- To search across multiple projects

#### `context_retrieve_stashed`

Retrieve stashed segments by searching with query and filters.

**Parameters:**
- `project_id` (optional): Project identifier (defaults to 'default')
- `query` (optional): Keyword to match segment text
- `filters` (optional): Metadata filters (same as `context_stash`)
- `move_to_active` (optional): If `true`, restore segments to active context (default: `false`)

**Returns:**
- `retrieved_segments`: List of retrieved segments (full details)
- `moved_to_active`: List of segment IDs moved to active (if `move_to_active=true`)
- `segments_found`: Number of segments found

**Example:**
```json
{
  "query": "launch bugs",
  "move_to_active": true
}
```

**When to use:**
- To access previously stashed context
- To restore segments back to active context
- After searching with `context_search_stashed`

#### `context_list_projects`

List all available project IDs from stashed storage.

**Parameters:** None

**Returns:**
- `projects`: List of project IDs with stashed context

**Example:**
```json
{}
```

**When to use:**
- To discover available projects
- To search across multiple projects

---

### Task Management Tools

#### `context_set_current_task`

Set the active task ID for a project.

**Parameters:**
- `project_id` (required): Project identifier
- `task_id` (optional): Task identifier (set to `null` to clear current task)

**Returns:**
- `project_id`: Project identifier
- `task_id`: New current task ID (or `null` if cleared)
- `previous_task_id`: Previous task ID (if any)

**Example:**
```json
{
  "project_id": "my-project",
  "task_id": "task-123"
}
```

**When to use:**
- To switch between tasks
- To clear the current task
- The working set automatically updates for the new task

#### `context_get_task_context`

Get all context segments for a specific task.

**Parameters:**
- `project_id` (required): Project identifier
- `task_id` (optional): Task identifier (uses current task if not provided)

**Returns:**
- `task_id`: Task identifier
- `segments`: List of all segments for the task (from all tiers)
- `total_tokens`: Total token count
- `segment_count`: Number of segments

**Example:**
```json
{
  "project_id": "my-project",
  "task_id": "task-123"
}
```

**When to use:**
- To see all context for a specific task
- To review task context before switching tasks

#### `context_create_task_snapshot`

Create a snapshot of current task state for later retrieval.

**Parameters:**
- `project_id` (required): Project identifier
- `task_id` (optional): Task identifier (uses current task if not provided)
- `name` (optional): Snapshot name

**Returns:**
- `snapshot_id`: Snapshot identifier
- `task_id`: Task identifier
- `name`: Snapshot name
- `segments_snapshot`: Number of segments in snapshot
- `tokens_snapshot`: Token count in snapshot

**Example:**
```json
{
  "project_id": "my-project",
  "task_id": "task-123",
  "name": "before-refactor"
}
```

**When to use:**
- Before switching to another task
- Before performing major context cleanup
- To capture task state for later reference

---

## Common Workflows

### Monitoring Context Usage

**Regular monitoring:**
1. Call `context_analyze_usage` periodically (e.g., every 10-20 interactions)
2. Review `usage_percent` and `warnings`
3. If usage > 60%, review `recommendations` and `suggested_actions`
4. If usage > 80%, take action to free space

**Before hitting limits:**
1. Call `context_analyze_usage` to get current state
2. Review `pruning_candidates_count` and `impact_summary`
3. If candidates exist, call `context_gc_analyze` to review candidates
4. Execute pruning plan with `context_gc_prune`

### Pruning Context

**Proactive pruning:**
1. Monitor usage with `context_analyze_usage`
2. When usage > 80%, call `context_gc_analyze` with `target_tokens`
3. Review `pruning_plan` to see what will be pruned
4. Pin important segments with `context_gc_pin` if needed
5. Execute plan with `context_gc_prune` (action: "stash" recommended)

**Emergency pruning:**
1. Call `context_analyze_usage` to see current state
2. Call `context_gc_analyze` to get candidates
3. Review candidates and identify segments to prune
4. Call `context_gc_prune` with selected segment IDs

### Stashing and Retrieval

**Stashing old segments:**
1. Call `context_get_working_set` to see available segments
2. Use `context_stash` with filters to stash old segments:
   ```json
   {
     "filters": {
       "created_before": "2024-01-01T00:00:00Z",
       "type": "log"
     }
   }
   ```
3. Verify with `context_search_stashed`

**Retrieving stashed context:**
1. Search with `context_search_stashed` to find segments
2. Review results to identify what to retrieve
3. Retrieve with `context_retrieve_stashed`:
   ```json
   {
     "query": "important function",
     "move_to_active": true
   }
   ```
4. Verify with `context_get_working_set`

### Task Management

**Switching tasks:**
1. Create snapshot with `context_create_task_snapshot` (optional)
2. Set new task with `context_set_current_task`
3. Working set automatically updates for new task
4. Retrieve task context with `context_get_task_context` if needed

**Organizing by task:**
1. Use `task_id` consistently when creating segments
2. Filter by `task_id` when stashing/retrieving
3. Use `context_get_task_context` to review task context

---

## Agent Integration Patterns

### Proactive Context Management

**Pattern: Periodic Analysis**
```python
# Every N interactions, analyze usage
if interaction_count % 10 == 0:
    usage = context_analyze_usage(project_id="my-project")
    if usage["usage_percent"] > 60:
        # Take action
        candidates = context_gc_analyze(project_id="my-project")
        # Review and prune if needed
```

**Pattern: Pre-Limit Pruning**
```python
# Before approaching limits, prune proactively
usage = context_analyze_usage(project_id="my-project")
if usage["usage_percent"] > 80:
    plan = context_gc_analyze(
        project_id="my-project",
        target_tokens=usage["usage_metrics"]["total_tokens"] * 0.2
    )
    context_gc_prune(
        project_id="my-project",
        segment_ids=plan["pruning_plan"]["stash_segments"],
        action="stash"
    )
```

### Periodic Analysis

**Pattern: Health Monitoring**
```python
# Regular health checks
usage = context_analyze_usage(project_id="my-project")
health = usage["health_score"]["score"]
if health < 50:
    # Context is unhealthy, take corrective action
    # Review recommendations and apply fixes
```

### Retrieving Stashed Context

**Pattern: On-Demand Retrieval**
```python
# When needed, search and retrieve
results = context_search_stashed(
    query="relevant topic",
    filters={"type": "code"}
)
if results["total_matches"] > 0:
    context_retrieve_stashed(
        query="relevant topic",
        filters={"type": "code"},
        move_to_active=True
    )
```

---

## Best Practices

### When to Prune

- **Usage > 80%**: Prune proactively to avoid hitting limits
- **Usage > 90%**: Prune immediately (urgent)
- **After long sessions**: Prune old segments that are no longer relevant
- **Before major context changes**: Prune to make room for new context

### What to Stash

- **Old segments**: Segments created before a certain date
- **Unused code**: Code segments not referenced recently
- **Logs**: Debug logs and verbose output
- **Completed tasks**: Context from finished tasks
- **Low-priority content**: Notes and summaries that can be retrieved later

### Task Organization

- **Use consistent task IDs**: Use meaningful task identifiers
- **Create snapshots**: Before switching tasks, create snapshots
- **Filter by task**: When stashing/retrieving, use task_id filters
- **Review task context**: Use `context_get_task_context` to review before switching

### Performance Tips

- **Batch operations**: Prune multiple segments in one call
- **Use filters**: Filter segments before stashing to avoid unnecessary operations
- **Cache results**: Cache usage analysis results for a short period
- **Monitor regularly**: Don't wait until limits are hit

### Scalability Considerations

The system is designed for millions of tokens:

- **Indexing**: Inverted index ensures fast search (< 500ms for millions of tokens)
- **Token caching**: Token counts are cached in segment metadata
- **File sharding**: Stashed segments are stored in sharded files
- **LRU cache**: Active segments use LRU eviction (max 10k segments)

**For very large contexts:**
- Use filters to narrow searches
- Prune in batches rather than all at once
- Monitor memory usage if working with extremely large contexts

---

## Troubleshooting

### Common Issues

**High usage but no candidates:**
- All segments may be pinned or in root set
- Try unpinning segments or expanding root set
- Check if segments are actually old enough to be candidates

**Stash not freeing space:**
- Verify segments were actually stashed (check `stashed_segments` in response)
- Ensure segments were in working tier (not already stashed)
- Check for errors in response

**Search not finding segments:**
- Verify segments are in stashed storage (not deleted)
- Check query spelling and filters
- Try broader search terms
- Check project_id matches

**Pruning errors:**
- Pinned segments cannot be pruned (unpin first)
- Verify segment IDs exist
- Check for permission errors

### Error Messages

**INVALID_PARAMETER:**
- Check parameter types and required fields
- Verify JSON format if using JSON strings
- Check project_id is provided

**INTERNAL_ERROR:**
- Check server logs for details
- Verify storage directory is writable
- Check for disk space issues

**SEGMENT_NOT_FOUND:**
- Verify segment IDs exist
- Check project_id matches
- Ensure segments haven't been deleted

### Debugging Tips

1. **Check working set**: Use `context_get_working_set` to see current state
2. **Review usage**: Use `context_analyze_usage` to understand context state
3. **Inspect segments**: Review segment metadata to understand organization
4. **Check storage**: Verify storage directory exists and is writable
5. **Review logs**: Check server logs for detailed error information

---

## Next Steps

- **Development Guide**: Learn how to contribute and extend the server
- **API Documentation**: Detailed reference for all tools and models
- **Demo Guide**: Follow step-by-step demo scenarios

See [Development Guide](development.md) for development setup and [API Documentation](api/tools.md) for detailed tool reference.

