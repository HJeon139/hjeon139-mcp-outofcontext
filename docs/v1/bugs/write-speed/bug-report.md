# Bug Report: Slow Write Performance with put_context

**Reported By:** Customer/User  
**Date:** 2024-12-16  
**Severity:** Medium  
**Component:** MCP Tool - put_context  
**Status:** Investigating

---

## Summary

The `put_context` MCP tool is significantly slower than expected, creating noticeable latency during agent sessions. This impacts user experience, especially when updating contexts frequently.

---

## User Experience Impact

### Observed Behavior

During a typical development session today (Developer Action Item 00), I used `put_context` **4 times** to update contexts:

1. Creating `action-items-revised` context (~5000 tokens)
2. Updating `current-status` context (~3000 tokens)
3. Updating `decision-log` context (~4000 tokens)
4. Creating `session-2024-12-16-developer-00-complete` (~2000 tokens)

**Each operation took noticeably longer than expected** - estimated 1-3 seconds per call. Total time spent waiting: **~5-10 seconds per session**.

### When It Hurts Most

**Scenario 1: Frequent Status Updates**
- Agent updates `current-status` after each sub-task
- 10 updates per session = 10-30 seconds wasted
- Breaks flow, feels sluggish

**Scenario 2: Creating Large Contexts**
- Large contexts (5K+ tokens) take longest
- Creates perception of "hanging" tool

**Scenario 3: Bulk Operations**
- Updating multiple contexts in sequence
- Latency compounds (4 updates = 4-12 seconds)

---

## Expected vs Actual Performance

### Expectations
- **Write operation:** < 100ms (file write is typically ~10ms)
- **MCP tool overhead:** < 50ms
- **Total expected:** < 150ms per put_context call

### Reality (Estimated)
- **Actual observed:** 1-3 seconds per call
- **10-20x slower** than expected
- **Noticeable lag** in agent interaction

---

## Comparison: File System Operations

### Direct File Operations (using write/search_replace tools)
During the same session, I also created files directly:
- Created `00-database-choice-decision.md` (400+ lines) - **felt instant**
- Created `test_chromadb.py` (176 lines) - **felt instant**
- Created `test_lancedb.py` (183 lines) - **felt instant**

**Observation:** Direct file operations via `write` tool feel **much faster** than `put_context`.

---

## Impact on Workflow

### Current Workflow
```
1. Complete subtask (e.g., database selection)
2. put_context("current-status", ...) → WAIT 2-3 seconds
3. put_context("decision-log", ...) → WAIT 2-3 seconds
4. Continue work
```

**Problem:** The wait times break concentration and make the tool feel "heavy".

### Desired Workflow
```
1. Complete subtask
2. Update contexts → Should feel instant (< 200ms)
3. Continue work seamlessly
```

---

## User Questions/Concerns

### Question 1: Why is put_context slow?
- Is it serialization (converting to MDC format)?
- Is it file I/O?
- Is it validation overhead?
- Is it MCP protocol overhead?

### Question 2: Do we need the MCP abstraction?
- LLMs are now excellent at direct file operations
- Could we just use `write` tool to edit `.mdc` files directly?
- Would that be faster AND simpler?

### Question 3: Impact on future semantic search?
- If we're building a vector database layer...
- Should we even use MCP tools for context management?
- Could we just:
  - Use direct file edits for `.mdc` files
  - Let file watcher + vector DB handle indexing
  - Skip the MCP tool layer entirely

---

## Reproducibility

### To Reproduce
1. Use `put_context` with a large context (~5000 tokens)
2. Observe response time
3. Compare to equivalent `write` operation on `.mdc` file

### Hypothesis
The issue is likely in one of:
- MDC serialization overhead
- MCP protocol round-trip time
- File write synchronization
- Validation logic in the tool

---

## Customer Perspective

### What I Care About
1. **Speed** - Tools should feel instant (< 200ms)
2. **Simplicity** - Fewer abstractions = fewer points of failure
3. **Reliability** - File system ops are rock-solid, MCP adds complexity

### What I Don't Care About
- Whether it's MCP or direct file ops - just want it to work fast
- Format abstractions - LLMs can handle raw `.mdc` format fine

### What Would Make Me Happy
**Option A: Fix put_context**
- If it can be < 200ms, great! Keep using it.

**Option B: Remove MCP tools, use direct file ops**
- Simpler architecture
- Faster (proven by today's experience)
- LLMs handle file create/edit/delete well now
- File watcher handles indexing automatically

---

## Related Observations

### LLM Capability Evolution
**2023:** LLMs needed structured tools, struggled with file formats  
**2024:** LLMs excel at:
- Creating/editing markdown with YAML frontmatter
- Direct file system operations
- Understanding file structure without abstraction

**Implication:** Maybe we don't need the MCP tool layer anymore?

### Future Vector Database Integration
If we're adding:
- File watcher (detects `.mdc` changes)
- Automatic indexing (embeds contexts on change)
- Vector database (stores embeddings)

**Then why do we need MCP tools at all?**

Could simplify to:
```
Agent → write .mdc file → File watcher → Vector DB updates → Done
Agent → semantic search → Vector DB query → Results
```

No `put_context`, `get_context`, `list_context`, `delete_context` tools needed!

---

## Next Steps (Customer Request)

1. **Investigate:** Root cause analysis of put_context slowness
2. **Benchmark:** Compare put_context vs direct file write performance
3. **Evaluate:** Should we deprecate MCP tools in favor of file ops?
4. **Decide:** Impact on database integration architecture

---

## Customer Vote

**My preference:** Move to direct file operations
- **Reason 1:** Faster (proven today)
- **Reason 2:** Simpler (fewer abstractions)
- **Reason 3:** Better fit for vector DB integration (file watcher model)
- **Reason 4:** LLMs are now good enough to handle it

**Caveat:** Open to keeping MCP tools if performance can match file ops.

---

**Priority:** Medium (impacts UX but not blocking)  
**Assigned To:** Engineering team  
**Next Action:** Root cause analysis + performance benchmarking

