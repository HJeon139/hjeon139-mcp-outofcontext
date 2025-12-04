# Design: LLM-Driven Context Compression via Paraphrasing

## 1. Scope & Goals

### What This Design Covers

This design document outlines a pattern for allowing the LLM agent to actively compress context by paraphrasing and replacing stored context segments in the MCP server. This addresses the recency bias problem where summarization loses critical information about the current state (e.g., where editing was happening, what was in progress).

### Non-Goals

- Not replacing pruning/stashing strategies (complementary approach)
- Not designing automatic compression (agent-driven, not automatic)
- Not designing lossless compression (some detail loss expected but key info preserved)

## 2. Core Problem: Recency Bias Loss

### The Issue

When context is summarized or removed:
- **Recency information is lost**: "We were editing file X at line Y"
- **Active state is lost**: "Currently debugging authentication, last error was..."
- **Progress context is lost**: "Fixed bug A, working on bug B, need to test C"
- **User must re-align**: Explain where they left off, what was being worked on

**Example Failure Scenario**:
```
Original Context:
- "I'm editing src/auth.py, currently at line 45"
- "Fixed the token validation issue, now working on expiration handling"
- "Last error was: 'Token expired' at line 42, I added a check"

Summarized Context:
- "Working on authentication improvements, fixed token validation"

Agent's Understanding After Summary:
- Doesn't know: Which file? Which line? What was last error?
- User must re-explain: "I was editing src/auth.py at line 45..."
```

### The Opportunity

**LLM-driven compression** can preserve recency and active state because:
- LLM understands context and can identify critical active information
- Can paraphrase while maintaining key details (file names, line numbers, progress)
- Can compress verbose explanations while keeping essential facts
- Agent controls compression, understands what's important

## 3. Design Pattern: Replace-with-Compression

### Core Concept

Allow the agent to:
1. **Identify context segments** to compress
2. **Generate compressed version** (paraphrased, shorter)
3. **Replace original with compressed** version in MCP storage
4. **Preserve key metadata** (file paths, line numbers, timestamps)
5. **Optionally expand later** if full detail needed

### Pattern Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Identifies Context                  │
│  - "This context segment is verbose"                        │
│  - "I can compress this while keeping key info"             │
│  - "Active state: editing src/auth.py at line 45"          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ compress_context_segment()
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              LLM Generates Compressed Version                │
│  - Paraphrases verbose explanations                         │
│  - Preserves: file paths, line numbers, active state        │
│  - Maintains: progress, errors, decisions                   │
│  - Removes: redundant details, verbose explanations         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ compressed_segment
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              MCP Server Replaces Context                     │
│  - Store compressed version                                 │
│  - Preserve metadata (original_id, compressed_at)           │
│  - Link to original (for expansion if needed)               │
│  - Update context at platform level                         │
└─────────────────────────────────────────────────────────────┘
```

## 4. Context Segment Compression Model

### Segment Structure

```python
@dataclass
class ContextSegment:
    segment_id: str
    text: str
    type: SegmentType
    metadata: SegmentMetadata
    compression_state: CompressionState
    
@dataclass
class SegmentMetadata:
    file_path: Optional[str]  # Preserved during compression
    line_number: Optional[int]  # Preserved during compression
    timestamp: datetime
    topic: Optional[str]
    tokens: int
    
@dataclass
class CompressionState:
    is_compressed: bool
    original_id: Optional[str]  # Link to original if compressed
    compressed_at: Optional[datetime]
    compression_ratio: Optional[float]  # e.g., 0.6 = 60% of original
    preserved_metadata: Dict[str, Any]  # What was explicitly preserved
