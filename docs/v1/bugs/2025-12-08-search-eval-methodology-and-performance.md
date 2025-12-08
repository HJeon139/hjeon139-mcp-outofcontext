# Issue: Search evaluation methodology and performance tracking for MCP memory

**Date**: 2025-12-08  
**Severity**: Low  
**Component**: MCP UX / evaluation  
**Status**: Open

## Description
We need to formalize and repeatably measure MCP search/memory performance (recall and latency) at a known scale to demonstrate efficacy as a context/memory tool. Current ad-hoc tests show good recall for design corpus queries, but we lack a documented methodology, performance baselines, and statistical significance from repeated runs.

## Reproduction / Current Method (baseline)
- Scope: `docs/v1/design` corpus (11 files ingested as summaries + file pointers) under task `design-corpus`.
- Tool flow per query: `context_search_stashed` with `task_id=design-corpus` and keyword query.
- Sample queries and intended targets:
  - “architectural decisions” → summary of `03_architectural_decisions.md`
  - “integration patterns” → summary of `05_integration_patterns.md`
  - “scalability” → summary of `10_scalability_analysis.md`
- Observed recall (manual spot checks): 3/3 intended matches returned; results also include the overall design summary (expected).
- Latency: not yet instrumented; single-run perceived latency acceptable, but no timing recorded.

## Impact
- Without a defined methodology and metrics, we can’t claim performance or reliability.
- Lack of repeated measurements means no statistical significance or tracking of regressions.

## Proposed Solution
- Define a repeatable test script or manual protocol:
  - Ingest a known corpus (e.g., `docs/v1/design` summaries + file pointers).
  - Run a fixed query set (≥10 queries) mapped to expected targets.
  - Record recall@k (e.g., did the expected segment appear in top-3), precision (optional), and latency (wall-clock from tool call).
  - Repeat N runs (e.g., 10) to gather basic statistics (mean/median latency, recall consistency).
- Capture scale info for each run:
  - Corpus size: number of segments, total tokens stashed.
  - Query count and limit (e.g., limit=5).
- Instrument or log latency per `context_search_stashed` call (client-side timing if server timing not exposed).
- Document findings in the bug file or a linked log, including any misses or slow queries.

## Current Findings (qualitative)
- Scale: ~11 design files ingested as summaries + file pointers (task `design-corpus`), with additional stashed transcript segments; total tokens small (<10k).
- Recall: spot checks for 3 design queries returned correct summaries in results.
- Latency: perceived acceptable, but unmeasured.
- Utility: MCP server works as a memory store for tagged, task-scoped stashed context; search is adequate for keyword/metadata but manual tagging and explicit search are required.

## Initial Measured Run (single pass, no timing)
- Corpus under test: task `design-corpus`, stashed summaries + file pointers for 11 design files (~22 segments; ~1–2k tokens est).
- Query set (1 pass, limit=3–5): `core architecture`, `research findings`, `architectural decisions`, `integration patterns`, `components`, `design patterns`, `constraints performance 500ms`, `scalability`.
- Recall@k (k<=5): 8/8 intended targets present in top results; extra overall-summary segment often accompanies results (expected given broad terms).
- Latency: not captured (tool API lacks timing); needs client-side timing in future runs.
- Precision observations: minor “extra” overall-summary hit; otherwise focused.

## Next Steps to Reach Significance
- Instrument client-side timing (wall-clock) per `context_search_stashed`.
- Expand query set to ~20–30, including misspellings/near-miss, empty query, tag/task-only, and time-filter cases.
- Run 5–10 passes; record recall@k, note spurious hits; compute mean/median/p95 latency.
- Log corpus size at test time (segment count, tokens) for comparability.

## Outstanding Issues / Risks
- No automatic timing/metrics; cannot prove latency targets (<500ms) at larger scales.
- No statistical significance: only a handful of queries tested once.
- Search is keyword/metadata only; semantic gaps may appear for fuzzier queries.
- Manual ingestion/tagging required; omissions can hurt recall.

## Acceptance Criteria
- A documented, repeatable search-eval procedure with query set, expected targets, and metrics.
- At least one recorded run with:
  - Corpus size metrics (segments, tokens)
  - Recall@k for each query
  - Latency (mean/median) across queries
- Notes on any misses or anomalies, plus assessment of utility as a memory/context tool.

## Notes
- Related to prior bug tasks on auto-fetch and stashing policy; this focuses on measuring recall/latency to demonstrate effectiveness. 

