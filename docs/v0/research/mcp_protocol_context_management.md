# Research: MCP Protocol Capabilities for Context Management

## Research Objective

Understand how the Model Context Protocol (MCP) supports context management, what interfaces are available, and what mechanisms exist for agents to interact with their session context.

## Research Questions

1. **Protocol Capabilities**
   - What MCP primitives support context introspection?
   - Can MCP tools query or inspect the agent's current context?
   - Are there hooks/events for context lifecycle management?
   - What context metadata is accessible through MCP?

2. **Tool Integration**
   - How do MCP tools interact with agent context?
   - Can tools modify or influence context directly?
   - What's the relationship between tool calls and context consumption?
   - How are tool descriptions/examples included in context?

3. **Agent Awareness**
   - Can agents query their own context usage through MCP?
   - Are there MCP mechanisms for context limit notifications?
   - How do agents discover available context management tools?
   - What signals do agents receive about context state?

4. **Context Representation**
   - How is context represented in MCP (messages, resources, tools)?
   - Can we segment context for analysis?
   - What context types exist (conversation, code, file contents)?
   - How is context structured/hierarchical?

5. **Limitations & Constraints**
   - What context management operations are NOT supported by MCP?
   - Are there protocol-level constraints on context manipulation?
   - What's out of scope for MCP tools?
   - What requires coordination with the client/agent host?

## Deliverables

- [x] **Protocol Analysis**: Document available MCP interfaces for context management
- [x] **Capability Matrix**: What can be done via MCP vs. requires client cooperation
- [x] **Tool Design Recommendations**: How to structure MCP tools for context management
- [x] **Gap Analysis**: What's missing from MCP for our use case
- [x] **Implementation Approach**: Technical approach for MCP server design

## Status

- ✅ Completed

## Key Findings

### 1. MCP is Tool-Centric, Not Context-Centric

- The **Model Context Protocol (MCP)** defines how:
  - Clients (agent hosts like Cursor, Claude Desktop, etc.) and servers exchange:
    - **Tools** (callable functions with schemas).
    - **Resources** (readable data).
    - **Prompts** (templated prompt snippets).
    - **Events** (in some implementations).
- MCP itself **does not define**:
  - How the client builds the LLM context window.
  - How much of the tool/resource metadata is included in each LLM call.
  - Any protocol-level API for “get my current tokens” or “prune my conversation”.

**Implication**: Context management is a **client/platform concern**. MCP servers can influence context **indirectly** via tools and resources, but cannot see or edit the actual LLM prompt directly.

### 2. No Native Context Introspection or Token APIs

- The MCP spec and reference SDKs:
  - Do not expose a standard “get current context” or “get token usage” API to servers.
  - Assume that the **client**:
    - Builds the prompt.
    - Tracks token usage (using tokenizer libraries).
    - Decides what to send to the LLM.
- MCP servers:
  - Receive **tool calls** with arguments and some metadata.
  - May maintain their own internal state, but **cannot inspect the full conversation context** unless the client sends it as arguments.

**Implication**: Our MCP server must:

- Treat context introspection as **data the client provides** via tool inputs.
- Offer tools that clients can call with:
  - Summaries or slices of current context.
  - Token usage metrics computed on the client.

### 3. Tools and Resources as the Main Integration Surface

**Tools**

- Servers define **tools** with:
  - Name, description, JSON schema input/output.
- Clients:
  - Expose these as callable actions to the agent.
  - Optionally show descriptions to users.
- For context management, this means:
  - All operations (analyze, prune, stash, retrieve) are expressed as **MCP tools**.

**Resources**

- Servers can expose **resources**:
  - Named read-only data (e.g., docs, configs, context snapshots).
  - Indexed, browsable, fetchable by ID/URI.
- Context management can use resources to:
  - Expose stashed context segments, task snapshots, or historical notes as **resources**.
  - Allow agents to browse or fetch them via MCP, which the client can then inject into the LLM context.

**Implication**: Our design should:

- Use tools for **actions** (analyze, prune, stash, compress).
- Optionally use resources for **read-only views** (stashed segments, task snapshots).

