# Research: Context Summarization and Compression Techniques

## Research Objective

Understand existing approaches to context compression and summarization, and determine how they fit into our context management strategy (complementary vs. primary approach).

## Research Questions

1. **Summarization Techniques**
   - How do existing summarization approaches work for context?
   - What information is preserved vs. lost in summarization?
   - What are the limitations of summarization?
   - Can summarization be lossless for important details?

2. **Compression Strategies**
   - What context compression techniques exist?
   - How do we compress context while preserving key information?
   - What's the compression ratio vs. information retention trade-off?
   - Can compression be reversible (decompression on demand)?

3. **Selective Summarization**
   - Can we summarize less important context while keeping detailed important context?
   - How do we determine what to summarize vs. keep verbatim?
   - What's the granularity of summarization (per-message, per-topic)?
   - How do we maintain context hierarchy during summarization?

4. **Lossy vs. Lossless**
   - What context can be summarized without loss?
   - What context must be preserved verbatim?
   - How do we handle code snippets vs. conversation differently?
   - What's the user experience impact of summarization?

5. **Integration with Pruning**
   - How does summarization complement pruning?
   - When to summarize vs. remove vs. stash?
   - Can summarization reduce context size enough to avoid pruning?
   - What's the combined strategy (summarize + prune + stash)?

## Deliverables

- [x] **Summarization Assessment**: Current state and limitations
- [x] **Compression Strategy**: When and how to use summarization
- [x] **Selective Approach**: What to summarize vs. preserve
- [x] **Integration Plan**: How summarization fits with pruning/stashing
- [x] **Recommendation**: Primary vs. complementary role for summarization

## Status

- ✅ Completed

## Key Findings

### 1. Summarization Techniques and Their Characteristics

#### Extractive Summarization

**How It Works**:
- Selects and concatenates key sentences/phrases directly from source text
- Uses scoring methods (TF-IDF, importance scoring) to identify important content
- Maintains original wording, preserves factual accuracy

**Characteristics**:
- **Preserves**: Original wording, exact facts, direct quotes
- **Loses**: Context relationships, narrative flow, nuanced explanations
- **Limitations**: 
  - May lack coherence or fluidity
  - Doesn't combine information across sentences
  - Can result in disjointed summaries

**Example**: Extracting key sentences from a debugging conversation:
```
Original: "I noticed the error occurs when users with expired sessions try to access the API. 
The authentication middleware checks for token validity but doesn't handle expiration gracefully. 
I added a check in the middleware to return 401 immediately if token is expired."

Extracted: "Error occurs when users with expired sessions try to access the API. 
Authentication middleware checks for token validity but doesn't handle expiration gracefully."
```

#### Abstractive Summarization

**How It Works**:
- Generates new sentences that capture essence of original text
- Uses transformer models (BERT, GPT) to understand and rephrase
- Produces more natural, coherent summaries

**Characteristics**:
- **Preserves**: Core ideas, semantic meaning, coherent narrative
- **Loses**: Exact wording, specific details, nuances, subtle context
- **Limitations**:
  - Potential information loss or inaccuracies
  - May introduce errors in factual details
  - Requires more computation

**Example**: Abstractive summary of same debugging conversation:
```
Abstractive: "Authentication errors occur with expired user sessions. 
The middleware needs to handle token expiration more gracefully. 
Added immediate 401 response for expired tokens."
```

**Key Problem**: The abstractive summary loses the specific insight about "when users with expired sessions try to access the API" - this nuance might be critical for debugging.

#### Hybrid Approaches

**How It Works**:
- Combines extractive and abstractive methods
- First identifies key sentences (extractive)
- Then rephrases for coherence (abstractive)

**Characteristics**:
- **Preserves**: Balance of accuracy and coherence
- **Loses**: Still loses some nuance, but less than pure abstractive
- **Benefits**: More coherent than extractive, more accurate than abstractive

#### Advanced Techniques

**KV-Distill** (Key-Value Cache Distillation):
- Distills long context key-value caches into shorter representations
- Preserves pre-trained model capabilities
- Question-independent compression
- **Application**: Could compress entire conversation history

