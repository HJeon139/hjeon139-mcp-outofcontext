# Tool API Reference

Complete reference for all MCP tools provided by the Out of Context server.

---

## Monitoring Tools

### `context_analyze_usage`

Analyze current context usage and return metrics, health score, and recommendations.

**Tool Name:** `context_analyze_usage`

**Description:**
Analyze current context usage and return metrics, health score, and recommendations. Use this tool to understand how much context is being used, the health of the context, and get recommendations for context management. Warnings are provided when usage crosses thresholds: 60% (warning), 80% (high), 90% (urgent). Check usage periodically, especially when context grows.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project identifier |
| `context_descriptors` | object or string | No | Context descriptors from platform (JSON string or dict) |
| `task_id` | string | No | Optional task identifier |
| `token_limit` | integer | No | Optional token limit (default: from config, typically 1 million) |

**Context Descriptors Structure:**
```json
{
  "recent_messages": [...],
  "current_file": {"path": "...", "line": 123},
  "token_usage": {
    "current": 25000,
    "limit": 1000000,
    "usage_percent": 2.5
  },
  "segment_summaries": [...],
  "task_info": {...}
}
```

**Return Value:**

```json
{
  "usage_metrics": {
    "total_tokens": 25000,
    "total_segments": 150,
    "tokens_by_type": {"message": 10000, "code": 15000},
    "segments_by_type": {"message": 50, "code": 100},
    "tokens_by_task": {"task-123": 20000},
    "oldest_segment_age_hours": 24.5,
    "newest_segment_age_hours": 0.1,
    "pinned_segments_count": 5,
    "pinned_tokens": 5000,
    "usage_percent": 2.5,
    "estimated_remaining_tokens": 975000
  },
  "health_score": {
    "score": 85.0,
    "usage_percent": 2.5,
    "factors": {
      "usage": 0.9,
      "distribution": 0.8,
      "age": 0.9
    }
  },
  "recommendations": [
    {
      "priority": "low",
      "message": "Context usage is healthy",
      "action": null
    }
  ],
  "warnings": [],
  "suggested_actions": [],
  "impact_summary": {
    "pruning_candidates_count": 50,
    "estimated_tokens_freed": 10000,
    "estimated_usage_after_pruning": 1.5
  },
  "pruning_candidates_count": 50
}
```

**Error Cases:**

- `INVALID_PARAMETER`: Missing or invalid `project_id`
- `INVALID_PARAMETER`: Invalid JSON in `context_descriptors` (if string)
- `INTERNAL_ERROR`: Internal server error

**Example Request:**
```json
{
  "project_id": "my-project",
  "token_limit": 1000000
}
```

---

### `context_get_working_set`

Get current working set segments for the active task.

**Tool Name:** `context_get_working_set`

**Description:**
Get current working set segments for the active task. Use this tool to see what segments are currently active in the working set.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project identifier |
| `task_id` | string | No | Optional task identifier (uses current task if not provided) |

**Return Value:**

```json
{
  "working_set": {
    "project_id": "my-project",
    "task_id": "task-123",
    "total_tokens": 25000,
    "last_updated": "2024-01-01T12:00:00Z"
  },
  "segments": [
    {
      "segment_id": "seg1",
      "text": "...",
      "type": "message",
      "project_id": "my-project",
      "task_id": "task-123",
      "created_at": "2024-01-01T10:00:00Z",
      "last_touched_at": "2024-01-01T12:00:00Z",
      "pinned": false,
      "generation": "young",
      "gc_survival_count": 0,
      "refcount": 1,
      "file_path": null,
      "line_range": null,
      "tags": [],
      "topic_id": null,
      "tokens": 100,
      "tokens_computed_at": "2024-01-01T10:00:00Z",
      "text_hash": "...",
      "tier": "working"
    }
  ],
  "total_tokens": 25000,
  "segment_count": 150
}
```

**Error Cases:**

- `INVALID_PARAMETER`: Missing or invalid `project_id`
- `INTERNAL_ERROR`: Internal server error

**Example Request:**
```json
{
  "project_id": "my-project"
}
```

---

## Pruning Tools

### `context_gc_analyze`

Analyze context and identify pruning candidates using GC heuristics.

**Tool Name:** `context_gc_analyze`

**Description:**
Analyze context and identify pruning candidates using GC heuristics. Use this tool to see which segments are candidates for pruning based on age, reachability, type, and other factors. Optionally provide target_tokens to generate a pruning plan.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project identifier |
| `context_descriptors` | object or string | No | Context descriptors from platform |
| `task_id` | string | No | Optional task identifier |
| `target_tokens` | integer | No | Optional target tokens to free (generates pruning plan if provided) |

**Return Value:**

```json
{
  "pruning_candidates": [
    {
      "segment_id": "seg1",
      "score": 0.85,
      "tokens": 500,
      "reason": "old + low refcount",
      "segment_type": "log",
      "age_hours": 48.5
    }
  ],
  "total_candidates": 50,
  "estimated_tokens_freed": 25000,
  "pruning_plan": {
    "candidates": [...],
    "total_tokens_freed": 25000,
    "stash_segments": ["seg1", "seg2"],
    "delete_segments": [],
    "reason": "Plan to free 25000 tokens by stashing old segments"
  }
}
```

