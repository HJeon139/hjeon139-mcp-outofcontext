# Issue: No latency instrumentation or scale validation vs. performance targets

**Date**: 2025-12-08  
**Severity**: Medium  
**Component**: performance / monitoring  
**Status**: Open

## Description
We have performance targets (<2s analysis, <500ms search, <100ms token counting), but we don’t instrument MCP tool latency or validate at realistic scales. Current tests are qualitative and small; no timing is recorded, and no large-corpus runs exist.

## Impact
- Cannot verify compliance with performance requirements.
- No baseline to detect regressions or to justify optimizations (indexing/sharding).
- Risk of poor UX at scale without early detection.

## Proposed Solution (if known)
- Add client-side timing to MCP tool calls (at least search/analyze/stash/get) and capture mean/median/p95.
- Run perf sweeps on larger corpora (tens/hundreds of thousands of segments) to validate or refute targets.
- Log corpus size (segments/tokens) with results; repeat periodically or in CI perf jobs if feasible.