**DAST** (Dynamic Allocation of Soft Tokens):
- Uses LLM's understanding of contextual relevance
- Dynamically allocates soft tokens to information-rich chunks
- Combines perplexity-based local info with attention-driven global info
- **Application**: More intelligent compression based on relevance

**RECOMP** (Retrieval-Augmented Compression):
- Compresses retrieved documents into summaries before integration
- Reduces computational costs
- Relieves burden on LLMs to identify relevant info
- **Application**: Similar to our RAG approach for stashed context

### 2. Information Loss and Limitations

#### What Gets Lost in Summarization

1. **Nuanced Details**:
   - Specific conditions, edge cases
   - Exact error messages, stack traces
   - Precise timestamps, version numbers
   - Subtle context relationships

2. **Alignment Context**:
   - User's specific phrasing and mental model
   - Shared understanding developed through conversation
   - Task-specific terminology and conventions
   - Implicit assumptions and background knowledge

3. **Structural Information**:
   - Code structure and organization
   - Conversation flow and dependencies
   - Logical relationships between ideas
   - Hierarchical organization of information

4. **Temporal Context**:
   - Sequence of decisions
   - Evolution of understanding
   - What was tried and why it failed
   - Progressive refinement of ideas

#### Why This Causes Re-alignment Overhead

**The Re-alignment Problem** (as mentioned by user):
1. Agent summarizes context to fit within limits
2. Summary loses nuanced details and alignment context
3. User must re-explain current state, what was working on
4. Shared understanding is broken, requires rebuilding

**Example Scenario**:
```
Original Context (1000 tokens):
- Detailed debugging session with specific error messages
- Step-by-step troubleshooting process
- User's specific requirements and constraints
- Code examples with explanations

Summarized (200 tokens):
- "Debugged authentication issue, fixed token expiration handling"

Agent's Understanding After Summary:
- Knows: Authentication issue was fixed
- Doesn't know: Specific errors, user's requirements, why certain approaches were taken
- User must re-explain: What specific issue, what constraints, current state
```

#### Compression Ratios and Trade-offs

**Reported Compression Ratios**:
- **60-80% token reduction** (60-80% cost savings)
- Typical compression: 4:1 to 5:1 (1000 tokens → 200-250 tokens)
- High compression (10:1): Significant information loss
- Low compression (2:1): Less information loss, less space savings

**Trade-off Curve**:
```
Compression Ratio  |  Information Retention  |  Use Case
------------------|------------------------|------------------
1:1 (no compression) | 100%                  | Critical details needed
2:1                  | ~80-90%               | Important but not critical
4:1                  | ~60-70%               | General context
10:1                 | ~30-40%               | High-level overview only
```

### 3. Selective Summarization Strategies

#### What to Summarize vs. Preserve

**Preserve Verbatim**:
1. **Active/Recent Context**:
   - Current task/goal state
   - Recent decisions and rationale
   - Active code/file context
   - Last few conversation messages

2. **Critical Details**:
   - Exact error messages, stack traces
   - Code snippets currently being worked on
   - User-specific requirements and constraints
   - Protected segments (user-marked)

3. **Reference Information**:
   - Code that's actively referenced
   - API specifications being used
   - Configuration values in use

**Safe to Summarize**:
1. **Completed Topics**:
   - Resolved issues (keep summary, remove details)
   - Finished features (high-level summary)
   - Closed discussion threads

2. **Redundant Information**:
   - Repeated explanations
   - Similar error logs
   - Duplicate code examples

3. **Historical Context**:
   - Old conversation topics
   - Past decisions already implemented
   - Outdated code versions

#### Granularity of Summarization

**Per-Message Summarization**:
- Summarize individual messages when context gets full
- Preserves recent messages, summarizes older ones
- **Issue**: Can break conversation flow

**Per-Topic Summarization**:
- Group related messages into topics
- Summarize entire topics when complete
- **Benefit**: Maintains topic coherence

**Hierarchical Summarization**:
- Keep detailed summary of recent context
- Progressively summarize older context
- **Structure**: 
  - Last 10 messages: Full detail
  - Next 20 messages: Detailed summary
  - Older messages: High-level summary

