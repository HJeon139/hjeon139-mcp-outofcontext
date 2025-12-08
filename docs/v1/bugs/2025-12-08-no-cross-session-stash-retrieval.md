# Issue: Cannot retrieve stashed context from different chat window/session

**Date**: 2025-12-08  
**Severity**: High (Launch Blocker)  
**Component**: MCP Tools / Storage / Retrieval  
**Status**: Open

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

## Related Issues
- Related to `2025-12-08-no-auto-fetch-from-stash.md` - both involve retrieval workflow
- Related to `2025-12-08-no-auto-rehydrate-when-empty.md` - both involve context restoration

