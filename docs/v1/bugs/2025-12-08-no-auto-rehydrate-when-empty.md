# Issue: No auto-rehydrate/search when working set is empty or after reset

**Date**: 2025-12-08  
**Severity**: Medium  
**Component**: retrieval / UX  
**Status**: Open

## Description
When context is cleared or working set is empty, the agent doesn’t automatically search stashed context to rehydrate. Retrieval requires manual search/retrieve calls. There’s no built-in trigger or reminder to restore context by task/tag.

## Impact
- Useful stashed context may stay unused after reset.
- Extra user effort to recover continuity; risk of missing critical history.

## Proposed Solution (if known)
- Add a simple policy/tool: when working set is empty or task changes, auto-run `context_search_stashed` (by task/tag) and suggest `context_retrieve_stashed` calls.
- Optionally emit a reminder in monitoring outputs when usage is near zero or working set is empty.

