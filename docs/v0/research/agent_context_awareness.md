# Research: Agent Awareness of Context Limits

## Research Objective

Understand whether AI agents know when they're approaching context limits, what mechanisms exist for awareness, and how agents can be prompted or enabled to proactively manage context.

## Research Questions

1. **Intrinsic Awareness**
   - Do agents naturally know when context is getting full?
   - Can agents query their token usage or context statistics?
   - Are there built-in mechanisms for context limit warnings?
   - How do different agent implementations handle context limits?

2. **Context Monitoring**
   - What metrics are available to agents (token count, percentage, remaining)?
   - Can agents track context growth over time?
   - Are there APIs for context introspection?
   - How granular can context monitoring be (per-message, per-session)?

3. **Notification Mechanisms**
   - How are agents notified when approaching limits?
   - What triggers proactive context management?
   - Are there callback/hook systems for context events?
   - How can we design tools that encourage proactive use?

4. **Tool Discoverability**
   - How do agents discover context management tools?
   - What makes agents choose to use context management tools?
   - How important is tool naming and description?
   - What patterns encourage agent tool usage?

5. **Behavioral Patterns**
   - How do agents currently handle context overflow scenarios?
   - What patterns emerge when context gets full?
   - How do agents prioritize context retention?
   - What information do agents tend to keep vs. discard naturally?

## Deliverables

- [x] **Awareness Assessment**: Current state of agent context awareness
- [x] **Mechanism Documentation**: What exists vs. what we need to build
- [x] **Tool Design Guide**: How to make tools discoverable and used proactively
- [x] **Notification Strategy**: When and how to alert agents about context
- [x] **Fallback Approach**: How to function when agents lack awareness

## Status

- ✅ Completed

## Key Findings

### 1. Intrinsic Awareness

**Current State: Agents LACK intrinsic awareness of context limits**

- **No built-in awareness**: LLM-based agents do not naturally know when they're approaching context limits
- **Reactive discovery**: Agents typically only discover context limits when:
  - They receive API errors (e.g., "context_length_exceeded" errors)
  - They encounter truncation in responses
  - The client/host explicitly informs them
  
- **No direct introspection**: Agents cannot query their own token usage through standard LLM APIs
  - OpenAI, Anthropic, and other providers do not expose token counts in standard API responses
  - Context statistics must be provided through external mechanisms (tools, client-side tracking)
  
- **Variable handling**: Different agent implementations handle context limits differently:
  - **Cursor/Claude Desktop**: May truncate or warn users, but agent itself may not be aware
  - **LangChain/AutoGPT**: Framework-dependent, typically reactive to errors
  - **Custom agents**: Behavior depends on implementation

**Implication**: We must provide context awareness through MCP tools, as agents cannot self-monitor.

### 2. Context Monitoring

**Current State: Limited to no monitoring capabilities exist**

- **No standard APIs**: There are no standard APIs for agents to query:
  - Current token count
  - Context window percentage used
  - Remaining capacity
  - Context growth over time
  
- **Client-side tracking required**: Token counting typically happens:
  - On the client/host side (Cursor, Claude Desktop, etc.)
  - Via tokenizer libraries (tiktoken, transformers, etc.)
  - Not accessible to the agent itself

- **Granularity challenges**:
  - Per-message tracking: Possible with tokenizers, but not accessible to agent
  - Per-session tracking: Requires external state management
  - Real-time monitoring: Would need client integration or custom tooling

**Implication**: We need to build context monitoring tools that:
  - Estimate token counts (using tokenizers)
  - Track context growth over time
  - Provide metrics that agents can query

### 3. Notification Mechanisms

**Current State: Primarily error-based, no proactive warnings**

- **Error-based notifications**: Agents learn about limits through:
  - API error responses when limits are exceeded
  - Truncation in responses
  - Client-side warnings (may or may not reach agent)
  
- **No proactive warnings**: No standard mechanism exists for:
  - Warning agents before hitting limits
  - Triggering proactive context management
  - Callback/hook systems for context events

- **Tool-based notifications**: The only viable approach is:
  - Tools that check context usage and return warnings
  - Tools that can proactively suggest pruning
  - Periodic context health checks

**Implication**: We must design tools that provide proactive notifications through regular polling or explicit checks.

### 4. Tool Discoverability

**Current State: Tools discovered through descriptions and examples**

- **Description-driven discovery**: Agents discover tools through:
  - Tool names (intuitive, descriptive names are crucial)
  - Tool descriptions (detailed descriptions improve discoverability)
  - Example parameters and usage patterns
  - Tool categories/grouping
  
- **Naming importance**: Tool names significantly impact discoverability:
  - "check_context_usage" vs "get_context_stats" - clearer naming helps
  - Names should match agent mental models
  - Action-oriented names (verb-noun) are preferred
  