```

### Compression vs. Summarization

**Key Differences**:

| Aspect | Summarization | LLM-Driven Compression |
|--------|--------------|----------------------|
| **Goal** | Create summary | Paraphrase while preserving key info |
| **Approach** | Extract/abstract | Intelligent paraphrasing |
| **Metadata Preservation** | May lose | Explicitly preserved |
| **Recency Info** | Often lost | Maintained (file, line, state) |
| **Reversibility** | Limited | Can expand with original link |
| **Agent Control** | Automatic | Agent-initiated |

**Example**:

**Original** (200 tokens):
```
I'm currently editing src/auth.py. I'm at line 45 working on the 
authenticate_user function. I just fixed a bug where expired tokens 
were causing 500 errors instead of 401. The fix was to add a check 
before the token validation that returns 401 immediately if the token 
is expired. The error was occurring because the expired token check 
was happening after the database query, which would throw an exception. 
Now I'm working on handling the case where the token format is invalid.
```

**Summarized** (40 tokens) - loses recency:
```
Working on authentication improvements. Fixed expired token error 
handling, now addressing invalid token format.
```

**LLM-Compressed** (80 tokens) - preserves recency:
```
Editing src/auth.py:45, authenticate_user(). Fixed: expired tokens 
now return 401 (was 500). Added pre-validation check. Current: 
handling invalid token format.
```

## 5. MCP Tool: compress_context_segment

### Tool Definition

```python
@mcp_tool("compress_context_segment")
def compress_context_segment(
    segment_ids: List[str],
    preserve_metadata: Optional[List[str]] = None,
    target_compression_ratio: float = 0.6,
    preserve_active_state: bool = True
) -> CompressionResult:
    """
    Compress context segments by paraphrasing while preserving key information.
    
    This allows the agent to reduce context size while maintaining critical
    details like file paths, line numbers, active state, and progress information.
    Preserves recency bias by maintaining "where we are" information.
    
    Args:
        segment_ids: IDs of segments to compress
        preserve_metadata: Specific metadata to explicitly preserve 
                          (e.g., ['file_path', 'line_number', 'error'])
        target_compression_ratio: Target size ratio (0.6 = 60% of original)
        preserve_active_state: Whether to preserve active state info 
                              (current file, line, progress)
    
    Returns:
        CompressionResult with compressed segments and space saved
    """
```

### Compression Instructions to LLM

When agent calls this tool, the MCP server uses LLM to compress:

```python
def generate_compressed_version(
    original_segment: ContextSegment,
    preserve_metadata: List[str],
    preserve_active_state: bool,
    target_ratio: float
) -> str:
    """Generate compressed version using LLM"""
    
    # Build compression prompt
    prompt = f"""
Compress the following context segment while preserving critical information.

Original Context ({original_segment.tokens} tokens):
{original_segment.text}

Compression Requirements:
1. Reduce to approximately {int(original_segment.tokens * target_ratio)} tokens
2. Preserve ALL of the following:
   - File paths and line numbers
   - Active state (what's currently being worked on)
   - Recent errors and their locations
   - Progress information (what's done, what's next)
   - Critical decisions and rationale
3. Remove:
   - Verbose explanations that don't add critical info
   - Redundant details
   - Historical details not needed for current state
4. Maintain recency bias: Always preserve "where we are" and "what we're doing"

Preserve these specific metadata fields:
{', '.join(preserve_metadata)}

Active State Preservation: {preserve_active_state}

Generate a compressed version that maintains all critical information while 
being more concise. Focus on preserving recency and active state.
"""
    
    # Call LLM for compression
    compressed_text = llm.generate(prompt)
    return compressed_text
