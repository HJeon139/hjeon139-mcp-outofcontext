# Design: Platform Integration Architecture

## 1. Scope & Goals

### What This Design Covers

This design document outlines the architecture for integrating the Context Management MCP Server with various agent platforms (Cursor, Kiro, Claude Code, etc.). It addresses how the MCP server must interact with platform-level context management systems to read and modify context.

### Non-Goals

- Not designing the internal MCP server logic (pruning algorithms, storage, etc.)
- Not designing the LLM interaction patterns
- Not designing platform-specific UI/UX (that's the platform's responsibility)

## 2. Core Architectural Insight

### The Context Management Pattern

**Universal Pattern**: Regardless of the underlying LLM model, all agent platforms follow the same pattern:

1. **Platform builds context** - The client/platform (Cursor, Kiro, etc.) assembles context from:
   - Conversation history
   - Selected files
   - Code snippets
   - User prompts
   - Tool responses

2. **Platform sends to LLM** - The assembled context is sent as a single payload to the LLM API

3. **LLM responds** - The model processes the context and returns a response

4. **Platform accumulates** - The response is added to context, which continues to grow

**Key Insight**: Context management happens at the **platform level**, not at the LLM level. The LLM only sees what the platform sends it.

### Implications for MCP Server Design

Our MCP server cannot operate independently. It must:

1. **Read context from the platform** - Need platform integration to access current context
2. **Modify context at the platform level** - Need platform integration to prune/modify context before it's sent to LLM
3. **Work across multiple platforms** - Need plug-and-play architecture supporting different platforms

## 3. Architecture Overview

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Platform Layer                     │
│  (Cursor / Kiro / Claude Code / VS Code / etc.)             │
│  - Builds context from conversation, files, code            │
│  - Manages token counting                                   │
│  - Sends context to LLM                                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Platform Integration API
                        │ (read context, modify context)
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              Context Management MCP Server                   │
│  - Context monitoring tools                                 │
│  - Context analysis (relevance, pruning)                    │
│  - Context modification commands                            │
│  - Storage for stashed context                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ MCP Protocol
                        │ (tool calls from agent)
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                        LLM Agent                             │
│  (Claude, GPT-4, etc. via platform)                         │
│  - Calls MCP tools to manage context                        │
│  - Receives modified context from platform                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Platform Integration Layer**
   - Platform-specific adapters (Cursor adapter, Kiro adapter, etc.)
   - Context reader interface (read current context, token counts)
   - Context modifier interface (prune, stash, reorder context)
   - Platform event hooks (context updates, token threshold warnings)

2. **MCP Server Core**
   - Standard MCP protocol implementation
   - Context management tools exposed via MCP
   - Context analysis engine (relevance scoring, pruning logic)
   - Storage layer (stashed context, metadata)

3. **Agent Interaction**
   - Agent calls MCP tools
   - Tools use platform integration to read/modify context
   - Platform sends updated context to LLM

## 4. Platform Integration Strategies

### Strategy 1: Extension/Plugin Architecture

**Approach**: Integrate as a platform extension/plugin

**Examples**:
- **VS Code**: VS Code extension that hooks into the editor's context management
- **Cursor**: Cursor plugin/extension that extends Cursor's context system
- **Kiro**: Kiro plugin that integrates with their platform

**Pros**:
- Deep integration with platform
- Can access internal context APIs
- Can hook into context building pipeline

**Cons**:
- Platform-specific implementation required
- May require platform vendor cooperation
- More complex deployment

**Implementation Pattern**:
```python
# Platform adapter interface
class PlatformAdapter:
    def read_context(self) -> ContextState:
        """Read current context from platform"""
        pass
    
    def modify_context(self, modifications: ContextModifications) -> None:
        """Apply context modifications at platform level"""
        pass
    
    def get_token_count(self) -> TokenUsage:
        """Get current token usage statistics"""
        pass

# Cursor-specific adapter
class CursorAdapter(PlatformAdapter):
    def read_context(self) -> ContextState:
        # Use Cursor's extension API or internal APIs
        # Access conversation history, selected files, etc.
        pass
```

### Strategy 2: API/Webhook Integration

**Approach**: Platform exposes APIs for context management, MCP server uses them

**Examples**:
- Platform provides REST API for context read/write
- Platform sends webhooks on context events
- MCP server calls platform APIs

**Pros**:
- Standardized interface
- Works across platforms if they adopt similar APIs
- Easier to implement

**Cons**:
- Requires platform to expose APIs (may not exist)
- Less deep integration
- Potential latency from API calls

**Implementation Pattern**:
```python
class APIPlatformAdapter(PlatformAdapter):
    def __init__(self, platform_api_url: str, api_key: str):
        self.api_client = PlatformAPIClient(platform_api_url, api_key)
    
    def read_context(self) -> ContextState:
        return self.api_client.get_context()
    
    def modify_context(self, modifications: ContextModifications) -> None:
        self.api_client.patch_context(modifications)
```