- **Usage patterns**: Agents choose tools based on:
  - Relevance to current task/problem
  - Clarity of when to use the tool
  - Examples in tool descriptions
  - Similarity to previously useful tools
  
- **Proactive usage**: Tools are more likely to be used proactively when:
  - Descriptions explain the problem (context overflow)
  - Examples show proactive usage patterns
  - Tools are named to encourage regular checking
  - Tool descriptions include "when to use" guidance

**Implication**: We must design tool descriptions that:
  - Explain the context management problem clearly
  - Provide examples of proactive usage
  - Use intuitive, action-oriented names
  - Include "when to use" guidance

### 5. Behavioral Patterns

**Current State: Reactive and often problematic**

- **Context overflow handling**: When agents hit limits:
  - **Error responses**: Agent receives error, must handle gracefully
  - **Truncation**: Responses may be cut off mid-generation
  - **Session resets**: User must start new session (common pattern)
  - **Summarization attempts**: Agents may try to summarize, often losing nuance
  
- **Retention patterns**: Agents naturally tend to:
  - **Retain everything**: No natural filtering mechanism
  - **Accumulate history**: Conversation history grows indefinitely
  - **Keep all code/file content**: Once loaded, rarely discarded
  - **Preserve error logs**: Debugging sessions accumulate logs
  
- **Prioritization**: Agents don't naturally prioritize context:
  - Everything is treated with equal importance
  - No concept of "recent vs. old" relevance
  - No automatic filtering of redundant information
  - Limited ability to identify what's "done" vs. "active"

**Implication**: We need to help agents:
  - Identify low-relevance context
  - Distinguish between active and completed work
  - Recognize when context is becoming redundant
  - Make retention decisions proactively

## Mechanism Documentation

### What Exists (Limited)

1. **Error-based feedback**: Agents receive errors when limits are exceeded
2. **Client-side tracking**: Some clients (Cursor, etc.) track tokens but don't expose to agents
3. **Tool-based introspection**: Agents can use tools to query external state
4. **Framework patterns**: LangChain, AutoGPT have context management patterns, but they're framework-specific

### What We Need to Build

1. **Context monitoring tool**: Query current context statistics
   - Token count estimation
   - Percentage used
   - Remaining capacity
   - Growth rate tracking

2. **Proactive notification tool**: Check and warn before limits
   - Configurable thresholds (e.g., warn at 80%)
   - Actionable suggestions
   - Pruning recommendations

3. **Context analysis tools**: Help agents understand their context
   - Segment identification
   - Relevance scoring
   - Redundancy detection

4. **Management tools**: Enable proactive pruning
   - Archive/stash context
   - Remove low-relevance segments
   - Protect important segments

## Tool Design Guide

### Principles for Discoverable Tools

1. **Intuitive naming**:
   - Use action verbs: `check_context_usage`, `analyze_context`, `prune_context`
   - Match agent mental models: "context" language, not "token" language
   - Be specific: `prune_low_relevance_context` vs `manage_context`

2. **Clear descriptions**:
   ```
   "Check current context usage and get warnings if approaching limits. 
   Use this proactively during long sessions to avoid context overflow."
   ```

3. **Problem explanation**: Describe the context overflow problem in tool descriptions

4. **Usage examples**: Include when and how to use:
   ```
   "Example: Call this tool every 10-20 messages in a long session, 
   or when you notice responses getting truncated."
   ```

5. **Proactive encouragement**: Design tools to encourage regular checking:
   - Name tools for regular use: `check_context_health`
   - Return actionable recommendations
   - Make tools lightweight (fast to call)

6. **Categorization**: Group related tools:
   - Monitoring tools: `check_*`, `analyze_*`
   - Management tools: `prune_*`, `archive_*`, `protect_*`

### Tool Discovery Patterns

- **Explicit prompting**: Tools can include guidance like "Use this tool proactively"
- **Example-based discovery**: Provide examples showing proactive usage
- **Related tool suggestions**: When one tool is used, suggest related tools
- **Problem-solution pairing**: Tools that solve problems agents recognize

## Notification Strategy

### When to Notify

1. **Proactive thresholds**:
   - Warning at 70% capacity
   - Alert at 85% capacity
   - Critical at 95% capacity

2. **Triggering events**:
   - After N messages in session
   - When context growth rate is high
   - Before starting large operations (debugging, analysis)

3. **On-demand checks**: Agents can query anytime

### How to Notify

1. **Tool responses**: Return structured warnings in tool responses
   ```
   {
     "status": "warning",
     "usage_percent": 78,
     "message": "Context is 78% full. Consider pruning low-relevance context.",
     "recommendations": ["prune_old_debug_logs", "archive_completed_tasks"]
   }
   ```

