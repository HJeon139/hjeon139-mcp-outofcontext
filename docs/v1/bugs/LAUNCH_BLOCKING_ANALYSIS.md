# Launch Blocking Analysis

**Date**: 2025-12-08
**Status**: Pre-Launch Review

## Summary

After reviewing all v1 bugs against requirements, **3 bugs are launch-blocking**:

### 🚨 Launch-Blocking Bugs

1. **2025-12-08-missing-proactive-limit-warnings.md** - **BLOCKING**
   - **Requirement**: #5 states "MUST provide proactive suggestions/notifications to the agent about what can be pruned"
   - **Current State**: No proactive warnings or threshold-based suggestions
   - **Impact**: High risk of hitting context limits without agent awareness
   - **Fix Complexity**: Low - can be fixed with prompt engineering and threshold config

2. **2025-12-08-no-cross-session-stash-retrieval.md** - **BLOCKING**
   - **Requirement**: Core functionality - persistent context storage must be retrievable across sessions
   - **Current State**: Cannot retrieve stashed context from different chat window/session (no project discovery)
   - **Impact**: Breaks core use case - stashed context becomes inaccessible across sessions
   - **Fix Complexity**: Medium - requires adding project discovery tool and/or making project_id optional

3. **2025-12-08-token-limit-defaults-to-32k-instead-of-1m.md** - **BLOCKING**
   - **Requirement**: Must support at least 1 million tokens to match Cursor's native chat context size
   - **Current State**: Config defines 1 million tokens but tools default to 32k everywhere
   - **Impact**: System only stores 32k tokens instead of 1 million - fails to meet parity requirement
   - **Fix Complexity**: Medium - need to thread config token_limit through AppState → tools → analysis engine

### ✅ Non-Blocking Bugs (Can Launch Without)

The following bugs are **NOT launch-blocking** but should be addressed post-launch:

#### Already Implemented (Bug Reports Deleted)
- **2025-12-08-no-high-priority-protection-tool.md** - ✅ **FIXED & DELETED**
  - Pin/unpin tools (`context_gc_pin`, `context_gc_unpin`) are implemented
  - Pruning logic respects `pinned` flag
  - Bug report deleted as it was already fixed
  
- **2025-12-08-no-protection-tools-enforced.md** - ✅ **FIXED & DELETED**
  - Protection is enforced in pruning logic
  - Bug report deleted as it was already fixed

#### Low Severity / Post-Launch Improvements
- **2025-12-08-llm-drafting-latency.md** - Low severity, UX improvement
- **2025-12-08-tool-feedback-lacks-impact.md** - Low severity, prompt engineering
- **2025-12-08-search-eval-methodology-and-performance.md** - Low severity, evaluation/testing

#### Medium Severity / Workflow Improvements (Post-Launch)
- **2025-12-08-no-auto-fetch-from-stash.md** - Policy improvement, not blocking
- **2025-12-08-no-auto-rehydrate-when-empty.md** - Policy improvement, not blocking
- **2025-12-08-no-combined-ingest-stash-helper.md** - Workflow optimization, not blocking
- **2025-12-08-no-consistent-stash-policy.md** - Policy improvement, not blocking
- **2025-12-08-slow-mcp-workflow-multiple-calls.md** - Performance improvement, not blocking
- **2025-12-08-no-latency-instrumentation-or-scale-validation.md** - Monitoring improvement, not blocking

## Required Actions Before Launch

### 1. Fix Proactive Limit Warnings (BLOCKING)

**File**: `docs/v1/bugs/2025-12-08-missing-proactive-limit-warnings.md`

**Implementation**:
- Add threshold configuration (60%, 80%, 90%)
- Modify `context_analyze_usage` to include warnings when thresholds crossed
- Add recommended follow-up tool calls in response
- Update tool descriptions with threshold guidance

**Estimated Effort**: Low (prompt engineering + response formatting)

### 2. Fix Cross-Session Stash Retrieval (BLOCKING)

**File**: `docs/v1/bugs/2025-12-08-no-cross-session-stash-retrieval.md`

**Implementation**:
- Add `context_list_projects` tool to discover available project IDs
- Make `project_id` optional in `context_search_stashed` (search across all projects when omitted)
- Expose project discovery functionality from storage layer

**Estimated Effort**: Medium (new tool + optional parameter handling)

### 3. Fix Token Limit Defaults (BLOCKING)

**File**: `docs/v1/bugs/2025-12-08-token-limit-defaults-to-32k-instead-of-1m.md`

**Implementation**:
- Extract `token_limit` from config in `AppState.__init__`
- Expose `token_limit` via `AppState` to tools
- Update all hardcoded `32000` defaults to use config value
- Update `AnalyzeUsageParams` to use config default instead of 32k
- Update analysis engine function defaults to use config value

**Estimated Effort**: Medium (config integration + threading through codebase)

### 4. Fixed Bugs (Completed)

**Files** (deleted):
- `docs/v1/bugs/2025-12-08-no-high-priority-protection-tool.md` - ✅ Deleted
- `docs/v1/bugs/2025-12-08-no-protection-tools-enforced.md` - ✅ Deleted

**Action**: Bug reports deleted as pin/unpin tools are already implemented

## Launch Readiness

**Status**: ⚠️ **NOT READY** - 3 blocking bugs

**Blocking Issues**: 3
**Non-Blocking Issues**: 9 (2 fixed bugs have been deleted)

**Recommendation**: Fix all three blocking bugs before launch:
1. Proactive limit warnings (low complexity)
2. Cross-session stash retrieval (medium complexity - project discovery)
3. Token limit defaults (medium complexity - config integration)

All other bugs can be addressed post-launch as improvements.

## References

- [Requirements](../v0/requirements.md) - Original requirements document
- [Bug Classification](./CLASSIFICATION.md) - V1 vs V2 classification
- [V1 Bugs](./) - All v1 bug reports