**Note:** `pruning_plan` is only included if `target_tokens` is provided.

**Error Cases:**

- `INVALID_PARAMETER`: Missing or invalid `project_id`
- `INTERNAL_ERROR`: Internal server error

**Example Request:**
```json
{
  "project_id": "my-project",
  "target_tokens": 100000
}
```

---

### `context_gc_prune`

Execute pruning plan to free context space.

**Tool Name:** `context_gc_prune`

**Description:**
Execute pruning plan to free context space. Use this tool to stash or delete segments identified as pruning candidates. Pinned segments cannot be pruned. Delete actions require confirm=True.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project identifier |
| `segment_ids` | array of strings | Yes | List of segment IDs to prune |
| `action` | string | Yes | Action to take: "stash" or "delete" |
| `confirm` | boolean | No | Safety flag - must be True for delete actions (default: false) |

**Return Value:**

```json
{
  "pruned_segments": ["seg1", "seg2"],
  "tokens_freed": 1000,
  "action": "stashed",
  "errors": []
}
```

**Error Cases:**

- `INVALID_PARAMETER`: Missing or invalid parameters
- `INVALID_PARAMETER`: Pinned segments cannot be pruned
- `INVALID_PARAMETER`: Delete action requires `confirm=true`
- `INTERNAL_ERROR`: Internal server error

**Example Request:**
```json
{
  "project_id": "my-project",
  "segment_ids": ["seg1", "seg2"],
  "action": "stash"
}
```

---

### `context_gc_pin`

Pin segments to protect them from pruning.

**Tool Name:** `context_gc_pin`

**Description:**
Pin segments to protect them from pruning. Pinned segments will not be pruned by the GC engine. Use this tool to protect important segments from being removed.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project identifier |
| `segment_ids` | array of strings | Yes | List of segment IDs to pin |

**Return Value:**

```json
{
  "pinned_segments": ["seg1", "seg2"],
  "errors": []
}
```

**Error Cases:**

- `INVALID_PARAMETER`: Missing or invalid parameters
- `INTERNAL_ERROR`: Internal server error

**Example Request:**
```json
{
  "project_id": "my-project",
  "segment_ids": ["seg1", "seg2"]
}
```

---

### `context_gc_unpin`

Unpin segments to allow pruning.

**Tool Name:** `context_gc_unpin`

**Description:**
Unpin segments to allow pruning. Unpinned segments can be pruned by the GC engine. Use this tool to allow previously pinned segments to be removed.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project identifier |
| `segment_ids` | array of strings | Yes | List of segment IDs to unpin |

**Return Value:**

```json
{
  "unpinned_segments": ["seg1", "seg2"],
  "errors": []
}
```

**Error Cases:**

- `INVALID_PARAMETER`: Missing or invalid parameters
- `INTERNAL_ERROR`: Internal server error

**Example Request:**
```json
{
  "project_id": "my-project",
  "segment_ids": ["seg1", "seg2"]
}
```

---

## Stashing Tools

### `context_stash`

Move segments from active context to stashed storage by filtering.

**Tool Name:** `context_stash`

**Description:**
PUT CONTEXT: Move segments from active context to stashed storage by filtering. This is the primary tool for freeing up active context space.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | No | Project identifier (defaults to 'default', avoid when possible) |
| `query` | string | No | Keyword to match segment text |
| `filters` | object or string | No | Metadata filters (dict or JSON string) |

**Filters Structure:**
```json
{
  "file_path": "src/main.py",
  "task_id": "task-123",
  "tags": ["important", "reference"],
  "type": "code",
  "created_after": "2024-01-01T00:00:00Z",
  "created_before": "2024-12-31T23:59:59Z"
}
```

**Return Value:**

```json
{
  "stashed_segments": ["seg1", "seg2"],
  "tokens_stashed": 5000,
  "segments_matched": 10,
  "errors": []
}
```

**Error Cases:**

- `INVALID_PARAMETER`: Invalid filters format
- `INTERNAL_ERROR`: Internal server error

**Example Request:**
```json
{
  "query": "old documentation",
  "filters": {
    "type": "note",
    "created_before": "2024-01-01T00:00:00Z"
  }
}
```

---

### `context_search_stashed`

Search stashed segments by keyword and metadata filters (read-only).

**Tool Name:** `context_search_stashed`

**Description:**
SEARCH STASHED: Search stashed segments by keyword and metadata filters (read-only). Use this tool to discover what's in stashed storage before retrieving.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | No | Project identifier (omit to search all projects) |
| `query` | string | No | Keyword search in segment text |
| `filters` | object or string | No | Metadata filters (same as `context_stash`) |
| `limit` | integer | No | Maximum number of results (default: 50) |

**Return Value:**

```json
{
  "segments": [
    {
      "segment_id": "seg1",
      "text": "...",
      "type": "code",
      ...
    }
  ],
  "total_matches": 25,
  "query": "function",
  "filters_applied": {
    "file_path": "src/main.py"
  }
}
```