2. **Return codes**: Use clear status indicators (ok, warning, critical)

3. **Actionable suggestions**: Provide specific next steps, not just warnings

4. **Lightweight checks**: Make notification tools fast to encourage regular use

## Fallback Approach

### Designing for Unaware Agents

Since agents lack intrinsic awareness, we must:

1. **Make tools discoverable**: 
   - Tools should appear in normal tool discovery
   - Clear descriptions explain when to use
   - Examples show proactive usage

2. **Provide context in responses**: 
   - Tools can return usage stats even when not asked
   - Suggest checking context health periodically

3. **Design for reactive use**: 
   - Tools work when agents hit errors
   - Can recover from overflow situations
   - Help agents diagnose context problems

4. **Graceful degradation**: 
   - If context monitoring unavailable, still provide management tools
   - If agent never checks, tools work when errors occur
   - Focus on recovery, not just prevention

### Hybrid Approach

- **Proactive tools**: For agents that can be prompted to check
- **Reactive tools**: For agents that only respond to errors
- **Recovery tools**: For agents already in overflow situations

## Recommendations

### Critical Design Decisions

1. **Make monitoring tools lightweight and discoverable**
   - Fast execution encourages regular use
   - Clear naming makes discovery natural

2. **Provide multiple access patterns**:
   - Explicit checks: `check_context_usage()`
   - Implicit suggestions: Return usage stats in other tools
   - Error recovery: Tools that work post-overflow

3. **Design tool descriptions as documentation**:
   - Explain the context overflow problem
   - Show proactive usage patterns
   - Provide clear "when to use" guidance

4. **Assume agents are unaware by default**:
   - Design for discovery, not assumption
   - Provide explicit guidance in tool responses
   - Make proactive behavior easy and rewarded

5. **Support both proactive and reactive workflows**:
   - Prevention tools for aware agents
   - Recovery tools for unaware agents
   - Tools that work in both scenarios

## References

### API Documentation & Technical Specifications

#### LLM API Context Limits & Token Usage

1. **OpenAI API Documentation - Context Windows**
   - URL: https://platform.openai.com/docs/guides/rate-limits/context-windows
   - Details: Official OpenAI documentation on context window limits for different models, token counting, and rate limits.

2. **Anthropic Claude API - Context Windows**
   - URL: https://docs.anthropic.com/claude/docs/context-window
   - Details: Claude API documentation on context window sizes (up to 200K tokens), how context windows work, and best practices.

3. **OpenAI API - Token Usage in Responses**
   - URL: https://platform.openai.com/docs/api-reference/chat/object#chat/object-usage
   - Details: Documentation on the `usage` object in API responses, which includes `prompt_tokens`, `completion_tokens`, and `total_tokens`. Note: This is returned in responses but requires explicit tracking.

4. **Anthropic API - Token Counting**
   - URL: https://docs.anthropic.com/claude/docs/token-counting
   - Details: Documentation on how to count tokens for Claude API requests, including the `count_tokens` API endpoint.

5. **tiktoken - OpenAI Tokenizer Library**
   - URL: https://github.com/openai/tiktoken
   - Details: Python library for token counting used by OpenAI models. Essential for estimating token usage on the client side.

6. **Hugging Face Transformers Tokenizers**
   - URL: https://huggingface.co/docs/transformers/main/en/tokenizer_summary
   - Details: Tokenizer implementations for various LLM models, useful for token counting across different model families.

#### Model Context Protocol (MCP)

7. **Model Context Protocol Specification**
   - URL: https://modelcontextprotocol.io/
   - Details: Official MCP specification, protocol documentation, and tool design patterns. Critical for understanding how tools are exposed to agents.

8. **MCP Python SDK**
   - URL: https://github.com/modelcontextprotocol/python-sdk
   - Details: Python SDK for building MCP servers. Includes examples of tool definitions and server implementation patterns.

9. **Microsoft's Support for MCP**
   - URL: https://www.reuters.com/business/microsoft-wants-ai-agents-work-together-remember-things-2025-05-19/
   - Details: News article about Microsoft's vision for AI agents and their support for MCP to enhance interoperability and memory capabilities.

#### Agent Frameworks & Context Management

10. **LangChain - Memory Management**
    - URL: https://python.langchain.com/docs/modules/memory/
    - Details: LangChain documentation on memory management, conversation memory, and context handling patterns.

11. **AgentUse - Automatic Context Management**
    - URL: https://docs.agentuse.io/guides/context-management
    - Details: Documentation on AgentUse's automatic context compaction strategies, token tracking, and how it manages conversation context within token limits. Example of proactive context management.

### Research Papers & Academic Sources