**Example Hierarchical Structure**:
```
Recent Context (Full Detail):
  - Last 5 messages: verbatim
  
Intermediate Context (Detailed Summary):
  - Messages 6-15: paragraph summary per topic
  
Historical Context (High-Level Summary):
  - Older messages: bullet-point summary of topics covered
```

### 4. Compression Strategies for Different Content Types

#### Code Snippets

**Challenges**:
- Code structure is critical
- Exact syntax matters
- Comments and explanations provide context

**Strategies**:
1. **Preserve Structure**:
   - Keep function/class definitions
   - Summarize implementation details
   - Keep comments that explain "why"

2. **Extract Key Patterns**:
   - Show code structure
   - Summarize implementation approach
   - Preserve critical logic

**Example**:
```
Original Code (100 tokens):
def authenticate_user(token: str) -> User:
    # Check if token exists
    if not token:
        raise AuthenticationError("Token required")
    
    # Validate token format
    if not token.startswith("Bearer "):
        raise AuthenticationError("Invalid token format")
    
    # Extract actual token
    actual_token = token[7:]  # Remove "Bearer " prefix
    
    # Check expiration
    if is_token_expired(actual_token):
        raise AuthenticationError("Token expired")
    
    # Return user
    return get_user_from_token(actual_token)

Summarized (40 tokens):
def authenticate_user(token: str) -> User:
    # Validates Bearer token format and expiration
    # Returns user if valid, raises AuthenticationError otherwise
    # Implementation: extracts token, checks expiration, retrieves user
```

#### Conversation Messages

**Challenges**:
- Context and nuance are important
- User's phrasing matters
- Conversation flow shows reasoning

**Strategies**:
1. **Extractive for Facts**:
   - Extract key decisions
   - Preserve user requirements
   - Keep important questions/answers

2. **Abstractive for Explanations**:
   - Summarize reasoning processes
   - Condense long explanations
   - Preserve core insights

**Example**:
```
Original (150 tokens):
User: "I'm seeing this weird error where the API returns 500 
when I send a request with an expired token. The error message 
says 'Internal server error' but I think it should be returning 
401 Unauthorized instead. Can you help me debug this?"

Agent: "Let me look at the authentication middleware. I see 
the issue - when the token is expired, the code is throwing 
an exception that gets caught by the error handler, which 
returns a generic 500. We should check token expiration 
before processing and return 401 directly."

Summarized (60 tokens):
User: "API returns 500 for expired tokens, should return 401."
Agent: "Issue in auth middleware - expired tokens trigger 
exception leading to 500. Should check expiration early and 
return 401 directly."
```

#### Error Logs and Debug Output

**Challenges**:
- Exact error messages are critical
- Stack traces show call hierarchy
- Timing information can be important

**Strategies**:
1. **Extract Key Errors**:
   - Keep error message and type
   - Summarize stack trace (keep top frames)
   - Remove redundant log entries

2. **Deduplicate**:
   - Remove repeated errors
   - Keep first occurrence with count
   - Summarize similar errors

**Example**:
```
Original Log (200 tokens):
ERROR: Token validation failed
Traceback (most recent call last):
  File "/app/middleware/auth.py", line 45, in validate_token
    user = db.get_user(token.user_id)
  File "/app/db/user.py", line 123, in get_user
    return User.query.filter_by(id=user_id).first()
  ...
ValueError: Token expired at 2024-01-15 10:30:00

ERROR: Token validation failed
[Same traceback repeated 5 times...]

Summarized (50 tokens):
ERROR: Token validation failed (occurred 6 times)
- Location: auth.py:45 → db/user.py:123
- Root cause: Token expired at 2024-01-15 10:30:00
- Issue: Expired token triggers ValueError in validation
```

### 5. Lossy vs. Lossless Compression

#### Lossless Compression (Theoretical)

**Pure Lossless**: Not achievable for semantic compression
- Can't compress meaning without losing information
- Text compression (gzip) is lossless but doesn't reduce semantic content
- Only reduces redundancy in encoding, not content

#### Near-Lossless Approaches

**Reversible Summarization** (Conceptual):
- Store full context + summary
- Use summary in active context
- Retrieve full context when needed (from stash)
- **Approach**: This is what we do with stashing + retrieval!

**Selective Preservation**:
- Keep critical parts verbatim
- Summarize less critical parts
- Mark what was summarized for potential retrieval

