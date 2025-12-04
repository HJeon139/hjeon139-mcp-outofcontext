# Design: Human-Memory-Inspired Context Patterns

## 1. Scope & Goals

### What This Design Covers

This document translates the research in `docs/research/human_memory_models.md` into **actionable design patterns** for the Context Management MCP server. The goal is to make context management:

- More **human-like** (focus, forget, and recall like a good collaborator).
- Consistent with our **lightweight**, 32k–64k token, minimal-dependency constraints.
- Complementary to existing designs:
  - `gc_heuristic_pruning_patterns.md`
  - `llm_driven_context_compression.md`
  - `rag_patterns_context_management.md`

### Non-Goals

- Not a full architecture or API spec (see other design docs for that).
- Not a cognitive model of humans—this is **inspiration**, not simulation.
- Not a replacement for GC/RAG/compression patterns; this is a **lens** shaping how we use them.

---

## 2. Pattern: Chunked Segments (vs. Token Soup)

### Problem

Raw context often accumulates as long transcripts or logs. This:

- Makes it hard to reason about what is important.
- Encourages keeping everything until we hit token limits.
- Does not align with how humans think (in **chunks**, not raw tokens).

### Human Analogy

- Working memory operates on **chunks**—meaningful units like “a phone number”, “a bug investigation”, “a feature request”—rather than on raw symbols.

### Design Pattern

- **Represent context as structured segments**, not arbitrary slices:
  - `ContextSegment` already captures this (type, text, metadata).
  - Segments should correspond to **meaningful units**:
    - “Bug #123 investigation log”
    - “Auth flow decision note”
    - “Current hypothesis and next steps”

### Recommendations

- Ingest flows should:
  - Group related messages, logs, or code snippets into **coherent segments**.
  - Avoid creating segments that are just “partial line ranges” without meaning.
- Pruning, stashing, and compression should operate at the **segment** level, never at arbitrary token slices.

---

## 3. Pattern: Strict Working Set (Working Memory)

### Problem

Agents tend to accumulate context until they hit limits, treating the entire window as indiscriminate history.

### Human Analogy

- Working memory is **small and precious** (≈4 chunks).
- Humans:
  - Keep only what’s needed **right now** in focus.
  - Externalize other information to notes or long-term memory.

### Design Pattern

- Define an explicit **“working set”**:
  - Small set of segments that represent the **current task state**.
  - Includes:
    - Current task/goal description.
    - Active file + recent edited region.
    - Last N user/assistant messages (small, e.g., 5–10).
    - A few key decision/summary notes.

### Recommendations

- Implement a `working_set` abstraction in server state:
  - A view over `ContextSegment`s tagged as `in_working_set=True`.
- GC and pruning patterns should:
  - Aggressively keep the working set under a small target (e.g., 10–20 segments).
  - Treat non-working-set segments as candidates for stashing or pruning.
- Tools should expose **working-set metrics**:
  - Count of segments and approximate tokens.
  - Composition (decisions vs. logs vs. code).

---

## 4. Pattern: Gist Before Prune

### Problem

Naive pruning (or summarization) can remove critical state (what file, what line, what error), forcing the user to re-align the agent.

### Human Analogy

- Humans often remember the **gist** (what was decided, what changed, where work is) and forget step-by-step details.

### Design Pattern

- Before removing large or complex segments (long debug logs, extended discussions):
  - Encourage the agent to create a **compact “gist” segment**:
    - What problem was tackled.
    - What decisions were made.
    - Where work is currently focused (file + location).
    - Next steps.

### Recommendations

- Add or reuse an MCP tool (building on `llm_driven_context_compression.md`) such as:
  - `context_create_gist_note`:
    - Input: list of `segment_id`s to summarize.
    - Output: a new `ContextSegment` of type `note` or `decision`, plus suggested old segments to prune/stash.
- GC patterns can:
  - Prefer **pruning/stashing segments that have a corresponding gist note**.
- UX-wise:
  - Analysis tools should explicitly suggest: “Create a gist for these 3 large log segments, then prune them.”

---

## 5. Pattern: Task-Centric Bundles

### Problem

Mixed-context windows (multiple tasks, features, bugs) increase confusion and make pruning risky.

### Human Analogy

- Humans organize memories **by task/goal** and feel friction when contexts are mixed.
- Task switching is costly; people leave themselves notes/checklists when switching.

### Design Pattern

