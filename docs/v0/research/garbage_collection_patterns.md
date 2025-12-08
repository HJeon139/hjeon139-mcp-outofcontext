# Research: Garbage Collection Patterns for Context Management

## Research Objective

Understand how garbage collection patterns from programming languages can be applied to context management, identifying unused or irrelevant context segments for removal.

## Research Questions

1. **GC Concepts Applicable to Context**
   - How do reference counting patterns apply to context?
   - What constitutes "unused" context in an agent session?
   - How do we track context references/dependencies?
   - What's the equivalent of "object reachability" for context?

2. **Mark-and-Sweep Approaches**
   - What context should be "marked" as reachable/important?
   - How do we identify roots (essential context that must be kept)?
   - What's the sweep phase for context (removal strategy)?
   - How do we handle cycles in context dependencies?

3. **Generational GC Patterns**
   - Can we treat recent context differently from old context?
   - What's the temporal component of context relevance?
   - How do we implement generational context collection?
   - What heuristics determine context age/relevance?

4. **Reference Counting for Context**
   - How do we count references to context segments?
   - What makes context referenced vs. unreferenced?
   - How do we handle weak references (nice-to-have context)?
   - What's the overhead of reference tracking?

5. **GC Algorithms**
   - Which GC algorithms translate best to context management?
   - What are the trade-offs (CPU vs. memory, latency vs. throughput)?
   - How do incremental GC patterns work for context?
   - What's the equivalent of "stop-the-world" for context pruning?

## Deliverables

- [x] **Pattern Mapping**: GC concepts mapped to context management
- [x] **Algorithm Selection**: GC-style patterns suited for millions of token context
- [x] **Implementation Design**: How to implement GC-inspired context pruning with lightweight heuristics
- [x] **Performance Analysis**: Trade-offs and optimization opportunities
- [x] **Hybrid Approach**: How GC combines with other pruning and compression strategies

## Status

- ✅ Completed

## Key Findings

### 1. GC Concepts Map Cleanly to Context Management

**Objects → Context Segments**

- In memory GC, the unit is an object; for context GC, the unit is a **context segment**:
  - Conversation message
  - Code snippet or file fragment
  - Log chunk
  - Decision/note/summary
- Each segment should have:
  - `segment_id`
  - `type` (log, code, instruction, note, summary, etc.)
  - `created_at`, `last_touched_at`
  - Optional links to other segments, file paths, or line ranges
  - Flags: `pinned` / `priority`

**Roots → Essential Context**

- Analog of stack/global roots:
  - Current task/goal description
  - Active file and recent edited region
  - Last N user/assistant messages
  - Pinned / protected segments
  - Session invariants (project overview, constraints)
- These form the **root set**; they should not be pruned by default.

**References → Links Between Segments**

- Instead of pointers, we track **links** between segments:
  - Explicit links: “derived from X”, reply threading, explicit `segment_id` references
  - Implicit links (lightweight):
    - Same file path or function
    - Shared tags (e.g. `bug-123`, `perf`, `api-x`)
    - Shared “topic id”
- Implementation can use in-memory adjacency lists:
  - `references: dict[segment_id, set[segment_id]]`
  - `backrefs: dict[segment_id, set[segment_id]]`
- At our scale (tens of thousands of tokens), **no graph DB is required**.

**Reachability → Still-Relevant Context**

- A segment is **reachable** if:
  - It is a root, or
  - It can be reached from a root via reference edges
  - And it is not “expired” by simple temporal rules (very old, never touched, low priority)
- Unreachable segments are candidates for **stashing** or **deletion**.

**Implication**: GC concepts (roots, references, reachability) give us a structural backbone for deciding which context is still relevant, without requiring embeddings or heavy infrastructure.

### 2. Mark-and-Sweep Works Well with Lightweight Heuristics

**Mark Phase**

- Periodically (or when near context limits):
  1. Build root set:
     - Current task
     - Active file + recent edits
     - Last N messages
     - Pinned/protected segments
  2. Traverse `references` from each root to build `reachable: set[segment_id]`
  3. While traversing, compute:
     - Age (steps or time since created)
     - Time since last touched
     - Simple “cold” flag if not touched for a while

**Sweep Phase**

- For each segment:
  - If not in `reachable`:
    - Old and low priority → **delete**
    - Potentially useful later → **stash** (removed from active context, kept in storage)
  - If in `reachable` but verbose and older:
    - Candidate for **LLM-driven compression** (paraphrasing to shrink size but preserve recency and metadata)

**Lightweight Implementation**

- All data kept in memory + JSON persistence:
  - Dicts and sets, O(N) passes
  - No concurrent GC required; simple cooperative steps around tool calls are sufficient

**Implication**: A classic mark-and-sweep approach, combined with basic heuristics (recency, type, pinned flag), gives robust pruning that fits our low-dependency design.

### 3. Generational GC Matches Context Lifetimes

**Young vs. Old Generations**

- Observations:
  - Most segments (logs, transient debug messages) are short-lived.
  - A minority (goals, decisions, key summaries) are long-lived.
