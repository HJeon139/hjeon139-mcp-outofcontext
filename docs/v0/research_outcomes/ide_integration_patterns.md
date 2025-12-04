# Design: IDE & Platform Integration Patterns (Cursor, Claude Code, Kiro)

## 1. Scope & Goals

### What This Design Covers

This document describes **practical integration patterns** for using the Context Management MCP server with:

- **Cursor** (IDE with built-in MCP support),
- **Claude Code** (CLI / tooling around Claude),
- **Kiro** (structured, spec-driven dev environment).

The focus is how to:

- Influence or “override” the **effective context** sent to the LLM,
- While respecting the fact that **platforms own the context window**, and MCP is **tool‑centric**, not context‑centric.

### Non-Goals

- Not a full restatement of MCP basics (see `mcp_protocol_context_management.md`).
- Not a complete VS Code extension spec or CLI implementation.
- Not a guarantee about any specific platform’s current plugin APIs—this is pattern-level guidance.

---

## 2. Constraints Recap

From `mcp_protocol_context_management.md` and `architecture_platform_integration.md`:

- MCP servers:
  - Expose **tools/resources**.
  - Maintain their **own internal state** (segments, stashes, GC metadata).
  - Cannot see or edit the **actual LLM prompt** unless the client sends relevant slices.
- Platforms (Cursor / Claude Code / Kiro / etc.):
  - Build the **real prompt**.
  - Track **token usage** and **model limits**.
  - Decide which messages, files, and tool outputs to send each time.

**Consequence**:  
We **cannot directly stop** an IDE’s chat window from filling up.  
We **can**:

- Provide tools that:
  - Maintain a **parallel, better-managed memory**.
  - Analyze and suggest pruning/gist/snapshot actions.
- Integrate (via extensions/wrappers) into the platform’s **prompt-building pipeline**, so the platform uses our server’s decisions.

---

## 3. Integration Modes Overview

We use three main integration modes:

1. **Advisory Mode (No Platform Changes)**  
   - MCP server acts as a **smart memory advisor + store**.  
   - The user/agent calls tools manually from within the IDE chat.  
   - Platform context is unchanged; we provide **gists** and **snapshots** to make resets cheaper.

2. **Sidecar/Extension Mode (IDE/Client Cooperation)**  
   - A **sidecar process or extension** in the IDE cooperates with our MCP server:
     - Reads conversation/file state.
     - Asks our server what to keep/prune/stash.
     - Builds a modified LLM prompt accordingly.

3. **Wrapper Mode (CLI Tools like Claude Code)**  
   - A wrapper script/binary around the CLI:
     - Intercepts context before sending to the LLM.
     - Delegates context decisions to the MCP server.
     - Sends a slimmed/reshaped prompt to the underlying tool.

The rest of the document applies these patterns to Cursor, Claude Code, and Kiro.

---

## 4. Cursor Integration Patterns

### 4.1 Advisory Mode: “Second Brain” Inside Cursor Chat

**Context**: Use Cursor as-is, just registering our MCP server.

**What we can do**

- Tools inside Cursor:
  - `context_analyze_usage`:
    - Takes a short summary of what’s in the conversation + active file, and (optionally) client-provided token stats.
    - Returns:
      - “Context health” metrics.
      - Recommended segments/themes to prune or stash.
  - `context_create_gist_note`:
    - Given IDs or quoted text of long logs/discussions, creates a **gist note** stored in our MCP server, returning a short summary.
  - `context_create_task_snapshot`:
    - Captures a compact snapshot of the current task (active file/lines, decisions, next steps).
  - `context_recall_task` / `context_search_stash`:
    - Retrieves previously stashed notes/snapshots by task, file, tags, or keywords.

**How it helps**

- User/agent:
  - Uses our tools to offload **details** into the MCP server.
  - Keeps Cursor chat lighter by:
    - Referring back to MCP-stored notes instead of reloading entire histories.
  - When the Cursor context “fills up” and resets are needed:
    - The agent can quickly re-align using `context_recall_task` / `context_recall_snapshot` results.

**Limitations**

- Cursor still accumulates chat context.
- We **cannot** delete chat messages or change what Cursor sends to the LLM.

### 4.2 Sidecar/Extension Mode: Prompt Builder Cooperation

**Context**: Requires Cursor (or a Cursor extension/host) to cooperate.

**High-level flow**

1. Cursor collects:
   - Conversation history.
   - Active file(s) and selections.
   - Tool outputs.
2. Before building the final prompt, a **sidecar**:
   - Calls MCP tools (e.g. `context_gc_analyze`, `context_suggest_pruning`) with:
     - Recent messages (or a compressed representation).
     - Active file info.
     - Token stats.
   - Receives:
     - A list of **segments to exclude**, **segments to compress**, and **segments to keep**.
     - Optional **gist summaries** or **snapshots** to inject instead of raw history.
3. The sidecar builds an adjusted context:
   - Drops or shortens older segments according to our pruning plan.
   - Inserts gist notes / snapshots from the MCP server where appropriate.
4. Cursor sends this adjusted prompt to the LLM.