```

### Example Compression

**Input Segment**:
```
Segment ID: msg_123
Type: conversation_message
Text: "I'm currently editing the authentication middleware in src/auth.py. 
I've reached line 45 where the authenticate_user function is defined. 
I just finished fixing a bug where expired tokens were causing 500 
Internal Server Errors instead of the expected 401 Unauthorized response. 
The issue was that the token expiration check was happening after the 
database query, which would throw an exception when the token was expired. 
I added a pre-validation check that returns 401 immediately if the token 
is expired, before any database operations. Now I'm working on handling 
the case where the token format is invalid - specifically when the Bearer 
prefix is missing or malformed. The error handling for this case needs 
to be added around line 50."
Tokens: 180
Metadata: {file_path: "src/auth.py", line_number: 45, topic: "authentication"}
```

**Compressed Output**:
```
Segment ID: msg_123
Type: conversation_message (compressed)
Text: "Editing src/auth.py:45, authenticate_user(). Fixed: expired tokens 
now return 401 (was 500) via pre-validation check. Current: handling 
invalid token format (malformed Bearer prefix) at line 50."
Tokens: 45
Compression Ratio: 0.25 (75% reduction)
Metadata: {file_path: "src/auth.py", line_number: 45, topic: "authentication", 
          original_id: "msg_123", compressed_at: "2024-01-15T10:30:00"}
```

**Key Preserved Elements**:
- ✅ File path: `src/auth.py`
- ✅ Line numbers: 45, 50
- ✅ Active state: "Editing", "Current"
- ✅ Progress: Fixed expired tokens, working on invalid format
- ✅ Errors: 500 → 401 issue
- ✅ Location: Line 50 for next work

## 6. Metadata Preservation Strategy

### Critical Metadata to Always Preserve

**Active State Metadata**:
```python
PRESERVE_ALWAYS = [
    "file_path",          # Current file being edited
    "line_number",        # Current position
    "function_name",      # Current function/method
    "active_task",        # What's currently being worked on
    "last_error",         # Most recent error
    "error_location",     # Where error occurred
    "progress_state",     # What's done, what's next
]
```

**Recency Metadata**:
```python
RECENCY_METADATA = [
    "current_file",       # File currently open/editing
    "cursor_position",    # Exact cursor location
    "recent_changes",     # Recent edits made
    "pending_work",       # What needs to be done next
]
```

### Metadata Extraction and Preservation

```python
def extract_preserved_metadata(
    segment: ContextSegment,
    preserve_list: List[str]
) -> Dict[str, Any]:
    """Extract metadata that must be preserved"""
    
    preserved = {}
    
    # Extract from text using patterns/LLM
    if "file_path" in preserve_list:
        preserved["file_path"] = extract_file_path(segment.text)
    
    if "line_number" in preserve_list:
        preserved["line_number"] = extract_line_number(segment.text)
    
    if "active_state" in preserve_list:
        preserved["active_state"] = extract_active_state(segment.text)
    
    # ... extract other metadata
    
    return preserved

def inject_preserved_metadata(
    compressed_text: str,
    metadata: Dict[str, Any]
) -> str:
    """Ensure compressed text explicitly includes preserved metadata"""
    
    # Build metadata summary
    metadata_parts = []
    if metadata.get("file_path"):
        metadata_parts.append(f"File: {metadata['file_path']}")
    if metadata.get("line_number"):
        metadata_parts.append(f"Line: {metadata['line_number']}")
    if metadata.get("active_state"):
        metadata_parts.append(f"State: {metadata['active_state']}")
    
    if metadata_parts:
        return f"[{', '.join(metadata_parts)}] {compressed_text}"
    return compressed_text
```

## 7. Compression Strategies

### Strategy 1: Active State Compression

**Focus**: Preserve "where we are" and "what we're doing"

**Compression Pattern**:
```
Original: "I'm currently editing src/auth.py at line 45. I've been working 
on the authenticate_user function. I just fixed..."

Compressed: "Editing src/auth.py:45, authenticate_user(). Fixed..."
```

**Preserved**:
- File path and line number
- Current function/context
- Active work item

**Removed**:
- Verbose phrasing ("I'm currently", "I've been working")
- Redundant context

### Strategy 2: Progress Compression

**Focus**: Preserve progress and next steps

**Compression Pattern**:
```
Original: "I fixed the token expiration bug. The issue was... Now I need 
to handle invalid token formats. Specifically, I need to..."

