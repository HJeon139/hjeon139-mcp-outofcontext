# Bug Classification Summary

This document summarizes the classification of bug reports into v1 bugfixes (kept in this directory) vs v2 feature improvements (moved to `docs/v2/requirements/`).

## Classification Criteria

### V1 Bugfixes (Remain in `docs/v1/bugs/`)
- Can be fixed with **prompt engineering** improvements
- Can be fixed with **workflow optimizations** (combined tools, helpers)
- Address **requirements** that are in v1 scope
- Improve **keyword + metadata search** (not semantic)
- Add **protection/pinning tools** (requirements call for this)
- Add **performance instrumentation** and monitoring
- Improve **policies** (auto-fetch, consistent stashing)

### V2 Requirements (Moved to `docs/v2/requirements/`)
- Require **semantic search** or vector databases (explicitly deferred)
- Require **fuzzy matching** or advanced ML capabilities
- Require **semantic understanding** for context reconstruction
- Add substantial dependencies beyond minimal v1 set

## V1 Bugfixes (10 items)

1. **2025-12-08-llm-drafting-latency.md** - UX issue, fixable with prompt engineering and helper tools
2. **2025-12-08-missing-proactive-limit-warnings.md** - Requirements call for this, fixable with threshold config and prompt engineering (BLOCKING - see Task 13)
3. **2025-12-08-no-auto-fetch-from-stash.md** - Policy improvement, fixable with prompt engineering
4. **2025-12-08-no-auto-rehydrate-when-empty.md** - Policy improvement, fixable with prompt engineering
5. **2025-12-08-no-combined-ingest-stash-helper.md** - Workflow improvement, can add helper tool
6. **2025-12-08-no-consistent-stash-policy.md** - Policy improvement, fixable with prompt engineering
7. **2025-12-08-no-latency-instrumentation-or-scale-validation.md** - Performance monitoring, v1 scope
8. **2025-12-08-search-eval-methodology-and-performance.md** - Evaluation/testing, v1 scope
9. **2025-12-08-slow-mcp-workflow-multiple-calls.md** - Workflow improvement, fixable with combined tools
10. **2025-12-08-tool-feedback-lacks-impact.md** - Prompt engineering improvement, v1 scope

## Fixed/Removed Bugs

- **2025-12-08-no-high-priority-protection-tool.md** - ✅ **FIXED** - Pin/unpin tools (`context_gc_pin`, `context_gc_unpin`) are implemented
- **2025-12-08-no-protection-tools-enforced.md** - ✅ **FIXED** - Protection is enforced in pruning logic

## V2 Requirements (2 items)

1. **2025-12-08-context-reconstruction-inefficiency.md** - Core solutions require semantic search and advanced retrieval strategies
2. **2025-12-08-no-semantic-or-fuzzy-search.md** - Semantic search explicitly deferred per architectural decisions

## Rationale

The two items moved to v2 both require semantic search capabilities, which are explicitly deferred to v2 per:
- [Architectural Decisions](../design/03_architectural_decisions.md) - Semantic search deferred to v2
- [Deferred Features](../design/08_deferred_features.md) - Semantic search and vector databases deferred

The v1 bugfixes can all be addressed within the current v1 scope using:
- Prompt engineering improvements
- Workflow optimizations (combined tools, helpers)
- Policy improvements (auto-fetch, consistent stashing)
- Basic keyword search improvements (not semantic)
- Protection/pinning tools (requirements call for this)

## References

- [V2 Requirements README](../../v2/requirements/README.md) - V2 classification criteria
- [V1 Deferred Features](../design/08_deferred_features.md) - Features explicitly deferred to v2
- [Architectural Decisions](../design/03_architectural_decisions.md) - Decisions that define v1 scope

