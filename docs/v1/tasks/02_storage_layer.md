# Task 02: Storage Layer Implementation

## Dependencies

- Task 01: Project Foundation and Core Infrastructure

## Scope

Implement the storage layer that manages both in-memory active segments and persistent stashed segments. This includes:

- Implement `IStorageLayer` interface from [09_interfaces.md](../design/09_interfaces.md)
- In-memory storage for active segments (`Dict[str, ContextSegment]`)
- JSON file persistence for stashed segments
- Load/save operations with error handling
- Project-scoped storage organization
- Basic metadata indexing (by project, task, file)

## Acceptance Criteria

- Segments can be stored and retrieved from memory
- Stashed segments persist to JSON file
- Storage survives server restart (loads from JSON on startup)
- Storage operations are atomic (no partial writes)
- Handles missing/corrupt JSON files gracefully
- Project isolation works (segments scoped to project_id)

## Implementation Details

### Storage Interface

Implement the `IStorageLayer` interface with the following methods:

- `store_segment(segment: ContextSegment, project_id: str) -> None`
- `load_segments(project_id: str) -> List[ContextSegment]`
- `stash_segment(segment: ContextSegment, project_id: str) -> None`
- `search_stashed(query: str, filters: Dict, project_id: str) -> List[ContextSegment]`
- `delete_segment(segment_id: str, project_id: str) -> None`

### In-Memory Storage

Maintain active segments in memory:

```python
active_segments: Dict[str, Dict[str, ContextSegment]] = {}  # project_id -> segment_id -> segment
```

### JSON File Persistence

Store stashed segments in JSON format:

```json
{
  "version": "1.0",
  "projects": {
    "project_id": {
      "segments": [
        {
          "segment_id": "...",
          "text": "...",
          "type": "message",
          "metadata": {...},
          "tokens": 100,
          ...
        }
      ],
      "indexes": {
        "by_task": {"task_id": ["segment_id", ...]},
        "by_file": {"file_path": ["segment_id", ...]},
        "by_tag": {"tag": ["segment_id", ...]}
      }
    }
  }
}
```

### Storage Location

- Default storage path: `~/.out_of_context/storage.json`
- Configurable via environment variable: `OUT_OF_CONTEXT_STORAGE_PATH`
- Create directory if it doesn't exist

### Atomic Operations

- Use temporary file + rename pattern for atomic writes
- Write to `storage.json.tmp`, then rename to `storage.json`
- Handle partial writes by checking for `.tmp` files on startup

### Error Handling

- Handle missing JSON file (treat as empty storage)
- Handle corrupt JSON (log error, start with empty storage)
- Handle permission errors (raise clear exceptions)
- Handle disk full errors (raise clear exceptions)

### Project Isolation

- All operations scoped to `project_id`
- Segments from different projects never mix
- Indexes maintained per project

### Metadata Indexing

Maintain simple indexes for fast filtering:

- By task_id: `Dict[str, List[str]]` (task_id -> segment_ids)
- By file_path: `Dict[str, List[str]]` (file_path -> segment_ids)
- By tag: `Dict[str, List[str]]` (tag -> segment_ids)

Indexes updated on segment store/stash/delete.

## Testing Approach

### Unit Tests

- Test in-memory storage operations (store, retrieve, delete)
- Test JSON serialization/deserialization
- Test atomic write operations
- Test index maintenance
- Test project isolation

### Integration Tests

- Test full persistence cycle (store, restart, load)
- Test concurrent access handling
- Test error recovery (corrupt file, missing file)

### Test Files

- `tests/test_storage.py` - Storage layer tests

### Test Scenarios

1. Store segment in memory, verify retrieval
2. Stash segment, verify JSON persistence
3. Restart server, verify segments loaded from JSON
4. Store segments for multiple projects, verify isolation
5. Test atomic writes (simulate crash during write)
6. Test error handling (corrupt JSON, missing file, permission errors)

## References

- [Interfaces and Data Models](../design/09_interfaces.md) - Storage interface specification
- [Components](../design/04_components.md) - Storage Layer component details
- [Architectural Decisions](../design/03_architectural_decisions.md) - Storage strategy decision
- [Constraints and Requirements](../design/07_constraints_requirements.md) - Performance requirements