Compressed: "Done: fixed token expiration (pre-validation check). Next: 
invalid token format handling at line 50."
```

**Preserved**:
- What's completed
- What's next
- Location for next work

**Removed**:
- Detailed explanations of completed work
- Verbose "need to" phrasing

### Strategy 3: Error Compression

**Focus**: Preserve error information and location

**Compression Pattern**:
```
Original: "I encountered an error. The error message was 'Token expired' 
and it occurred at line 42 in the authenticate_user function..."

Compressed: "Error: 'Token expired' at src/auth.py:42 in authenticate_user()."
```

**Preserved**:
- Error message
- Exact location
- Context (function name)

**Removed**:
- Verbose error description
- Redundant context

### Strategy 4: Decision Compression

**Focus**: Preserve decisions and rationale concisely

**Compression Pattern**:
```
Original: "After discussing the options, I decided to use approach A because 
it's simpler and more maintainable. The alternative approach B would have..."

Compressed: "Decision: use approach A (simpler, more maintainable)."
```

**Preserved**:
- Decision made
- Key rationale

**Removed**:
- Detailed discussion
- Alternative analysis

## 8. Agent Control and Decision Making

### When Should Agent Compress?

**Good Candidates for Compression**:

1. **Verbose Explanations**:
   - Long explanations that can be paraphrased
   - Redundant details already captured elsewhere
   - Historical context that's less critical

2. **Completed Work**:
   - Finished tasks with verbose descriptions
   - Resolved issues with long explanations
   - Completed features that can be summarized

3. **Non-Active Context**:
   - Context not currently being worked on
   - Background information
   - Reference material that's verbose

**Bad Candidates for Compression**:

1. **Active State**:
   - Current file and line being edited
   - What's currently being worked on
   - Next immediate task

2. **Critical Details**:
   - Exact error messages being debugged
   - Code currently being written
   - Configuration values in use

3. **Recent Context**:
   - Last few messages (keep full detail)
   - Very recent decisions
   - Currently relevant information

### Agent Decision Logic

```python
def should_compress_segment(segment: ContextSegment, context_state: ContextState) -> bool:
    """Determine if segment is a good candidate for compression"""
    
    # Don't compress if:
    if segment.is_active():
        return False  # Currently being worked on
    
    if segment.is_recent(threshold_minutes=10):
        return False  # Too recent, might be needed
    
    if segment.protected:
        return False  # User explicitly protected
    
    if segment.tokens < 100:
        return False  # Too small, compression not worth it
    
    # Good candidates:
    if segment.is_verbose(ratio=0.7):  # >70% verbose phrasing
        return True
    
    if segment.is_completed_topic():
        return True  # Completed work can be compressed
    
    if segment.tokens > 200 and not segment.is_critical():
        return True  # Large segments that aren't critical
    
    return False
```

## 9. Reversibility and Expansion

### Storing Original

When compressing, store original for potential expansion:

```python
@dataclass
class CompressionRecord:
    compressed_id: str  # ID of compressed segment
    original_id: str    # ID of original segment
    original_text: str  # Full original text
    compressed_at: datetime
    compression_ratio: float
    preserved_metadata: Dict[str, Any]

# Store in MCP server
compression_registry: Dict[str, CompressionRecord] = {}
```

### Expansion Tool

```python
@mcp_tool("expand_compressed_context")
def expand_compressed_context(
    segment_id: str
) -> ExpandResult:
    """
    Expand a compressed segment back to original version.
    
    Useful when full detail is needed for deep context.
    """
    # Retrieve original from registry
    record = compression_registry.get(segment_id)
    if not record:
        return ExpandResult(error="No compression record found")
    
    # Replace compressed with original
    # (or add original alongside compressed)
    return ExpandResult(
        original_text=record.original_text,
        expanded_at=datetime.now()
    )
