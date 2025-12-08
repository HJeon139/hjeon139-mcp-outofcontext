# Data Models Reference

Complete reference for all data models used by the Out of Context MCP server.

---

## Core Models

### `ContextSegment`

Core segment model representing a piece of context.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `segment_id` | string | Yes | Unique segment identifier |
| `text` | string | Yes | Segment text content |
| `type` | enum | Yes | Segment type: "message", "code", "log", "note", "decision", "summary" |
| `project_id` | string | Yes | Project identifier |
| `task_id` | string or null | No | Task identifier |
| `created_at` | datetime | Yes | Creation timestamp (ISO 8601) |
| `last_touched_at` | datetime | Yes | Last access timestamp (ISO 8601) |
| `pinned` | boolean | No | Whether segment is pinned (default: false) |
| `generation` | enum | No | GC generation: "young" or "old" (default: "young") |
| `gc_survival_count` | integer | No | Number of GC cycles survived (default: 0) |
| `refcount` | integer | No | Reference count (default: 0) |
| `file_path` | string or null | No | File path if applicable |
| `line_range` | tuple of integers or null | No | Line range [start, end] if applicable |
| `tags` | array of strings | No | Tags (default: []) |
| `topic_id` | string or null | No | Topic identifier |
| `tokens` | integer or null | No | Token count (cached) |
| `tokens_computed_at` | datetime or null | No | When token count was computed |
| `text_hash` | string or null | No | Hash of text for cache invalidation |
| `tier` | enum | No | Storage tier: "working", "stashed", "archive" (default: "working") |

**Example:**
```json
{
  "segment_id": "seg-123",
  "text": "This is a code segment",
  "type": "code",
  "project_id": "my-project",
  "task_id": "task-456",
  "created_at": "2024-01-01T10:00:00Z",
  "last_touched_at": "2024-01-01T12:00:00Z",
  "pinned": false,
  "generation": "young",
  "gc_survival_count": 0,
  "refcount": 1,
  "file_path": "src/main.py",
  "line_range": [10, 20],
  "tags": ["important", "reference"],
  "topic_id": null,
  "tokens": 150,
  "tokens_computed_at": "2024-01-01T10:00:00Z",
  "text_hash": "abc123...",
  "tier": "working"
}
```

**Validation Rules:**
- `segment_id` must be unique within a project
- `type` must be one of the allowed values
- `tokens` must be non-negative if provided
- `line_range` must be [start, end] where start <= end

---

### `SegmentSummary`

High-level segment information for summaries.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `segment_id` | string | Yes | Segment identifier |
| `type` | enum | Yes | Segment type |
| `preview` | string | Yes | Text preview (first N characters) |
| `tokens` | integer | Yes | Token count |
| `created_at` | datetime | Yes | Creation timestamp |

**Example:**
```json
{
  "segment_id": "seg-123",
  "type": "code",
  "preview": "def function(): ...",
  "tokens": 150,
  "created_at": "2024-01-01T10:00:00Z"
}
```

---

## Analysis Models

### `UsageMetrics`

