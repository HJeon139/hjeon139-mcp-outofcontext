# Design: GC-Inspired Heuristic Pruning for Context Management

## 1. Scope & Goals

### What This Design Covers

This design document translates the research in `docs/research/garbage_collection_patterns.md` into **actionable design patterns** and **concrete implementation building blocks** for the Context Management MCP server, with a focus on:

- GC-inspired context pruning using **lightweight heuristics**.
- Operating at **millions of tokens** without heavy infrastructure (no vector DBs, no large ML deps).
- In-memory + JSON-based storage that is easy to reason about and debug.
- Clear MCP tools that expose GC-style capabilities to the agent.

### Non-Goals

- Not designing vector/embedding-based retrieval (covered in `rag_patterns_context_management.md` and deferred by requirements).
- Not designing the full storage abstraction (only the pieces needed for GC-style pruning).
- Not designing platform integration (handled in `architecture_platform_integration.md`).
- Not selecting final scoring coefficients; we define patterns and knobs, not exact numbers.

---

## 2. Core Idea: GC Patterns for Context, Not Memory

### Conceptual Mapping

- **Objects → Context Segments**  
  Each “object” in GC becomes a **context segment**:
  - Conversation messages
  - Code snippets / file fragments
  - Logs or trace chunks
  - Notes, decisions, summaries

- **Roots → Essential Context**  
  Root sets define context that must be preserved:
  - Current task / goal state
  - Active file & recent edited region
  - Last N user/assistant exchanges
  - Pinned / protected segments
  - Session invariants (project overview, constraints)

- **References → Links Between Segments**  
  Lightweight links replace pointers:
  - Explicit: `segment_id` references, “derived from X”, reply threading.
  - Implicit: same file path/function, shared tags (`bug-123`), topic IDs.

- **Reachability → Still-Relevant Context**  
  Segments reachable from roots via links (and not “expired” by simple heuristics) are **candidates to keep**. Others are candidates to **stash or prune**.

### Design Principle

> **Use GC-style reachability + simple heuristics (recency, type, refcount, generation) as the default pruning strategy, without embeddings or vector DBs.**

---

## 3. Data Model & In-Memory Structures

### 3.1 Context Segment Model

Minimal Python model (structurally, not final types):

```python
class ContextSegment(BaseModel):  # Pydantic model
    segment_id: str
    text: str
    type: Literal["message", "code", "log", "note", "decision", "summary"]

    created_at: datetime
    last_touched_at: datetime

    pinned: bool = False
    generation: Literal["young", "old"] = "young"
    gc_survival_count: int = 0

    refcount: int = 0

    file_path: str | None = None
    line_range: tuple[int, int] | None = None
    tags: list[str] = []
    topic_id: str | None = None
```

### 3.2 GC Metadata Structures

```python
# Reachability graph (lightweight)
references: dict[str, set[str]] = {}   # from_id -> {to_id, ...}
backrefs: dict[str, set[str]] = {}     # to_id   -> {from_id, ...}

# Segment lookup
segments: dict[str, ContextSegment] = {}
```

### 3.3 Storage Layer (MVP)

- **Active segments**: `segments` dict in memory.
- **Stashed segments**: JSON file on disk:
  - Path configurable (e.g. `artifacts/context_stash.json`).
  - Structure: `{"segments": [ContextSegment, ...]}`.
- **No SQL / vector DB** in this pattern; fully aligned with `docs/requirements.md`.

**Dependencies**:

- `pydantic` for schema/validation (`ContextSegment`).
- Standard library: `datetime`, `json`, `uuid`, `typing`, `pathlib`.

---

## 4. GC-Inspired Algorithms

### 4.1 Root Computation

Roots come from:

- **Platform integration layer** (via MCP adapters):
  - Active file + selection/line range.
  - Recently opened/edited files.
- **MCP server state**:
  - Current task/goal segment(s).
  - Last N interaction segments.
  - Pinned segments (user or agent pinned).

API-style pseudo-code:

```python
def compute_roots(state: ServerState) -> set[str]:
    roots: set[str] = set()
    roots |= state.current_task_segment_ids
    roots |= state.last_n_message_ids  # sliding window
    roots |= state.pinned_segment_ids
    roots |= state.active_file_context_segment_ids
    return roots
```

### 4.2 Mark Phase

```python
def mark_reachable(roots: set[str]) -> set[str]:
    reachable: set[str] = set()
    stack: list[str] = list(roots)

    while stack:
        seg_id = stack.pop()
        if seg_id in reachable:
            continue
        reachable.add(seg_id)
        for child_id in references.get(seg_id, ()):
            if child_id not in reachable:
                stack.append(child_id)

    return reachable
```

### 4.3 Sweep Phase (Prune / Stash)

Inputs:

- `reachable`: result of mark phase.
- Token budget: from requirements (e.g. millions of tokens window with soft limit).
- Simple scoring function (Section 5).

Steps:

1. Build candidate list of **non-root**, **non-pinned** segments.
2. Sort by score (lowest first).
3. For segments **not in reachable**:
   - Prune or stash first.
4. If still over budget, consider reachable but low-score segments:
   - Prefer **stashing** over deletion.
   - For medium-score but verbose segments, use **compression pattern** (LLM-driven).

This is implemented as a **single pass + sort** over at most a few thousand segments, which is acceptable for millions of tokens.

---

## 5. Heuristic Scoring (No ML)

### 5.1 Score Inputs

For each `ContextSegment`:

- **Recency**:
  - `age_steps = now_step - created_step`
  - `last_touched_age = now_step - last_touched_step`