- Group segments into **task bundles**:
  - Each segment can have:
    - `task_id: str | None`
    - `task_label: str | None` (e.g., “Fix bug #123 in auth flow”).
- Active task:
  - A single `current_task_id` drives:
    - Working-set membership.
    - Pruning/stashing decisions.

### Recommendations

- Introduce light task metadata:
  - Agents can set or update current `task_id` via a tool (or it can be inferred from conversation tags/labels).
- GC and analysis tools:
  - Prefer to prune/stash **segments from inactive tasks** from the active window.
  - Offer “task-scope” pruning: “Clean up old context for task X while preserving Y.”
- Snapshots (next pattern) should be **task-scoped**.

---

## 6. Pattern: Task Snapshots (State Before Switch)

### Problem

When context is pruned or tasks are switched, the agent may lose track of what was last done, requiring re-alignment.

### Human Analogy

- Before switching tasks, humans often:
  - Write down what they were doing.
  - List remaining TODOs.
  - Mark where to resume.

### Design Pattern

- Provide a “snapshot” tool to capture:
  - Current file and location(s).
  - Current hypothesis and next steps.
  - Open questions or blockers.

### Recommendations

- MCP tool example:

  - `context_create_task_snapshot`:
    - Input:
      - `task_id` (optional; defaults to current).
      - Optional hint text from agent.
    - Behavior:
      - Aggregates:
        - Key working-set segments.
        - Active file metadata.
      - Produces a compact `ContextSegment` of type `note` or `summary`.
      - Tags it with `snapshot=True`, `task_id`, timestamp.

- GC and pruning:
  - When switching tasks or doing heavy cleanup, first call `context_create_task_snapshot`.
  - After that, it’s safer to prune more aggressively.

---

## 7. Pattern: Tiered Storage (Working → Recent Stash → Deep Archive)

### Problem

Treating all stashed context uniformly makes retrieval and pruning decisions harder, and can bloat even the stash layer over time.

### Human Analogy

- Human memory is hierarchical:
  - Recently used info is more available.
  - Older memories are still there, but need stronger cues and may be more gist-like.

### Design Pattern

- Introduce simple **tiers** in storage:
  - **Tier 0: Working Set** – segments actively used in the current window.
  - **Tier 1: Recent Stash** – recently stashed segments, easily retrievable.
  - **Tier 2: Deep Archive** – older, less frequently used segments, often compressed.

### Recommendations

- Implementation can be:
  - A single JSON store with a `tier` field per segment.
  - Tier migration based on age/refcount:
    - New stashes start in Tier 1.
    - After multiple GC cycles without use, migrate to Tier 2 (and possibly compress).
- Retrieval tools:
  - First search Tier 1; only search Tier 2 if necessary.
- RAG-style retrieval (if we ever use embeddings) can be focused on Tier 2.

---

## 8. Pattern: Cue-Based Retrieval (Filename/Tag/Task-First)

### Problem

Without embeddings, recall may seem limited; but adding heavy vector infra is against current constraints.

### Human Analogy

- Humans recall via **cues**:
  - “That bug in the auth module”, “the meeting about billing”, “the file we changed yesterday”.

### Design Pattern

- Provide retrieval tools that prioritize **human-like cues**:
  - By `task_id` / `task_label`.
  - By file path or function name.
  - By simple tags (bug ID, feature name).
  - By text search over summaries/notes.

### Recommendations

- MCP tools:
  - `context_search_stash`:
    - Inputs: optional `task_id`, `file_path`, `tags`, `keyword_query`.
    - Behavior: keyword/metadata search across Tier 1 and Tier 2, ranked by:
      - Task match.
      - Tag/file match.
      - Recency.
- UX/agent behavior:
  - Encourage the agent to:
    - Tag important segments with stable identifiers (bug IDs, feature names).
    - Use these cues when requesting retrieval.

---

## 9. Pattern: Cognitive-Load-Inspired Metrics

### Problem

Agents currently lack simple signals about “how overloaded” the context is or what is causing that load.

### Human Analogy

- Cognitive load theory distinguishes:
  - **Intrinsic load** (task complexity) vs. **extraneous load** (bad presentation, irrelevant info).

### Design Pattern

- Expose **simple, interpretable metrics** about context usage:
  - Total tokens vs. budget.
  - Working-set size (segments/tokens).
  - Ratio of logs vs. decision/summary segments.
  - Number of tasks represented in the working set.

### Recommendations

- Extend context analysis tools (or GC analysis tool) to return:
  - A small “context health” panel:
    - `working_set_tokens`, `total_tokens`, `num_tasks_in_working_set`, `log_to_decision_ratio`.
  - Simple recommendations:
    - “Working set includes 3 tasks; consider snapshotting and pruning inactive tasks.”
    - “Logs account for 70% of tokens; consider gist + prune.”

---

## 10. Dependencies & Compatibility

These patterns:

- Do **not** require new heavy dependencies.
- Build on:
  - `pydantic` models (`ContextSegment` extended with `task_id`, `tier`, `snapshot` flags).
  - Existing GC heuristics and storage abstractions.
  - Simple metadata and keyword search.

They should be considered **conceptual overlays** on top of the concrete algorithms in:

- `gc_heuristic_pruning_patterns.md`
- `llm_driven_context_compression.md`
- `rag_patterns_context_management.md` (for future deep archive/RAG tiers)

---

## 11. Summary

The human-memory-inspired patterns recommend that the MCP server:

- Treat the active context as **working memory** (small, chunked, task-centric).
- Use **gist-before-prune**, **task snapshots**, and **tiered storage** to preserve continuity while freeing tokens.
- Apply **cue-based retrieval** and **cognitive-load-like metrics** to make pruning and retrieval decisions more natural and interpretable.

These patterns are optional but strongly recommended lenses when refining the final design and deciding how GC, compression, and retrieval tools should behave in practice.