#### What Must Be Preserved Verbatim

1. **User Requirements**:
   - Specific constraints and preferences
   - Exact user phrasing for alignment
   - Non-negotiable requirements

2. **Active Code**:
   - Code being actively edited
   - Code that's being referenced
   - Configuration values in use

3. **Critical Details**:
   - Exact error messages
   - API endpoints and parameters
   - Version numbers and dependencies

4. **Recent Decisions**:
   - Why certain approaches were chosen
   - Trade-offs discussed
   - Constraints discovered

### 6. Integration with Pruning and Stashing

#### Complementary Strategies

**Three-Tier Context Management**:

1. **Active Context** (Keep in Session):
   - Recent messages, active code
   - Current task state
   - Essential details

2. **Summarized Context** (Compress):
   - Completed topics → summaries
   - Old conversations → bullet points
   - Historical context → high-level overview

3. **Stashed Context** (Remove + Store):
   - Detailed debugging sessions
   - Long code examples
   - Extensive logs
   - Retrieve via semantic search when needed

#### Decision Framework: Summarize vs. Remove vs. Stash

**Summarize When**:
- Topic is complete but context is still relevant
- Information is important but too detailed
- Need high-level overview, details available elsewhere
- Compression ratio: 4:1 to 5:1 acceptable

**Remove/Stash When**:
- Topic is completely done, no longer relevant
- Detailed information can be retrieved later
- Need significant space (>50% reduction)
- Low likelihood of needing details soon

**Keep Verbatim When**:
- Currently active or recently used
- Critical details needed for current task
- User explicitly protected
- Context is small enough to keep

#### Combined Strategy Workflow

```python
def manage_context(context_segments, target_tokens):
    # 1. Protect essential segments
    protected = [s for s in segments if s.protected or s.is_active]
    
    # 2. Categorize remaining segments
    for segment in segments:
        if segment.is_complete_topic():
            if segment.relevance_score > 0.7:
                # Summarize (still relevant)
                summarized = summarize_segment(segment)
                context.add(summarized)
            else:
                # Stash (less relevant, can retrieve)
                stash_segment(segment)
        elif segment.is_redundant():
            # Remove (duplicate information)
            context.remove(segment)
        else:
            # Keep as-is
            context.keep(segment)
    
    # 3. Apply summarization to old context
    if context.tokens > target_tokens:
        old_segments = get_old_segments(context)
        for segment in old_segments:
            summarized = summarize_segment(segment)
            context.replace(segment, summarized)
```

### 7. Limitations and Challenges

#### Technical Limitations

1. **Loss of Nuance**:
   - Summarization inevitably loses details
   - Can't perfectly preserve all information
   - Abstractive summaries may introduce inaccuracies

2. **Context Fragmentation**:
   - Summarizing parts of conversation breaks flow
   - Relationships between messages can be lost
   - User's mental model may not match summary

3. **Compression Quality**:
   - Automatic summarization isn't perfect
   - May lose critical information
   - Requires validation of important summaries

#### User Experience Impact

1. **Re-alignment Overhead**:
   - User must re-explain context after summarization
   - Shared understanding is broken
   - Frustration from lost context

2. **Loss of Trust**:
   - If summaries lose important details, user loses trust
   - Uncertainty about what was preserved
   - Need to verify summaries are accurate

3. **Cognitive Load**:
   - Users must remember what was summarized
   - Need to track what details are still available
   - Complexity of managing summarized vs. full context

## Recommendations

### Primary Recommendation: Summarization as Complementary Tool

**Role**: Summarization should be a **complementary tool**, not the primary strategy.

**Rationale**:
1. **User feedback**: Summarization causes re-alignment overhead
2. **Information loss**: Inevitable loss of nuance and details
3. **Better alternatives**: Stashing + retrieval preserves details

**When to Use Summarization**:
- **Completed topics**: Summarize old, finished topics for high-level context
- **Historical overview**: Create summary of conversation history
- **Initial compression**: When approaching limits, summarize before stashing
- **Selective use**: Only summarize when details aren't needed soon

**Primary Strategy Should Be**:
1. **Pruning**: Remove irrelevant context
2. **Stashing**: Store detailed context for retrieval
3. **Selective Preservation**: Keep active/recent context verbatim