Context usage metrics.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_tokens` | integer | Yes | Total token count |
| `total_segments` | integer | Yes | Total segment count |
| `tokens_by_type` | object | No | Token count by segment type (default: {}) |
| `segments_by_type` | object | No | Segment count by type (default: {}) |
| `tokens_by_task` | object | No | Token count by task ID (default: {}) |
| `oldest_segment_age_hours` | float | Yes | Age of oldest segment in hours |
| `newest_segment_age_hours` | float | Yes | Age of newest segment in hours |
| `pinned_segments_count` | integer | Yes | Number of pinned segments |
| `pinned_tokens` | integer | Yes | Total tokens in pinned segments |
| `usage_percent` | float | Yes | Usage percentage (0-100) |
| `estimated_remaining_tokens` | integer | Yes | Estimated remaining tokens |

**Example:**
```json
{
  "total_tokens": 25000,
  "total_segments": 150,
  "tokens_by_type": {
    "message": 10000,
    "code": 15000
  },
  "segments_by_type": {
    "message": 50,
    "code": 100
  },
  "tokens_by_task": {
    "task-123": 20000,
    "task-456": 5000
  },
  "oldest_segment_age_hours": 24.5,
  "newest_segment_age_hours": 0.1,
  "pinned_segments_count": 5,
  "pinned_tokens": 5000,
  "usage_percent": 2.5,
  "estimated_remaining_tokens": 975000
}
```

---

### `HealthScore`

Context health score.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `score` | float | Yes | Health score (0-100, higher = healthier) |
| `usage_percent` | float | Yes | Usage percentage (0-100) |
| `factors` | object | No | Score factors and contributions (default: {}) |

**Example:**
```json
{
  "score": 85.0,
  "usage_percent": 2.5,
  "factors": {
    "usage": 0.9,
    "distribution": 0.8,
    "age": 0.9
  }
}
```

**Score Calculation:**
- Based on usage percentage (lower usage = higher score)
- Distribution of segment types (balanced = higher score)
- Age of segments (recent = higher score)
- Other factors as implemented

---

### `Recommendation`

Recommendation for context management.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `priority` | enum | Yes | Priority level: "low", "medium", "high", "urgent" |
| `message` | string | Yes | Recommendation message |
| `action` | string or null | No | Suggested action |

**Example:**
```json
{
  "priority": "high",
  "message": "Context usage at 80%+ - consider pruning to free space",
  "action": "context_gc_analyze"
}
```

---

### `AnalysisResult`

Context analysis results.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_tokens` | integer | Yes | Total token count |
| `segment_count` | integer | Yes | Number of segments |
| `usage_percent` | float | Yes | Usage percentage |
| `health_score` | HealthScore | Yes | Context health score |
| `recommendations` | array of strings | No | Analysis recommendations (default: []) |

**Example:**
```json
{
  "total_tokens": 25000,
  "segment_count": 150,
  "usage_percent": 2.5,
  "health_score": {
    "score": 85.0,
    "usage_percent": 2.5,
    "factors": {}
  },
  "recommendations": [
    "Context usage is healthy"
  ]
}
```

---

## Pruning Models

### `PruningCandidate`

Pruning candidate with score and metadata.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `segment_id` | string | Yes | Segment identifier |
| `score` | float | Yes | Prune score (higher = more likely to prune) |
| `tokens` | integer | Yes | Token count for this segment |
| `reason` | string | Yes | Reason why it's a candidate |
| `segment_type` | string | Yes | Segment type |
| `age_hours` | float | Yes | Age in hours |

**Example:**
```json
{
  "segment_id": "seg-123",
  "score": 0.85,
  "tokens": 500,
  "reason": "old + low refcount",
  "segment_type": "log",
  "age_hours": 48.5
}
```

**Score Calculation:**
- Age factor (older = higher score)
- Reference count (lower = higher score)
- Segment type (logs/notes = higher score)
- Other heuristics as implemented

---

### `PruningPlan`

Pruning plan with candidates and actions.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `candidates` | array of PruningCandidate | Yes | Sorted candidates by score |
| `total_tokens_freed` | integer | Yes | Total tokens that will be freed |
| `stash_segments` | array of strings | Yes | Segment IDs to stash |
| `delete_segments` | array of strings | Yes | Segment IDs to delete |
| `reason` | string | Yes | Explanation of plan |

**Example:**
```json
{
  "candidates": [
    {
      "segment_id": "seg-123",
      "score": 0.85,
      "tokens": 500,
      "reason": "old + low refcount",
      "segment_type": "log",
      "age_hours": 48.5
    }
  ],
  "total_tokens_freed": 25000,
  "stash_segments": ["seg-123", "seg-456"],
  "delete_segments": [],
  "reason": "Plan to free 25000 tokens by stashing old segments"
}
```