### 4. Capability Matrix: MCP vs. Client Responsibilities

**What MCP Server Can Do (via Tools/Resources)**

- Maintain its **own state**:
  - Context segments, stashed context, task metadata, GC metadata.
- Analyze context **descriptions** passed in:
  - E.g., list of recent messages, current file, token counts.
- Suggest:
  - Segments to prune/stash.
  - Gist summaries to create.
  - Task snapshots and working-set adjustments.
- Store:
  - Stashed segments, notes, snapshots.
  - Tiered context (working set vs. stash vs. archive).

**What Requires Client/Platform Cooperation**

- Actual **LLM context window building**:
  - Which messages, files, and segments are included.
  - In what order and with what formatting.
- **Token counting and limits**:
  - Using the real tokenizer for the chosen model.
  - Knowing the model’s max context length.
- **Applying pruning decisions**:
  - Removing or reordering prior messages from the conversation history.
  - Deciding what to send in the next LLM call.

**Implication**: Our MCP server must be designed as:

- A **context advisor and stateful memory service**, not a direct context editor.
- Effective only when integrated into a client that:
  - Calls MCP tools.
  - Applies the server’s recommendations to its own context management logic.

### 5. Tool Design Recommendations for MCP

Given the constraints above, effective context management tools should:

- **Accept explicit context descriptors**:
  - Recent messages (or summaries).
  - Current file and cursor location.
  - Token usage estimates (if available).
  - Task identifiers or labels.
- **Return structured recommendations**:
  - Segments/IDs to prune, stash, or compress.
  - Gist/snapshot suggestions with suggested titles/tags.
  - Simple “context health” metrics (working set size, log-to-decision ratio, tasks in window).
- **Be idempotent and stateless where possible**:
  - Re-running analysis should be safe and deterministic given the same input.
- **Use clear naming and descriptions**:
  - Make it obvious to the agent that these tools are about **context management**.

Examples (conceptual):

- `context_analyze_usage`
- `context_suggest_pruning`
- `context_stash_segments`
- `context_recall_task`
- `context_create_snapshot`

These align with the patterns described in the design documents.

### 6. Gaps and Limitations in MCP for Our Use Case

- **No built-in token awareness**:
  - Servers cannot directly know model token limits or exact usage.
  - We must rely on:
    - Client-side token counting.
    - Approximate counting using local tokenizers (if clients pass in text).
- **No direct conversation editing**:
  - Servers cannot edit the client’s chat history.
  - All pruning decisions must be carried out by the client.
- **No guaranteed tool exposure semantics**:
  - While MCP defines how tools are advertised, different clients may:
    - Present tools differently.
    - Limit which tools are visible/used by agents.

**Implication**: To be effective, our server:

- Must be paired with **platform-integration work** (as captured in `architecture_platform_integration.md` and `leveraging_existing_tooling.md`).
- Should be robust to partial adoption:
  - Work even if only some tools are called.
  - Provide value from a single `context_analyze` call, not require a complex protocol.

### 7. Implementation Approach for Our MCP Server

Based on the above:

- The MCP server will:
  - Be implemented as a **stateful Python MCP server** (Python SDK).
  - Expose:
    - **Tools** for analysis, pruning, stashing, recall, snapshots.
    - Optionally, **resources** for browsing stashed context.
  - Maintain:
    - Its own internal **context store** (segments, tasks, tiers).
    - GC and heuristic metadata (as per `gc_heuristic_pruning_patterns.md`).
- The client/platform will:
  - Provide contextual inputs to these tools (recent messages, file info, token stats).
  - Apply the server’s recommendations to its own context window.

This architecture matches the **three-layer pattern** already captured in `architecture_platform_integration.md`:

- Platform builds and owns the context.
- MCP server advises, stores, and manages context-related state via tools/resources.
- LLM agent uses tools to reason about and manage context, but never manipulates it directly.

## Key Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP GitHub](https://github.com/modelcontextprotocol)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Client implementations and docs (Cursor, Claude Desktop, and others using MCP).