```

### Hybrid Approach: Compressed + Stashed

Optionally store original in stash for retrieval:

```python
def compress_and_stash_original(segment: ContextSegment) -> CompressionResult:
    """Compress segment and stash original for later retrieval"""
    
    # Compress segment
    compressed = compress_segment(segment)
    
    # Stash original in vector DB for semantic retrieval
    stash_segment(segment)  # Original in stash
    
    # Use compressed in active context
    replace_segment(segment.id, compressed)
    
    return CompressionResult(
        compressed_segment=compressed,
        original_stashed=True,
        can_retrieve=True
    )
```

## 10. Integration with Existing Strategies

### Three-Part Context Management

1. **Keep Active** (Verbose, Full Detail):
   - Current file, line, task
   - Recent messages
   - Active code being edited

2. **Compress Verbose** (LLM-Driven):
   - Long explanations
   - Completed work with verbose descriptions
   - Background context that's verbose

3. **Stash Detailed** (For Retrieval):
   - Detailed debugging sessions
   - Long code examples
   - Extensive logs

### Decision Tree

```
Context Segment
    │
    ├─ Is active/recent? → KEEP (verbatim)
    │
    ├─ Is verbose but relevant? → COMPRESS (LLM-driven)
    │
    ├─ Is detailed but not needed soon? → STASH (for retrieval)
    │
    └─ Is irrelevant/complete? → REMOVE
```

### Combined Workflow

```python
def manage_context_intelligently(segments: List[ContextSegment]) -> None:
    """Intelligent context management combining all strategies"""
    
    for segment in segments:
        if segment.is_active() or segment.is_recent():
            # Keep verbatim - active state
            keep_segment(segment)
        
        elif segment.is_verbose() and segment.is_relevant():
            # Compress - reduce size while preserving key info
            compressed = compress_segment(segment)
            replace_segment(segment.id, compressed)
        
        elif segment.is_detailed() and not segment.needed_soon():
            # Stash - remove but keep for retrieval
            stash_segment(segment)
        
        elif segment.is_irrelevant() or segment.is_complete():
            # Remove - no longer needed
            remove_segment(segment)
```

## 11. MCP Tool Implementation

### Tool: compress_context_segment

```python
@mcp_tool("compress_context_segment")
def compress_context_segment(
    segment_ids: List[str],
    preserve_metadata: Optional[List[str]] = None,
    target_compression_ratio: float = 0.6,
    preserve_active_state: bool = True
) -> CompressionResult:
    """
    Compress context segments by paraphrasing while preserving key information.
    
    This tool allows the agent to reduce context size while maintaining critical
    details like file paths, line numbers, active state, and progress information.
    Preserves recency bias by maintaining "where we are" information.
    
    Use this when:
    - Context segments are verbose but contain important information
    - You need to reduce context size while preserving active state
    - Completed work can be condensed without losing critical details
    - Background context is too verbose for current needs
    
    Args:
        segment_ids: List of segment IDs to compress
        preserve_metadata: Specific metadata fields to preserve
                          Default: ['file_path', 'line_number', 'active_state']
        target_compression_ratio: Target size (0.6 = 60% of original)
        preserve_active_state: Whether to preserve active state info
    
    Returns:
        CompressionResult with compressed segments and tokens saved
    """
    # Implementation
    results = []
    total_tokens_saved = 0
    
    for segment_id in segment_ids:
        segment = get_segment(segment_id)
        
        # Generate compressed version
        compressed_text = generate_compressed_version(
            segment,
            preserve_metadata or DEFAULT_PRESERVE_METADATA,
            preserve_active_state,
            target_compression_ratio
        )
        
        # Create compressed segment
        compressed = create_compressed_segment(segment, compressed_text)
        
        # Store compression record (for expansion)
        store_compression_record(segment.id, compressed.id, segment.text)
        
        # Replace in context
        replace_segment(segment.id, compressed)
        
        tokens_saved = segment.tokens - compressed.tokens
        total_tokens_saved += tokens_saved
        
        results.append({
            "segment_id": segment.id,
            "compressed_id": compressed.id,
            "original_tokens": segment.tokens,
            "compressed_tokens": compressed.tokens,
            "tokens_saved": tokens_saved,
            "compression_ratio": compressed.tokens / segment.tokens
        })
    
    return CompressionResult(
        compressed_segments=results,
        total_tokens_saved=total_tokens_saved,
        can_expand=True  # Originals stored for expansion
    )