**Error Cases:**

- `INVALID_PARAMETER`: Invalid filters format
- `INTERNAL_ERROR`: Internal server error

**Example Request:**
```json
{
  "query": "function",
  "filters": {
    "file_path": "src/main.py"
  },
  "limit": 20
}
```

---

### `context_retrieve_stashed`

Retrieve stashed segments by searching with query and filters.

**Tool Name:** `context_retrieve_stashed`

**Description:**
FETCH CONTEXT: Retrieve stashed segments by searching with query and filters. This is the primary tool for accessing previously stashed context.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | No | Project identifier (defaults to 'default') |
| `query` | string | No | Keyword to match segment text |
| `filters` | object or string | No | Metadata filters (same as `context_stash`) |
| `move_to_active` | boolean | No | If true, restore segments to active context (default: false) |

**Return Value:**

```json
{
  "retrieved_segments": [
    {
      "segment_id": "seg1",
      "text": "...",
      "type": "code",
      ...
    }
  ],
  "moved_to_active": ["seg1", "seg2"],
  "segments_found": 5
}
```

**Note:** `moved_to_active` is only included if `move_to_active=true`.

**Error Cases:**

- `INVALID_PARAMETER`: Invalid filters format
- `INTERNAL_ERROR`: Internal server error

**Example Request:**
```json
{
  "query": "launch bugs",
  "move_to_active": true
}
```

---

### `context_list_projects`

List all available project IDs from stashed storage.

**Tool Name:** `context_list_projects`

**Description:**
List all available project IDs from stashed storage. Use this tool to discover available projects when you don't know the project_id or need to search across multiple projects.

**Parameters:** None

**Return Value:**

```json
{
  "projects": ["project1", "project2", "default"]
}
```

**Error Cases:**

- `INTERNAL_ERROR`: Internal server error

**Example Request:**
```json
{}
```

---

## Task Management Tools

### `context_set_current_task`

Set the active task ID for a project.

**Tool Name:** `context_set_current_task`

**Description:**
Set the active task ID for a project, updating the working set. Use this tool to switch between tasks or clear the current task. The working set will automatically update to include only segments for the new task.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project identifier |
| `task_id` | string or null | No | Task identifier (null to clear current task) |

**Return Value:**

```json
{
  "project_id": "my-project",
  "task_id": "task-123",
  "previous_task_id": "task-456"
}
```

**Error Cases:**

- `INVALID_PARAMETER`: Missing or invalid `project_id`
- `INTERNAL_ERROR`: Internal server error

**Example Request:**
```json
{
  "project_id": "my-project",
  "task_id": "task-123"
}
```

---

### `context_get_task_context`

Get all context segments for a specific task.

**Tool Name:** `context_get_task_context`

**Description:**
Get all context segments for a specific task. Use this tool to see all segments (from all tiers) that belong to a specific task.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project identifier |
| `task_id` | string | No | Task identifier (uses current task if not provided) |

**Return Value:**

```json
{
  "task_id": "task-123",
  "segments": [
    {
      "segment_id": "seg1",
      "text": "...",
      "type": "message",
      ...
    }
  ],
  "total_tokens": 50000,
  "segment_count": 200
}
```

**Error Cases:**

- `INVALID_PARAMETER`: Missing or invalid `project_id`
- `INTERNAL_ERROR`: Internal server error

**Example Request:**
```json
{
  "project_id": "my-project",
  "task_id": "task-123"
}
```

---

### `context_create_task_snapshot`

Create a snapshot of current task state for later retrieval.

**Tool Name:** `context_create_task_snapshot`

**Description:**
Create a snapshot of current task state for later retrieval. Use this tool to capture the state of a task before switching to another task or performing major context cleanup. Snapshots are stored in stashed storage with special tags.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project identifier |
| `task_id` | string | No | Task identifier (uses current task if not provided) |
| `name` | string | No | Optional snapshot name |

**Return Value:**

```json
{
  "snapshot_id": "snapshot-123",
  "task_id": "task-123",
  "name": "before-refactor",
  "segments_snapshot": 150,
  "tokens_snapshot": 25000
}
```

**Error Cases:**

- `INVALID_PARAMETER`: Missing or invalid `project_id`
- `INTERNAL_ERROR`: Internal server error

**Example Request:**
```json
{
  "project_id": "my-project",
  "task_id": "task-123",
  "name": "before-refactor"
}
```

---

## Error Response Format

All tools may return error responses in the following format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "exception": "Detailed error information"
    }
  }
}
```

**Common Error Codes:**

- `INVALID_PARAMETER`: Invalid or missing parameters
- `INTERNAL_ERROR`: Internal server error
- `SEGMENT_NOT_FOUND`: Segment ID not found
- `PERMISSION_DENIED`: Operation not allowed (e.g., pruning pinned segments)

---

## See Also

- [Usage Guide](../usage.md) - Detailed usage instructions and workflows
- [Data Models](models.md) - Reference for data structures
- [Development Guide](../development.md) - Development setup and contribution guidelines