- **Type/Importance**:
  - Decisions / notes / summaries > logs.
- **Refcount**:
  - Higher refcount → more important.
- **Generation**:
  - Young/old to bias toward pruning short-lived noise.
- **Pinned**:
  - Pinned segments are excluded from pruning.

### 5.2 Conceptual Score

```python
def compute_score(seg: ContextSegment, now: datetime) -> float:
    if seg.pinned:
        return float("inf")  # never prune in normal GC

    recency = 1.0 / (1.0 + seconds_since(seg.last_touched_at, now))
    importance = {
        "decision": 1.0,
        "note": 0.8,
        "summary": 0.7,
        "code": 0.6,
        "message": 0.5,
        "log": 0.2,
    }.get(seg.type, 0.4)
    ref_factor = min(seg.refcount / 5.0, 1.0)
    gen_bonus = 0.1 if seg.generation == "young" else 0.0

    return 0.4 * recency + 0.3 * importance + 0.2 * ref_factor + 0.1 * gen_bonus
```

**Policy**: Segments with the **lowest score** are pruned or stashed first.

---

## 6. Incremental vs. Stop-the-World Strategies

### 6.1 Incremental GC (Default)

- Run a **small GC step**:
  - On each MCP tool call that updates context.
  - Or every N tool calls / messages.
- GC step:
  1. Update ages/last_touched for affected segments.
  2. Recompute scores for a small subset (e.g. recently changed + a sample of old segments).
  3. If above soft token threshold:
     - Prune/stash a small batch (e.g. 5–20 segments).

This keeps latency small and spreads cost over time.

### 6.2 Threshold-Triggered Full GC

- When:
  - Approaching hard context limit (e.g. 90% of window), or
  - Agent explicitly calls a “cleanup” tool.
- Run a full:
  - Root computation.
  - Mark-and-sweep.
  - Score-based pruning until comfortably under budget.

---

## 7. MCP Tool Design

### 7.1 Tool Overview

Proposed GC-related tools (names TBD but illustrative):

- **`context_gc_analyze`**  
  - **Input**: Optional parameters (max_candidates, include_scores, dry_run).  
  - **Output**:
    - Token usage summary (current, soft limit, hard limit).
    - Candidate segments to prune/stash with:
      - `segment_id`, type, score, tokens.
      - Reason: “old + low refcount”, “unreachable”, etc.

- **`context_gc_prune`**  
  - **Input**:
    - List of `segment_id`s to prune or stash.
    - Strategy (`"delete"` / `"stash"` / `"auto"`).
  - **Output**:
    - What was deleted vs. stashed.
    - Token savings estimate.

- **`context_gc_pin` / `context_gc_unpin`**  
  - Manage `pinned` flag on segments and adjust root sets.

- **`context_gc_configure`** (optional, phase 2)  
  - Adjust thresholds:
    - soft/hard token limits.
    - recency windows.
    - max batch size per GC step.

### 7.2 Tool Behavior Principles

- **Explainability**:
  - Always return **why** a segment is being suggested for pruning.
  - Provide a **before/after token usage** summary.

- **Agent Control**:
  - Agent can:
    - Ask for analysis only (`dry_run`).
    - Approve/prune specific segments.
    - Pin segments to protect them.

- **Safety**:
  - Default to **stashing** instead of deleting when uncertain.
  - Deletion reserved for clearly unused, low-score segments or explicit agent request.

---

## 8. Dependencies & Libraries

Aligned with `docs/requirements.md` (lightweight, minimal deps):

- **Core**:
  - `mcp` SDK – to expose tools.
  - `pydantic` – for `ContextSegment` and tool schemas.
  - `tiktoken` – for token counting and budgets.
- **Standard Library**:
  - `datetime`, `uuid`, `json`, `typing`, `pathlib`, `dataclasses` (if desired).

**Explicitly Not Required for This Pattern**:

- Vector DBs (`faiss`, `qdrant`, `chromadb`).
- Large embedding libraries (`sentence-transformers`, etc.).
- SQL databases (Postgres/MySQL).

---

## 9. Integration with Other Designs

### 9.1 With LLM-Driven Compression

- GC identifies **which** segments are safe to:
  - Delete,
  - Stash, or
  - Compress.
- LLM compression pattern (`llm_driven_context_compression.md`) defines:
  - How to paraphrase segments while preserving file paths, line ranges, and recency.
- Combined flow:
  1. GC marks a reachable but verbose segment as “cold but important”.
  2. Agent calls compression tool to shrink it.
  3. GC treats compressed segment as a normal segment with lower token cost.

### 9.2 With RAG Patterns

- GC pattern runs **without** embeddings or vector DBs.
- If later we enable RAG for long-term stashed context:
  - GC decisions still stand.
  - Stashed segments may additionally be embedded and indexed for semantic retrieval.

### 9.3 With Platform Integration

- Roots and segment metadata can be enriched by:
  - Active editor (file/line) from Cursor or similar.
  - Open tabs, breakpoints, etc.
- GC tools use this platform-enriched context to avoid pruning critical working state.

---

## 10. Summary

This design defines a **GC-inspired, heuristic-first pruning layer** for the Context Management MCP server that:

- Works entirely with **in-memory structures + JSON storage**.
- Uses **roots, reachability, generations, and refcounts** to guide pruning.
- Relies on a **simple scoring function**, not embeddings or vector DBs.
- Exposes clear, explainable MCP tools for analysis and pruning.

It should be treated as a **baseline pruning pattern** that we can layer more advanced techniques (compression, RAG) on top of, while staying faithful to the lightweight dependency and millions of token constraints in `docs/requirements.md`.


