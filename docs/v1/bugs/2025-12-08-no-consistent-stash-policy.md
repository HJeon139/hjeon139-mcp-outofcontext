# Issue: No enforced policy to stash both user prompts and LLM outputs consistently

**Date**: 2025-12-08  
**Severity**: Medium  
**Component**: MCP UX / workflow  
**Status**: Open

## Description
There is no built-in mechanism or policy ensuring both user prompts and LLM outputs (plus additional context from file reads or CLI runs) are consistently stashed. Stashing is manual and easy to miss, which can lead to gaps after context flushes or task switches. Unlike “no-auto-fetch-from-stash” (retrieval gap), this issue is about capture discipline: the agent may forget to stash both sides of each exchange and ancillary context.

## Reproduction
1. Conduct a session where some prompts/responses are stashed manually.
2. Run additional commands or read files without stashing their context.
3. Later, after reset, parts of the session are missing because they were never stashed.

## Expected Behavior
- A lightweight, enforced or guided policy that stashes both user and assistant messages (and key file/CLI outputs) per prompt, so the transcript and derived context are complete.
- Clear reminders or automation to stash after each prompt/response pair or when new context is added.

## Actual Behavior
- Stashing is ad hoc; prompts or assistant replies (or CLI/file context) can be skipped, creating gaps.

## Impact
- Loss of continuity after context resets; incomplete session rehydration from stashed storage.

## Proposed Solution (if known)
- Add a simple rule/hook: after each prompt/response pair, call `context_stash` for both messages; when files/CLI outputs are read, create segments and stash them too.
- Optionally add a tool description reminder or a small helper tool to bundle and stash the most recent prompt/response/context in one call.
- Keep dependencies minimal; leverage existing stashing tools and task_id tagging.

## Notes
- Related to `2025-12-08-no-auto-fetch-from-stash` but focuses on capture (stash) rather than retrieval triggers. 