### Strategy 3: File System / Configuration Integration

**Approach**: Monitor and modify platform's context files/configuration

**Examples**:
- Platform stores context in files (chat history, session state)
- MCP server reads/writes these files directly
- Platform picks up changes

**Pros**:
- No special APIs needed
- Works with platforms that store context locally
- Simple implementation

**Cons**:
- File format dependencies
- Platform must reload context files
- Less reliable (file locking, timing issues)

**Implementation Pattern**:
```python
class FileSystemAdapter(PlatformAdapter):
    def __init__(self, context_file_path: Path):
        self.context_file = context_file_path
    
    def read_context(self) -> ContextState:
        with open(self.context_file, 'r') as f:
            return ContextState.from_file(f)
    
    def modify_context(self, modifications: ContextModifications) -> None:
        context = self.read_context()
        context.apply(modifications)
        with open(self.context_file, 'w') as f:
            context.to_file(f)
```

### Strategy 4: Hybrid Approach (Recommended)

**Approach**: Support multiple integration methods with platform detection

- Try extension API first (if available)
- Fall back to file system monitoring
- Use webhooks for real-time updates
- Support configuration-based integration

**Benefits**:
- Maximum compatibility
- Works across different platform architectures
- Graceful degradation

## 5. Platform-Specific Considerations

### Cursor Integration

**Context Management**:
- Cursor maintains context in chat sessions
- Uses token counting (tiktoken) client-side
- Summarizes at ~90% of context window
- Supports Max Mode for larger contexts

**Integration Points**:
1. **VS Code Extension API**: Cursor is built on VS Code, can use VS Code extension APIs
2. **Cursor Settings**: Configuration files for context management
3. **Chat Session Files**: May store chat history in files

**Approach**: VS Code extension that hooks into Cursor's context pipeline

### Kiro Integration

**Context Management**:
- Similar pattern to Cursor
- Platform-specific implementation

**Integration Points**:
- TBD: Research Kiro's architecture
- Likely similar extension/plugin approach

### Claude Code Integration

**Context Management**:
- Anthropic's coding agent platform
- Uses Claude API with context management

**Integration Points**:
1. **Anthropic SDK**: May have context management APIs
2. **Extension API**: If built on extensible platform
3. **Configuration**: Context settings and limits

**Approach**: TBD based on Claude Code's architecture

### Claude Desktop Integration

**Context Management**:
- Desktop application for Claude
- Manages conversation context locally

**Integration Points**:
- MCP protocol integration (already supports MCP servers)
- Configuration files for context settings
- Local storage for conversation history

**Approach**: MCP server integration (may be easier than other platforms)

## 6. Plug-and-Play Architecture

### Adapter Pattern

Implement platform adapters that conform to a common interface:

```python
# Core interface
class PlatformAdapter(ABC):
    @abstractmethod
    def read_context(self) -> ContextState:
        """Read current context from platform"""
        pass
    
    @abstractmethod
    def modify_context(self, modifications: ContextModifications) -> None:
        """Apply context modifications"""
        pass
    
    @abstractmethod
    def get_token_count(self) -> TokenUsage:
        """Get token usage statistics"""
        pass
    
    @abstractmethod
    def subscribe_to_updates(self, callback: Callable) -> None:
        """Subscribe to context update events"""
        pass

# Platform registry
class PlatformRegistry:
    _adapters: Dict[str, Type[PlatformAdapter]] = {}
    
    @classmethod
    def register(cls, platform_name: str, adapter_class: Type[PlatformAdapter]):
        cls._adapters[platform_name] = adapter_class
    
    @classmethod
    def create_adapter(cls, platform_name: str, config: Dict) -> PlatformAdapter:
        adapter_class = cls._adapters.get(platform_name)
        if not adapter_class:
            raise ValueError(f"Unknown platform: {platform_name}")
        return adapter_class(**config)
```

### Platform Detection

Auto-detect platform and load appropriate adapter:

```python
class PlatformDetector:
    @staticmethod
    def detect() -> Optional[str]:
        """Detect current platform"""
        # Check environment variables
        # Check for platform-specific files/directories
        # Check running processes
        # Check VS Code workspace settings
        
        if "CURSOR" in os.environ:
            return "cursor"
        elif os.path.exists(Path.home() / ".claude"):
            return "claude_desktop"
        # ... more detection logic
        
        return None
```

### Configuration-Based Setup

Allow users to configure platform integration:

```yaml
# mcp-server-config.yaml
platform:
  name: cursor  # or auto-detect
  adapter: extension  # extension, api, filesystem, hybrid
  
  cursor:
    extension_path: /path/to/cursor/extension
    context_file: ~/.cursor/chat-context.json
    
  claude_desktop:
    config_dir: ~/.claude
    mcp_integration: true
```