### Implementation Strategy

**Phase 1: Pruning + Stashing** (Primary)
- Focus on removing irrelevant context
- Stash detailed context for semantic retrieval
- No summarization initially

**Phase 2: Selective Summarization** (Complementary)
- Add summarization for completed topics
- Hierarchical summarization for old context
- Always preserve option to retrieve full context

**Phase 3: Advanced Integration** (Optional)
- Smart summarization based on content type
- User-controlled summarization preferences
- Summarization quality validation

### Selective Summarization Approach

**Recommended Pattern**:

1. **Keep Recent**: Last N messages verbatim (e.g., last 10)
2. **Summarize Intermediate**: Next M messages summarized (e.g., next 20)
3. **Stash Detailed**: Detailed context stashed for retrieval
4. **High-Level Summary**: Very old context as bullet points

**Example Structure**:
```
Active Context (2000 tokens):
├─ Recent Messages (500 tokens) - Full detail
├─ Intermediate Summary (300 tokens) - Paragraph summaries
├─ Historical Overview (200 tokens) - Bullet points
└─ Stashed Context (available via retrieval) - Full detail preserved
```

### Content-Type Specific Handling

**Code**:
- **Don't summarize active code** - Keep verbatim
- **Summarize old code examples** - Show structure, summarize implementation
- **Stash detailed code** - For retrieval when needed

**Conversation**:
- **Keep recent conversation** - Full detail for alignment
- **Summarize completed topics** - Extract decisions, preserve rationale
- **Stash detailed discussions** - For deep-dive retrieval

**Logs/Errors**:
- **Keep recent errors** - Full detail for debugging
- **Summarize old errors** - Extract patterns, remove redundancy
- **Stash detailed logs** - For historical analysis

## References

### Summarization Research

1. **Neural Extractive Text Summarization with Syntactic Compression**
   - URL: https://aclanthology.org/D19-1324/
   - Details: Joint sentence extraction and compression model

2. **RECOMP: Improving Retrieval-Augmented LMs with Compression**
   - URL: https://arxiv.org/abs/2310.04408
   - Details: Compresses retrieved documents into summaries before integration

3. **KV-Distill: Transformer Compression Framework**
   - URL: https://arxiv.org/abs/2503.10337
   - Details: Distills long context key-value caches into shorter representations

4. **DAST: Dynamic Allocation of Soft Tokens**
   - URL: https://arxiv.org/abs/2502.11493
   - Details: Context-aware compression using LLM's understanding of relevance

5. **SoftPromptComp: Natural Language Summarization with Soft Prompts**
   - URL: https://arxiv.org/abs/2404.04997
   - Details: Combines summarization with dynamically generated soft prompts

### Compression Techniques

6. **Semantic Compression**
   - URL: https://en.wikipedia.org/wiki/Semantic_compression
   - Details: Reducing language heterogeneity using hypernyms

7. **Context Compression Patterns (CCP)**
   - URL: https://agentic-design.ai/patterns/context-management/context-compress-patterns
   - Details: Semantic compression for maximizing information density

8. **Context Compression Cost Savings**
   - URL: https://thread-transfer.com/blog/2025-03-07-context-compression-cost-savings/
   - Details: Reports 60-80% cost savings from context compression

### Tools and Libraries

9. **context-compressor Python Library**
   - URL: https://pypi.org/project/context-compressor/
   - Details: Provides extractive and abstractive compression strategies

10. **Text Summarization Techniques**
    - URL: https://analyticsvidhya.com/blog/2021/11/a-beginners-guide-to-understanding-text-summarization-with-nlp/
    - Details: Overview of extractive and abstractive summarization

## Notes

* **User feedback validated**: Summarization causes re-alignment overhead due to loss of nuance
* **Complementary role**: Summarization works best as a supporting tool, not primary strategy
* **Selective approach**: Summarize completed topics, keep active context verbatim
* **Integration**: Combine with pruning (remove) and stashing (retrieve) for comprehensive strategy
* **Content-aware**: Different strategies for code vs. conversation vs. logs
* **Reversibility**: Stashing provides "reversible compression" - full context available when needed

