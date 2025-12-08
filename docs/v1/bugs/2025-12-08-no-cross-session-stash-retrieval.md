# Issue: Cannot retrieve stashed context from different chat window/session

**Date**: 2025-12-08  
**Severity**: High (Launch Blocker)  
**Component**: MCP Tools / Storage / Retrieval  
**Status**: Fixed (2025-12-08)

## Description
The `context_search_stashed` tool requires a `project_id` parameter, but there is no way to discover what `project_id` values exist or search across all projects. This prevents retrieving stashed context from a different chat window or session where the `project_id` may be unknown or different. The storage layer organizes segments by project (one JSON file per project), but the MCP tool interface doesn't expose project discovery functionality.

## Reproduction
1. In Chat Window A: Stash context segments using `context_stash` with a specific `project_id` (e.g., "my-project")
2. Open a new Chat Window B (or start a new session)
3. Attempt to retrieve stashed context using `context_search_stashed`
4. **Result**: The tool requires a `project_id`, but there's no way to know what project IDs exist or to search across all projects

## Expected Behavior
- Ability to discover available `project_id` values (e.g., `context_list_projects` tool)
- Ability to search stashed context across all projects (optional `project_id` parameter)
- Or automatic project discovery when `project_id` is not provided

## Actual Behavior
- `context_search_stashed` requires `project_id` (validated as mandatory)
- No tool or method to list available projects
- No way to search across all projects
- Stashed context from previous sessions is inaccessible if `project_id` is unknown

## Impact
- **Launch Blocker**: Core use case broken - users cannot retrieve context across sessions
- Stashed context becomes inaccessible after switching chat windows or sessions
- Users must remember or document `project_id` values manually
- Breaks the fundamental promise of persistent context storage

## Root Cause
- Storage layer organizes by project: `stashed_dir / f"{project_id}.json"`
- MCP tool interface requires `project_id` but doesn't provide discovery mechanism
- `rebuild_indexes` function iterates through all JSON files, but this isn't exposed via MCP tools

## Proposed Solution
1. **Add project discovery tool**: `context_list_projects` that returns all available project IDs from stashed directory
2. **Make `project_id` optional in `context_search_stashed`**: When omitted, search across all projects
3. **Add project metadata**: Store project creation time, last accessed, segment count, etc.

## Implementation Notes
- Storage layer already has the capability (iterates through all `.json` files in `rebuild_indexes`)
- Need to expose this via MCP tool interface
- Consider backward compatibility if making `project_id` optional

## Resolution
**Fixed on 2025-12-08:**
- Added `context_list_projects` tool to discover available project IDs
- Made `project_id` optional in `context_search_stashed` - when omitted, searches across all projects
- Updated `context_retrieve_stashed` to also support optional `project_id` for cross-project retrieval
- Storage layer's `list_projects()` method now exposed via MCP tool interface

**Implementation:**
- `src/hjeon139_mcp_outofcontext/tools/stashing/context_list_projects.py` - New tool for project discovery
- `src/hjeon139_mcp_outofcontext/storage/__init__.py` - Added `list_projects()` method
- `src/hjeon139_mcp_outofcontext/storage/file_operations.py` - Added `list_stashed_projects()` implementation
- `src/hjeon139_mcp_outofcontext/tools/stashing/context_search_stashed.py` - Made `project_id` optional

## Verification Steps

To verify cross-session stash retrieval works correctly:

### Step 1: Discover Available Projects

First, list all projects that have stashed context:

```
Call: context_list_projects
```

This returns all project IDs with stashed context, even if you don't know the project_id from the other session.

### Step 2: Search for Stashed Context

Search across all projects or within a specific project:

**Option A: Search across all projects (omit project_id)**

```
Call: context_search_stashed(query="your search term")
```

**Option B: Search within a specific project**

```
Call: context_search_stashed(project_id="project-name", query="your search term")
```

**Option C: Search with filters**

```
Call: context_search_stashed(
    project_id="project-name",
    filters={"type": "message", "created_after": "2025-12-08T00:00:00Z"}
)
```

### Step 3: Retrieve Stashed Context

After finding segments, retrieve them:

**Just retrieve (read-only):**

```
Call: context_retrieve_stashed(
    project_id="project-name",
    query="your search term"
)
```

**Retrieve and restore to active context:**

```
Call: context_retrieve_stashed(
    project_id="project-name",
    query="your search term",
    move_to_active=True
)
```

### Step 4: Verify Content

After retrieving, verify the content matches what was stashed:

```
Call: context_get_working_set(project_id="project-name")
```

This shows the segments in active context if you used `move_to_active=True`.

### Example Verification Workflow

1. **List projects**: `context_list_projects()` → Returns: `["test-put-fetch", "test-simple-interface"]`

2. **Search for "IMPORTANT"**: `context_search_stashed(project_id="test-put-fetch", query="IMPORTANT")`

3. **Retrieve important message**: `context_retrieve_stashed(project_id="test-put-fetch", query="IMPORTANT", move_to_active=True)`

4. **Verify**: `context_get_working_set(project_id="test-put-fetch")` → Should show the retrieved segment

### Key Features to Test

- Cross-project discovery: `context_list_projects` works without knowing project IDs
- Cross-project search: Omit `project_id` to search all projects
- Query-based retrieval: Use `query` to find segments by content
- Filter-based retrieval: Use `filters` to find segments by metadata
- Restore capability: Use `move_to_active=True` to restore segments to active context

The interface abstracts away segment IDs—use queries and filters instead.

## Related Issues
- Related to `2025-12-08-no-auto-fetch-from-stash.md` - both involve retrieval workflow
- Related to `2025-12-08-no-auto-rehydrate-when-empty.md` - both involve context restoration