```

### Tool: expand_compressed_context

```python
@mcp_tool("expand_compressed_context")
def expand_compressed_context(
    segment_id: str
) -> ExpandResult:
    """
    Expand a compressed segment back to its original version.
    
    Use this when you need the full detail from a compressed segment.
    The original text is retrieved from storage.
    """
    # Retrieve compression record
    record = compression_registry.get(segment_id)
    if not record:
        return ExpandResult(error="Segment not found or not compressed")
    
    # Get original segment
    original = get_segment(record.original_id)
    
    # Replace compressed with original
    replace_segment(segment_id, original)
    
    return ExpandResult(
        segment_id=segment_id,
        original_text=record.original_text,
        expanded_at=datetime.now()
    )
```

## 12. Performance Considerations

### LLM Call Costs

**Cost Analysis**:
- Compression requires LLM call per segment
- Cost: ~$0.01-0.05 per compression (depending on model)
- Benefit: Saves tokens in every subsequent request
- **Break-even**: If segment is used in >10-20 requests, compression pays off

**Optimization**:
- Batch compression of multiple segments
- Cache compression results
- Only compress if significant token savings expected

### Compression Quality

**Validation**:
- Check that preserved metadata is actually present
- Verify compression ratio is achieved
- Ensure critical information isn't lost

**Fallback**:
- If compression fails quality check, keep original
- Allow agent to retry with different parameters
- Provide feedback on what was preserved vs. lost

## 13. Decisions Summary

- **D1: LLM-Driven Compression as Complementary Strategy**
  - **Rationale**: Preserves recency bias better than automatic summarization

- **D2: Agent Control Over Compression**
  - **Rationale**: Agent understands context and can decide what to compress

- **D3: Always Preserve Active State Metadata**
  - **Rationale**: Recency information (file, line, state) is critical

- **D4: Store Originals for Expansion**
  - **Rationale**: Reversibility enables retrieving full detail when needed

- **D5: Compression vs. Stashing Decision**
  - **Rationale**: Compress if verbose but relevant, stash if detailed but not needed soon

- **D6: Preserve Metadata Explicitly in Compressed Text**
  - **Rationale**: Ensures metadata survives compression process

## 14. Implementation Phases

### Phase 1: Basic Compression Tool
- Single-segment compression
- Basic metadata preservation
- Store compression records

### Phase 2: Enhanced Preservation
- Extract and inject metadata explicitly
- Multiple preservation strategies
- Compression quality validation

### Phase 3: Expansion Support
- Expand compressed segments
- Hybrid compression + stashing
- Compression registry management

### Phase 4: Advanced Features
- Batch compression
- Compression caching
- Adaptive compression strategies

## 15. Open Questions

1. **Compression Quality**: How to validate that critical info is preserved?
2. **Metadata Extraction**: LLM-based or pattern-based extraction?
3. **Expansion Strategy**: Always store original or optional?
4. **Cost vs. Benefit**: When is compression cost-effective?
5. **Agent Guidance**: How to help agent decide what to compress?
6. **Hybrid Storage**: Compress + stash original or just compress?

## 16. References

- **Context Summarization Research**: `docs/research/context_summarization_compression.md`
- **Recency Bias in LLMs**: Cognitive bias research on recency effects
- **Paraphrasing Techniques**: NLP research on text paraphrasing
- **Metadata Preservation**: Information extraction research