- We can mirror **generational GC**:
  - **Young generation**:
    - New segments
    - Recent messages, logs, edits
  - **Old generation**:
    - Survived multiple GC cycles while still used
    - Long-term notes, decisions, key summaries

**Simple Metadata**

- `generation: "young" | "old"`
- `gc_survival_count: int`

**Heuristics**

- New segments start in **young**.
- After N GC cycles where a segment remains reachable or touched:
  - Promote to **old** and treat as more stable.
- Run:
  - Young-gen GC **frequently** (cheap).
  - Full GC (young + old) only:
    - When approaching hard context limits.
    - Or on explicit user/agent request.

**Implication**: Generational patterns let us focus most pruning on short-lived “noise” (logs, partial experiments) while preserving long-lived structure with minimal overhead.

### 4. Reference Counting Helps Identify Unused Context

**What Counts as a Reference?**

- Each segment tracks:
  - How many other segments explicitly link to it.
  - How many times it has been:
    - Retrieved via a “recall” tool.
    - Used to answer a user question.
    - Included in active context segments.

- State:
  - `refcount: dict[segment_id, int]`
  - Optional `soft_refcount` for weaker/heuristic links.

**Heuristic Use of Refcounts**

- **Strong prune candidates**:
  - Old segments
  - Low `refcount`
  - Not near any root (no strong links)
- **Keep or compress, don’t delete**:
  - High `refcount`
  - Recently used in answers or decisions

**Overhead**

- Low: increments on tool events (store, retrieve, reuse).
- Works fine at our scale without elaborate data structures.

**Implication**: Reference counting gives a cheap, interpretable signal for “how much this context has mattered so far”.

### 5. Incremental vs. Stop-the-World for Context GC

**Stop-the-World Analogy**

- A naive context GC would:
  - Wait until context is nearly full.
  - Pause work and run a big global prune.
- Problems:
  - Latency spikes.
  - Risk of cutting context at awkward times (e.g., mid-debug).

**Incremental / Opportunistic GC (Preferred)**

- **Incremental GC steps** on normal operations:
  - On each tool call or every few messages:
    - Update ages and refcounts.
    - Recompute scores for a small subset of segments.
    - If above a soft token limit:
      - Prune or stash the lowest-scoring 1–N segments.
- **Threshold-triggered deeper sweeps**:
  - When context usage reaches a soft threshold (e.g. 70–80% of window):
    - Run a young-gen mark-and-sweep.

**Implication**: Incremental GC keeps the system responsive and predictable, with GC work spread over time and no heavy pauses.

### 6. Hybrid Heuristic Scoring (GC + Simple Signals)

Instead of a learned model, we can use a hand-tuned score:

- Inputs:
  - Recency (time/steps since last touch)
  - Type (decision/note vs. log/noise)
  - Refcount (how often used)
  - Generation (young vs. old)
  - Pinned flag (hard constraint)

**Policy**

- Build a candidate list of non-root, non-pinned segments.
- Sort by a simple score (recency + importance + refcount + generation bias).
- Drop or stash until under budget.

**Implication**: We can get most of the GC benefits using purely heuristic, explainable scoring; no embeddings or ML required for MVP.

## Design Implications for the MCP Server

1. **Explicit Roots and Segments**
   - Tools should expose operations over `segment_id`s, with clear root sets:
     - Task, active file, recent interactions, pinned segments.
2. **GC-Aware Tools**
   - Example tools:
     - `context_gc_analyze` – returns candidates for pruning/stashing with scores and reasons.
     - `context_gc_prune` – applies a pruning plan (with user/agent confirmation).
     - `context_gc_pin` / `context_gc_unpin` – manage roots/essential segments.
3. **Incremental Operation**
   - GC should primarily run as:
     - Small steps during context queries or updates.
     - Threshold-triggered sweeps, not constant full scans.
4. **Transparency**
   - Tools should return:
     - What was pruned/stashed.
     - Why it was selected (age, low refcount, not near roots).
     - Estimated token savings.

These patterns should be reflected in design docs as the **baseline pruning mechanism**, with attention/RAG/summarization layered on later.

## References

1. **Jones, Hosking, & Moss (2011)** – *The Garbage Collection Handbook: The Art of Automatic Memory Management*. Chapman & Hall/CRC. Comprehensive survey of mark-sweep, generational, incremental, and real-time GC algorithms.
2. **Uniprocessor Garbage Collection Techniques** – Paul R. Wilson, 1992. Classic technical report describing mark-sweep, copying, generational, and incremental collectors and their trade-offs.
3. **Automatic Memory Management in the Microsoft .NET Framework** – Microsoft Docs. Explains generations, roots, and mark-and-sweep/compact patterns used in modern runtimes.
4. **Java Garbage Collection Tuning Guide** – Oracle/Java documentation. Practical overviews of generational and incremental GC in HotSpot (Parallel, CMS, G1).
5. **CPython Memory Management and Garbage Collection** – Python documentation. Describes hybrid reference counting + cyclic GC, illustrating how reference counting and tracing can be combined.
