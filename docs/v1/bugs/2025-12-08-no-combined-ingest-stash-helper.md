# Issue: No combined ingest+stash helper; multiple calls required

**Date**: 2025-12-08  
**Severity**: Medium  
**Component**: workflow / UX  
**Status**: Partially Addressed (2025-12-08)

## Description
Capturing context requires multiple MCP calls (`context_analyze_usage` → `context_get_working_set` → `context_stash`), increasing latency and effort. There is no helper or single-call path to ingest and stash recent messages/file pointers in one step.

## Impact
- Higher latency and more drafting overhead per update.
- Greater chance of missing a step (e.g., forgetting to stash after ingest).

## Partial Resolution (2025-12-08)
**Improved:**
- Simplified stash interface: No longer need to call `context_get_working_set` first to extract segment IDs
- Can now stash directly with query/filters: `context_stash(project_id="x", query="old docs")` or `context_stash(project_id="x", filters={"type": "file"})`
- Reduced from 3 calls to 2 calls: `context_analyze_usage` → `context_stash` (no need for `context_get_working_set` in between)
- Interface is more intuitive - agents think in terms of content/metadata, not segment IDs

**Still Open:**
- Still requires 2 separate calls (`context_analyze_usage` + `context_stash`)
- No single "ingest_and_stash" helper that combines both operations

**Implementation:**
- `src/hjeon139_mcp_outofcontext/tools/stashing/context_stash.py` - Now accepts query/filters instead of segment_ids
- `src/hjeon139_mcp_outofcontext/tools/stashing/context_retrieve_stashed.py` - Now accepts query/filters instead of segment_ids

## Proposed Solution (if known)
- Add a helper tool (e.g., "ingest_and_stash") that takes descriptors and stashes the resulting segments in one call.
- Keep minimal deps; reuse existing context manager/storage logic internally.

