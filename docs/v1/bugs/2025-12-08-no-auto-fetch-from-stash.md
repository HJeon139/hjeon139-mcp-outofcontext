# Issue: Agent lacks auto-fetch trigger for stashed context when context is empty

**Date**: 2025-12-08  
**Severity**: Medium  
**Component**: MCP UX / retrieval  
**Status**: Open

## Description
When the active context is cleared or missing, the agent has no built-in signal or rule to automatically search and retrieve relevant stashed segments. The MCP server doesn’t indicate when the platform is running out of context, and the agent must be explicitly instructed to call `context_search_stashed` / `context_retrieve_stashed`. This can leave useful stashed context unused after a reset or context flush.

## Reproduction
1. Stash segments for a task.
2. Clear/lose active context (or start a new session) without explicit retrieval instructions.
3. The agent does not auto-fetch; stashed context remains unused.

## Expected Behavior
- When active context is missing or after a reset, the agent should have a trigger or rule to search stashed context (by task/tag) and optionally retrieve key segments.
- A simple heuristic (e.g., on session start, after reset, or when working set is empty) should prompt a search/retrieve suggestion.

## Actual Behavior
- No automatic trigger; retrieval happens only if explicitly requested.

## Impact
- Important stashed context may be overlooked after context flushes.
- Extra user effort to rehydrate context; risk of lost continuity.

## Proposed Solution (if known)
- Add a lightweight policy: when working set is empty or task switches, call `context_search_stashed` (filtered by task/tag) and surface suggested `context_retrieve_stashed` calls.
- Optionally include a reminder in monitoring responses when token usage is near zero or working set is empty.
- Keep implementation minimal; no new dependencies required.

## Notes
- Related to proactive warnings, but focuses on retrieval after context loss rather than token thresholds.

