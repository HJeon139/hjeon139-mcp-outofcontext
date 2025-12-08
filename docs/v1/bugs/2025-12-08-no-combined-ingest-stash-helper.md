# Issue: No combined ingest+stash helper; multiple calls required

**Date**: 2025-12-08  
**Severity**: Medium  
**Component**: workflow / UX  
**Status**: Open

## Description
Capturing context requires multiple MCP calls (`context_analyze_usage` → `context_get_working_set` → `context_stash`), increasing latency and effort. There is no helper or single-call path to ingest and stash recent messages/file pointers in one step.

## Impact
- Higher latency and more drafting overhead per update.
- Greater chance of missing a step (e.g., forgetting to stash after ingest).

## Proposed Solution (if known)
- Add a helper tool (e.g., “ingest_and_stash”) that takes descriptors and stashes the resulting segments in one call.
- Keep minimal deps; reuse existing context manager/storage logic internally.

