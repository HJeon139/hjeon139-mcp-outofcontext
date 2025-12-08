## MCP Server Design Patterns

This document captures design patterns for building our context-management MCP server, drawing inspiration from:

- Claude Memory (project-scoped, user-controllable long-term memory) [`https://www.claude.com/blog/memory`](https://www.claude.com/blog/memory)
- `mcp-devtools` (modular, tool-centric MCP server architecture) [`https://github.com/sammcj/mcp-devtools`](https://github.com/sammcj/mcp-devtools)
- Our own research and design docs (GC heuristics, RAG, human-memory-inspired patterns, IDE integration).

The goal is to define *how* the server should be structured, not just *what* it does.

---

## 1. High-Level Goals

- **Goal 1 – Never hit context limits “by surprise”**  
  The host platform (Cursor, Claude Code, Kiro, wrappers) should be able to proactively manage the LLM context window for a task/project, guided by our server.

- **Goal 2 – Project/task-scoped memory**  
  Context state should be scoped to a project/task (similar to Claude’s project memory) instead of a global blob, aligning with how real work is organized.

- **Goal 3 – Lightweight, pluggable strategies**  
  GC-style pruning, summarization, RAG retrieval, and human-memory-inspired bundles should be implemented as *pluggable strategies*, with a minimal, heuristics-first MVP.

- **Goal 4 – Host integration as a first-class concern**  
  The MCP server does not directly build the final LLM prompt. It advises and serves context to the host, which ultimately decides what goes into the model input.

---

## 2. Core Architectural Patterns

### 2.1 Tool Registry + Modular Tools (inspired by `mcp-devtools`)

**Pattern:**  
Use a central **Tool Registry** that discovers and registers all context-related tools at startup, similar to `mcp-devtools`’ modular architecture.

- Each “capability” is a **tool module**:
  - `context_get_working_set`
  - `context_prune_gc`
  - `context_summarize_segment`
  - `context_stash` / `context_restore`
  - `context_inspect` / `context_edit`
  - (Optional) `context_rag_retrieve`
- Each module implements a **standard interface** (Pydantic models for inputs/outputs, clear error types).
- Tools are **self-contained** and do not depend on each other’s internal state except via shared context storage abstractions.

**Benefits:**

- Easy to add/remove capabilities without changing core server logic.
- Aligns with how clients already expect to interact with MCP servers (tool-first mental model).
- Enables “feature flags” for advanced tools.

---

### 2.2 Transport-Abstraction Layer

**Pattern:**  
Decouple transport (STDIO, HTTP, SSE) from tool logic, mirroring `mcp-devtools`’ `--transport` options.

- Core context logic lives in a **pure Python service layer**:
  - `ContextStore` interface
  - `GcEngine` interface
  - `SummarizationEngine` interface
  - `RagEngine` interface (optional)
- Transports:
  - **STDIO**: default for IDE integration and local agents.
  - **HTTP/SSE (later)**: for remote orchestration or multi-agent systems.

**Benefits:**

- We can start with the simplest transport (STDIO) and evolve without invasive refactors.
- Makes it easier to deploy the same server in multiple environments.

---

### 2.3 Configuration via Environment + Safe Defaults

**Pattern:**  
Use environment variables and simple config files to turn features on/off and choose backends, similar to `ENABLE_ADDITIONAL_TOOLS`, `DISABLED_TOOLS`, `MEMORY_FILE_PATH` in `mcp-devtools`.

Examples:

- **Feature toggles**
  - `CONTEXT_ENABLE_SUMMARIZATION=true|false`
  - `CONTEXT_ENABLE_RAG=true|false`
  - `CONTEXT_ENABLE_VECTOR_STORE=true|false` (off for MVP)
  - `CONTEXT_ENABLE_ADVANCED_GC=true|false`
- **Storage + limits**
  - `CONTEXT_STORAGE_DIR=~/.context-mcp/`
  - `CONTEXT_MAX_TOKENS_PER_PROJECT=1000000` (millions of tokens)
  - `CONTEXT_MAX_SEGMENT_TOKENS=512` (or similar)
- **Integrations (opt-in)**
  - `CONTEXT_EMBEDDING_MODEL=...`
  - `CONTEXT_DB_URL=...` (if/when we add SQLite/other backends)

**Design principle:**  
Defaults are **lightweight and safe**, matching the constraints in `docs/requirements.md`. Heavier features are opt-in.

---

### 2.4 Security + Data Governance as First-Class

**Pattern:**  
Take inspiration from `mcp-devtools`’ security framework (YAML rules, filesystem allowlists, HTTP/domain restrictions) and apply it to context storage.

Key ideas:

- **Filesystem access**:
  - Only allow context storage under **explicitly configured directories** (`CONTEXT_STORAGE_DIR`).
  - Never read arbitrary files unless through a dedicated, restricted file tool.
- **Data sensitivity**:
  - Treat persisted context as sensitive:
    - Support per-project encryption at rest (future).
    - Offer “ephemeral” vs. “persisted” context policies per project.
- **Tool-level access control**:
  - Optionally restrict tools like `context_export`, `context_snapshot` to trusted roles or configurations.

**Benefits:**

- Reduces risk when storing logs, code, and user content.
- Makes it easier to adopt this server in security-conscious environments.

---

### 2.5 Observability and Introspection

**Pattern:**  
Mirror `mcp-devtools`’ logging and OpenTelemetry-style observability, but focused on **context lifecycle**.

What to log/measure (with appropriate privacy controls):

- Per-project:
  - Total tokens stored vs. target capacity.
  - Number of GC cycles, number of segments pruned.
  - Number and size of summaries created.
  - Number of stashed vs. active segments.
- Per-session (per agent run or per request):
  - Tools invoked (`context_prune_gc`, `context_summarize_segment`, etc.).
  - Estimated token savings from GC/compression.
  - Reasons for prunes (heuristic scores, age, low reference count).

**Use cases:**

- Debugging “why did my context vanish?”.
- Tuning heuristics (e.g., raising/lowering recency weight).
- Demonstrating value (tokens saved, fewer resets).

---

## 3. Memory and Context Patterns (Claude Memory + Our Designs)

### 3.1 Project/Task-Scoped Memory

**Pattern (from Claude Memory):**  
Each project has a **separate memory**, with its own summary, editable by the user [`https://www.claude.com/blog/memory`](https://www.claude.com/blog/memory).

Our adaptation:

- Every context segment belongs to:
  - A **project_id** (IDE project, repo, or workspace).
  - Optionally a **task_id** (bug ID, feature ticket, “working on X”).
- We maintain:
  - **Working set**: active segments relevant to the current task.
  - **Stashed set**: archived but retrievable segments.
  - **Summaries**: higher-level descriptions of tasks/projects, updated over time.

Implications:

- Avoids cross-project contamination (no leaking context between clients/tasks).
- Matches human workflows and integrates cleanly with hosts (Cursor project, Claude project, Kiro workspace).

---

### 3.2 Memory Summaries as First-Class Objects

**Pattern (from Claude Memory):**  
Claude maintains a **memory summary** per project that users can view and edit.

Our adaptation:

- Define a `ContextSummary` segment type:
  - References underlying segments (or bundles).
  - Contains compressed “gist” text plus metadata (files, tasks, timestamps).
- Promote summaries to first-class citizens:
  - GC might **replace** many old fine-grained segments with one summary segment.
  - The host can fetch summaries as part of the prompt-building pipeline.

Benefits:

- Aligns with our **LLM-driven compression** design.
- Bridges between raw logs and high-level “what were we doing last week?” style queries.

---

### 3.3 Incognito / No-Persist Sessions

**Pattern (from Claude Memory):**  
Incognito chats do not add to memory or conversation history.

Our adaptation:

- Support a simple **no-persist / incognito flag** when calling tools:
  - Example: `persist=false` in tool params or in a session config.
  - These segments may participate in GC within the process, but are never written to disk.

Use cases:

- Sensitive debugging sessions.
- One-off explorations where long-term memory is not desired.

---

### 3.4 Human-Memory-Inspired Tiered Storage

**Pattern (from our research/design):**

- **Working memory** ↔ strict, small working set.
- **Short-term** ↔ recent task-local history, possibly compressed.
- **Long-term** ↔ summaries, key decisions, and stashed bundles.

Our MCP server maps this via:

- **Tier 0 (Working Set)**:
  - A small number of high-priority segments (e.g., active file, current diff, latest instructions).
  - Strict token budget enforced via GC heuristics.
- **Tier 1 (Recent History)**:
  - Recently-used segments with decaying priority.
  - Candidates for summarization or stashing.
- **Tier 2 (Long-Term)**:
  - Summaries and snapshots, possibly indexed for retrieval (lightweight at first; RAG later).

GC and summarization operate over these tiers to maintain a healthy working set.

---

## 4. GC, Compression, and Retrieval as Pluggable Strategies

### 4.1 GC Heuristic Pruning (Default Strategy)

**Pattern:**  
Use a **heuristics-only GC engine** as the default pruning strategy (no embeddings or heavy ML).

Key ideas (from `gc_heuristic_pruning_patterns.md` and `garbage_collection_patterns.md`):

- Score segments by:
  - **Recency** (timestamps, last-access).
  - **Type** (instructions, code, logs, summaries, user intent).
  - **Reference count** (how many other segments/summaries refer to them).
  - **Generation** (how many GC cycles survived).
  - **Pinned flag** (never prune unless forced).
- Run incremental GC when:
  - Working-set token estimate exceeds thresholds.
  - Host explicitly calls `context_prune_gc`.

This is the MVP strategy and should work well for millions of token ranges.

---

### 4.2 LLM-Driven Compression (Optional Strategy)

**Pattern:**  
Use the LLM to paraphrase segments while preserving key metadata, as described in `llm_driven_context_compression.md`.

Design:

- Tool: `context_compress_segment` (or `context_compress_bundle`).
- Annotated input:
  - “Keep these facts *exactly* (file path, line range, active cursor state).”
  - “Aggressively compress these parts (verbatim logs, repetitive traces).”
- Output:
  - A shorter segment with attached metadata.
  - Optionally a link to the original segment (for reversible expansion).

Use cases:

- When we want to preserve **recency and structure** but must reduce token size.
- When a host wants “gist plus pointers” instead of raw logs.

---

### 4.3 RAG for Stashed Context (Future/Optional Strategy)

**Pattern:**  
Treat stashed segments like a tiny, per-project knowledge base, retrievable by semantic or keyword search (aligned with `rag_patterns_context_management.md`).

MVP approach:

- Start with **simple keyword/metadata search** over stashed segments (no vector DB).
- Later:
  - Enable embeddings and a vector index behind a feature flag (e.g., `CONTEXT_ENABLE_VECTOR_STORE`).

Tools:

- `context_search_stash` – returns ranked segments based on query + metadata filters.
- `context_retrieve_for_task` – returns a curated bundle for a given task ID or query.

---

## 5. Host Integration Patterns (How Platforms Use These Tools)

We align with the integration modes described in `ide_integration_patterns.md`:

- **Advisory mode**:
  - Host periodically calls:
    - `context_get_working_set`
    - `context_prune_gc` (optionally with a target token budget)
  - Host still directly manages the final prompt.

- **Sidecar/Extension mode**:
  - IDE/plugin cooperates more tightly:
    - Sends file/edit state and cursor position.
    - Lets the MCP server propose an ordered list of segments to include, plus suggested prunes.

- **Wrapper mode**:
  - CLI or agent runtime calls the LLM API and can **fully control** the composed context.
  - This mode can use our server as the single source of truth for working set, stashes, and summaries.

**Key pattern:**  
In all modes, the MCP server **does not override** context by itself. It advises, stores, and returns curated context; the host decides what to send to the LLM.

---

## 6. Deployment Patterns

Following the spirit of `mcp-devtools`:

- **Local developer mode (default)**:
  - Transport: STDIO.
  - Storage: JSON files under `~/.context-mcp/`.
  - Feature flags: GC + heuristics enabled, RAG/summarization optional.

- **Team/shared mode (later)**:
  - Transport: HTTP/SSE.
  - Storage: shared directory or DB.
  - Optional OAuth-style auth (if needed).

- **Containerized mode (later)**:
  - Container image bundling our MCP server.
  - Config-driven deployment in CI, remote dev environments, or as a shared org service.

---

## 7. Open Questions and Next Steps

Open questions:

- How much of the GC/summarization logic should be *automatic* vs. **explicitly requested** by tools from the host?
- What is the minimal introspection API the host needs to debug context decisions (“why did this get pruned?”)?
- How should we version context schemas to allow safe upgrades over time?

Proposed next steps:

- Define concrete Pydantic models for:
  - `ContextSegment`, `ContextSummary`, `ContextBundle`, `GcPlan`, `GcResult`.
- Draft the initial tool specs and signatures:
  - `context_get_working_set`
  - `context_prune_gc`
  - `context_summarize_segment`
  - `context_stash` / `context_restore`
  - `context_inspect`
- Wire these into a **minimal MCP server skeleton** with:
  - STDIO transport.
  - JSON-file-backed `ContextStore`.
  - Basic heuristic GC implementation.

This will give us a coherent, extensible base that mirrors successful patterns from Claude Memory and `mcp-devtools`, while remaining tailored to our context-management problem and lightweight constraints.