## 7. Context Modification Pipeline

### Read-Modify-Write Pattern

```python
# 1. Agent calls MCP tool
@mcp_tool("prune_context")
def prune_context(relevance_threshold: float) -> PruneResult:
    # 2. Read current context from platform
    context = platform_adapter.read_context()
    
    # 3. Analyze and prune
    analysis = analyze_context(context)
    modifications = create_pruning_modifications(analysis, relevance_threshold)
    
    # 4. Apply modifications at platform level
    platform_adapter.modify_context(modifications)
    
    # 5. Return result to agent
    return PruneResult(
        removed_segments=modifications.removed,
        tokens_freed=modifications.tokens_freed,
        remaining_tokens=platform_adapter.get_token_count()
    )
```

### Context Modification Types

```python
@dataclass
class ContextModifications:
    """Represents modifications to apply to context"""
    
    remove_segments: List[ContextSegment] = field(default_factory=list)
    stash_segments: List[ContextSegment] = field(default_factory=list)
    reorder_segments: Dict[int, int] = field(default_factory=dict)
    protect_segments: List[str] = field(default_factory=list)  # segment IDs
    add_segments: List[ContextSegment] = field(default_factory=list)
```

### Atomic Operations

Ensure context modifications are atomic:

```python
class ContextModifier:
    def apply_modifications(self, modifications: ContextModifications) -> None:
        # 1. Validate modifications
        self._validate(modifications)
        
        # 2. Create backup
        backup = self._create_backup()
        
        try:
            # 3. Apply modifications
            self._apply(modifications)
            
            # 4. Verify integrity
            self._verify()
        except Exception as e:
            # 5. Rollback on error
            self._restore(backup)
            raise
```

## 8. MCP Tools That Require Platform Integration

### Tools That Read Context

- `check_context_usage()` - Needs platform token counting
- `analyze_context()` - Needs to read context structure
- `list_context_segments()` - Needs to enumerate context parts

### Tools That Modify Context

- `prune_context()` - Needs to remove segments at platform level
- `stash_context()` - Needs to remove and store segments
- `protect_context()` - Needs to mark segments as protected
- `reorder_context()` - Needs to change context ordering

### Tools That Don't Need Platform Integration

- `retrieve_stashed_context()` - Uses MCP server storage
- `search_stashed_context()` - Uses MCP server storage
- `get_pruning_strategies()` - Pure logic, no platform access

## 9. Implementation Phases

### Phase 1: Platform-Agnostic Core

- MCP server core (without platform integration)
- Context analysis logic
- Storage layer for stashed context
- Tools that don't require platform access

### Phase 2: Platform Adapter Framework

- Platform adapter interface
- Platform detection
- Adapter registry
- Configuration system

### Phase 3: Platform-Specific Adapters

- Cursor adapter (VS Code extension)
- Claude Desktop adapter (MCP integration)
- File system adapter (for testing/fallback)

### Phase 4: Advanced Features

- Real-time context monitoring
- Proactive pruning triggers
- Multi-platform support in single session

## 10. Decisions Summary

- **D1: Platform Integration Required** - MCP server must integrate with platforms, not just LLMs
  - **Rationale**: Context is managed at platform level, not LLM level

- **D2: Plug-and-Play Architecture** - Support multiple platforms via adapter pattern
  - **Rationale**: Different platforms have different architectures, need flexible integration

- **D3: Extension/Plugin Primary Strategy** - Prioritize extension-based integration
  - **Rationale**: Deepest integration, most control over context management

- **D4: Hybrid Integration Approach** - Support multiple integration methods per platform
  - **Rationale**: Maximum compatibility, graceful degradation

- **D5: Read-Modify-Write Pattern** - Context modifications happen at platform level
  - **Rationale**: Platform controls context, MCP server provides analysis and commands

- **D6: Atomic Operations** - Context modifications must be atomic with rollback
  - **Rationale**: Prevent corruption of context state

## 11. Open Questions

1. **Platform Cooperation**: Do platform vendors (Cursor, Anthropic) expose APIs for context management?
2. **VS Code Extension API**: What context management APIs are available in VS Code extensions?
3. **Context Format**: What format does each platform use for storing context?
4. **Real-time Updates**: How do platforms notify about context changes? (webhooks, events, polling)
5. **Security**: How do we ensure context modifications are safe and authorized?
6. **Performance**: What's the latency impact of platform integration on tool calls?

## 12. Next Steps

1. Research platform-specific APIs (Cursor, Claude Desktop, Kiro)
2. Prototype VS Code extension adapter
3. Design context state representation
4. Implement platform detection logic
5. Create platform adapter interface and base classes