**Implementation sketch**

- The sidecar:
  - Could be:
    - A small local service that Cursor (or a VS Code extension) talks to.
    - A plugin if Cursor exposes plugin APIs.
  - Is responsible for:
    - Translating Cursor’s internal message/file model into our `ContextSegment`-like descriptors.
    - Handling token counting with the model’s real tokenizer.

**Benefits**

- Now our MCP server **effectively controls** the working set that goes into each LLM call.
- We achieve the goal of “stopping context from filling up” at the **prompt-building layer**, without MCP needing protocol-level context control.

---

## 5. Claude Code Integration (Wrapper Mode)

### 5.1 Environment

- Claude Code is typically:
  - A CLI that:
    - Reads code, user commands, config.
    - Builds a prompt for Claude.
    - Streams responses.

We may not be able to change the official binary, but we can **wrap** its behavior.

### 5.2 Wrapper Pattern

**Approach**

- Create a wrapper CLI, e.g. `cm-claude`:
  - Accepts the same inputs as Claude Code (command, context).
  - Before calling Claude:
    1. Builds a **candidate context** (files, previous interactions, logs).
    2. Calls our MCP server tools:
       - `context_gc_analyze` / `context_suggest_pruning`:
         - Input: description of messages/files and token estimates.
         - Output: a pruning/compression plan.
       - `context_recall_task`:
         - Optionally pull in relevant stashed context from prior runs.
    3. Applies the plan:
       - Drops or compresses some parts of the candidate context.
       - Injects gist/snapshot segments instead of raw prior runs.
    4. Calls Claude Code or the Claude API with the **trimmed prompt**.

**Benefits**

- We fully control the **effective context**:
  - No need for MCP protocol changes.
  - Works today as long as we own the wrapper.

**Limitations**

- Users must opt into the wrapper (use `cm-claude` instead of the vanilla `claude` CLI).
- Tight integration with official Claude Code features may require extra compatibility work as the tool evolves.

---

## 6. Kiro Integration Patterns

### 6.1 Background

- Kiro emphasizes:
  - Structured specs and workflows (Spec Mode).
  - Explicit context controls (`#File`, `#Folder` directives, etc.).
- This explicitness is actually **compatible** with our approach:
  - Kiro already treats context as something to be **declared**, not guessed.

### 6.2 Advisory Mode

- Use our MCP tools from within Kiro’s chat/command environment to:
  - Analyze current spec and files.
  - Suggest which parts of the spec/logs to compress or stash.
  - Maintain long-term stashed context for:
    - Past specs.
    - Design rationale.
    - Decisions.

### 6.3 Spec-Aware Integration

**Pattern**

- Integrate the MCP server as a **companion** that:
  - Reads:
    - The current Spec (as a document).
    - The set of `#File`/`#Folder` directives in use.
  - Returns:
    - A refined set of files/folders to include for the current step.
    - Suggestions to split the spec into **subtasks** with their own task IDs and snapshots.

**Concrete uses**

- “Context advisor” for Kiro’s Spec Mode:
  - On each phase (plan, implement, test), call:
    - `context_analyze_usage` / `context_gc_analyze`:
      - Input: spec text, file list, rough token counts.
      - Output: recommended subset of files/spec sections to emphasize.
  - Optionally, use:
    - `context_create_task_snapshot`:
      - Before moving from one phase to another.

**Benefits**

- Kiro’s already-explicit context boundaries make it easy to:
  - Let our MCP server **refine which parts** are in focus.
  - Implement a more human-like working-memory model for each Spec phase.

---

## 7. Cross-Platform “Minimum Integration” Pattern

Regardless of platform, a minimal but useful integration looks like:

1. **Expose tools with clear names and schemas**:
   - For analysis, pruning suggestions, stashing, recall, snapshots.
2. **Have the client send structured context descriptors**:
   - Recent messages (summaries), active files, tokens, task IDs.
3. **Apply recommendations in the client’s prompt builder**:
   - Drop or rewrite parts of history according to our GC/heuristic rules.
   - Inject gist notes/snapshots from the MCP server instead of entire histories.
4. **Use the MCP server as the durable context store**:
   - Past tasks, decisions, and compressed logs live on the server.
   - The platform treats it as a “second brain” that can be queried when needed.

This pattern is consistent across Cursor, Claude Code, and Kiro, differing mainly in **where** you hook into the prompt assembly process (IDE extension vs. CLI wrapper vs. spec engine).

---

## 8. Summary

- We cannot stop built-in UIs (like Cursor’s chat) from **accumulating raw messages** via MCP alone.  
- We **can**:
  - Provide a stateful MCP server that manages context segments, stashes, GC, and snapshots.
  - Integrate with platforms via:
    - Advisory tools (no platform changes).
    - Sidecar/extension pattern (IDE cooperates for prompt assembly).
    - Wrapper pattern (for CLIs like Claude Code).
- Implementations that adopt the sidecar/wrapper patterns can effectively let our server **control the working set** of context, achieving the goal of “never running out of useful context” while staying within current protocol constraints.