---

## Stashing Models

### `StashResult`

Stashing operation result.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stashed_segments` | array of strings | Yes | IDs of stashed segments |
| `tokens_freed` | integer | Yes | Tokens freed by stashing |
| `stash_location` | string or null | No | Stash storage location |

**Example:**
```json
{
  "stashed_segments": ["seg-123", "seg-456"],
  "tokens_freed": 5000,
  "stash_location": ".out_of_context/stashed/default.json"
}
```

---

## Working Set Models

### `WorkingSet`

Working set abstraction.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `segments` | array of ContextSegment | Yes | Active segments |
| `total_tokens` | integer | Yes | Total token count |
| `project_id` | string | Yes | Project identifier |
| `task_id` | string or null | No | Task identifier |
| `last_updated` | datetime | Yes | Last update timestamp |

**Example:**
```json
{
  "segments": [
    {
      "segment_id": "seg-123",
      "text": "...",
      "type": "message",
      ...
    }
  ],
  "total_tokens": 25000,
  "project_id": "my-project",
  "task_id": "task-456",
  "last_updated": "2024-01-01T12:00:00Z"
}
```

---

## Parameter Models

### `ContextDescriptors`

Context descriptors from platform.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recent_messages` | array | Yes | Last N messages |
| `current_file` | object or null | No | Active file and location |
| `token_usage` | TokenUsage | Yes | Current token counts |
| `segment_summaries` | array | Yes | High-level segment info |
| `task_info` | object or null | No | Current task metadata |

**Example:**
```json
{
  "recent_messages": [
    {
      "role": "user",
      "content": "..."
    }
  ],
  "current_file": {
    "path": "src/main.py",
    "line": 123
  },
  "token_usage": {
    "current": 25000,
    "limit": 1000000,
    "usage_percent": 2.5
  },
  "segment_summaries": [
    {
      "segment_id": "seg-123",
      "type": "code",
      "preview": "...",
      "tokens": 150,
      "created_at": "2024-01-01T10:00:00Z"
    }
  ],
  "task_info": {
    "task_id": "task-456",
    "name": "Fix bug"
  }
}
```

---

### `TokenUsage`

Token usage information.

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `current` | integer | Yes | Current token count |
| `limit` | integer | Yes | Token limit |
| `usage_percent` | float | Yes | Usage percentage (0-100) |

**Example:**
```json
{
  "current": 25000,
  "limit": 1000000,
  "usage_percent": 2.5
}
```

---

## Type Definitions

### Segment Types

- `"message"`: Chat messages or conversation history
- `"code"`: Code snippets or files
- `"log"`: Debug logs or verbose output
- `"note"`: Notes or annotations
- `"decision"`: Decisions or architectural choices
- `"summary"`: Summaries or compressions

### Storage Tiers

- `"working"`: Active segments in working set
- `"stashed"`: Archived segments in stashed storage
- `"archive"`: Long-term archived segments (future use)

### GC Generations

- `"young"`: Recently created segments
- `"old"`: Older segments that have survived GC cycles

---

## Validation Rules

### General Rules

- All required fields must be present
- String fields must be non-empty (unless nullable)
- Integer fields must be non-negative
- Datetime fields must be valid ISO 8601 format
- Enum fields must match allowed values

### Segment Validation

- `segment_id` must be unique within a project
- `tokens` must match actual token count if provided
- `line_range` must be valid [start, end] where start <= end
- `tier` must match actual storage location

### Metrics Validation

- `usage_percent` must be between 0 and 100
- `total_tokens` must equal sum of tokens_by_type
- `total_segments` must equal sum of segments_by_type

---

## See Also

- [Tool API Reference](tools.md) - Tool parameters and return values
- [Usage Guide](../usage.md) - Usage instructions and examples
- [Development Guide](../development.md) - Development setup