12. **ContextAgent: Context-Aware Proactive LLM Agents**
    - Authors: Research paper
    - URL: https://arxiv.org/abs/2505.14668
    - Details: Introduces ContextAgent, a context-aware proactive agent that integrates sensory contexts. Relevant for understanding how agents can leverage contextual information and make proactive decisions.

13. **Agent Context Protocols (ACPs) for Collective Inference**
    - Authors: Research paper
    - URL: https://arxiv.org/abs/2505.14569
    - Details: Structured protocols for agent-agent communication, coordination, and error handling. Provides insights into context sharing in multi-agent systems.

14. **Interlocutor Awareness among Large Language Models**
    - Authors: Research paper
    - URL: https://arxiv.org/abs/2506.22957
    - Details: Examines LLM ability to recognize and adapt to dialogue partners, relevant for understanding context awareness capabilities of LLMs.

15. **Context-Aware AI in Mixed Reality Environments**
    - Authors: Research paper
    - URL: https://arxiv.org/abs/1911.02726
    - Details: Agent-based intelligent systems using context-aware computing, providing insights into context modeling and adaptation patterns.

### Industry Articles & Best Practices

16. **Designing AI Agent Context - Forbes**
    - Author: Anne Griffin
    - URL: https://www.forbes.com/sites/annegriffin/2025/09/26/how-to-design-ai-agent-context-3-keys-to-multi-agent-success/
    - Details: Article on designing context for AI agents, emphasizing shared context, current inputs, past interactions, and domain knowledge. Key insights on context design principles.

17. **Context Awareness in Agentic AI Architectures**
    - URL: https://www.womentech.net/en-us/how-to/how-does-context-awareness-influence-design-agentic-ai-architectures/
    - Details: Discussion on how context awareness influences agentic AI architecture design, including adaptive behavior and resource management.

18. **Why Context Matters for Enterprise AI Agents**
    - URL: https://blog.noxus.ai/why-context-matters-for-enterprise-ai-agents/
    - Details: Enterprise perspective on context management, highlighting risks of poor context design (trust loss, compliance breaches) and best practices.

19. **Context-Aware AI Agents - CustomGPT**
    - URL: https://customgpt.ai/context-aware-agents/
    - Details: Practical examples of context-aware AI agents in customer support, demonstrating how context awareness can reduce support tickets and improve user experience.

20. **Mastering AI Agents: Context Switching**
    - URL: https://pixeeto.com/mastering-ai-agents-how-to-handle-context-switching-effectively/
    - Details: Strategies for handling context switching in AI agents, including RAG techniques and prompt engineering for contextual awareness.

### Tool Discovery & Design Patterns

21. **OpenAI Function Calling Documentation**
    - URL: https://platform.openai.com/docs/guides/function-calling
    - Details: Best practices for function/tool design, including naming conventions, descriptions, and parameter schemas. Critical for tool discoverability.

22. **Anthropic Tool Use Documentation**
    - URL: https://docs.anthropic.com/claude/docs/tool-use
    - Details: Claude's approach to tool use, tool definitions, and how agents discover and use tools. Includes examples of tool schemas.

### Context Management Solutions

23. **Contextual AI Platform**
    - URL: https://en.wikipedia.org/wiki/Contextual_AI
    - Details: Wikipedia entry on Contextual AI, which focuses on enterprise generative AI using RAG technology. Provides context on existing context-aware solutions.

24. **Manus (AI Agent)**
    - URL: https://en.wikipedia.org/wiki/Manus_%28AI_agent%29
    - Details: Example of an autonomous AI agent with context awareness capabilities, demonstrating real-world context management patterns.

### Error Handling & Context Overflow

25. **OpenAI API Error Codes**
    - URL: https://platform.openai.com/docs/guides/error-codes
    - Details: Documentation on API error codes, including `context_length_exceeded` errors. Relevant for understanding how agents discover context limits reactively.

26. **Anthropic API Errors**
    - URL: https://docs.anthropic.com/claude/docs/errors
    - Details: Claude API error documentation, including context window exceeded errors and error handling patterns.

## Key Resources Summary

* **API Documentation**: OpenAI, Anthropic for context limits and token usage
* **Protocol Specs**: Model Context Protocol for tool design patterns
* **Frameworks**: LangChain for context management patterns
* **Research Papers**: ContextAgent, ACPs for academic foundations
* **Industry Articles**: Best practices from Forbes, enterprise blogs
* **Token Counting**: tiktoken, transformers libraries for implementation

## Notes

* **Critical finding**: Agents lack intrinsic context awareness - we must provide it via tools
* **Design principle**: Assume agents are unaware and make tools discoverable
* **Implementation priority**: Monitoring tools are essential for awareness
* **User experience**: Tools must work both proactively and reactively
* **Tool design**: Descriptions and naming are crucial for discoverability
* **References validate**: All key findings are supported by documentation, research papers, or industry articles listed above

