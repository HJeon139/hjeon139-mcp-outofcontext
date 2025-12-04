# Design: Leveraging Existing Tooling and Libraries

## 1. Scope & Goals

### What This Design Covers

This design document catalogs existing tooling, libraries, and patterns we can leverage from established solutions (LangChain, research projects, etc.) to accelerate development and avoid reinventing the wheel. It covers what to use, how to integrate, and what we still need to build ourselves.

### Non-Goals

- Not designing our core MCP server logic (covered in other design docs)
- Not replacing existing tools (we leverage them, not replace)
- Not framework-specific implementations (we use libraries, not frameworks)

## 2. Leveraging Strategy

### Principle: Build on Proven Components

**Strategy**: 
- Leverage mature, battle-tested libraries for foundational components
- Focus our development on unique value (MCP integration, platform adapters, agent-driven control)
- Use existing tools as building blocks, not as complete solutions

**What We Build**:
- MCP server implementation
- Platform integration adapters
- Agent-driven context management orchestration
- Context analysis and decision logic

**What We Leverage**:
- Embedding generation (sentence-transformers)
- Vector storage (FAISS, Qdrant, Chroma)
- Token counting (tiktoken)
- Memory patterns (from LangChain)
- Compression utilities (if needed)

## 3. Core Libraries to Leverage

### 3.1 Embedding Generation

#### Sentence Transformers

**Library**: `sentence-transformers`

**What It Provides**:
- Pre-trained embedding models
- Easy-to-use API for text → vector conversion
- Model loading and management
- Batch processing support

**Usage**:
```python
from sentence_transformers import SentenceTransformer

class EmbeddingGenerator:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Leverage sentence-transformers for embeddings
        self.model = SentenceTransformer(model_name)
    
    def generate_embedding(self, text: str) -> np.ndarray:
        return self.model.encode(text, normalize_embeddings=True)
    
    def batch_generate(self, texts: List[str]) -> List[np.ndarray]:
        return self.model.encode(texts, batch_size=32)
```

**Why Leverage**:
- Mature, well-tested library
- Multiple model options
- Optimized for performance
- Active maintenance

**Dependencies to Add**:
```toml
[project.dependencies]
sentence-transformers = ">=2.2.0"
```

#### Alternative: OpenAI Embeddings

**Library**: `openai` (optional, for cloud-based embeddings)

**When to Use**:
- Higher quality needed
- Budget allows API costs
- Production deployment

**Usage**:
```python
from openai import OpenAI

class OpenAIEmbeddingGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def generate_embedding(self, text: str) -> np.ndarray:
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return np.array(response.data[0].embedding)
```

**Why Leverage**:
- Best quality embeddings
- Managed service (no model loading)
- Consistent API

**Dependencies to Add**:
```toml
[project.optional-dependencies]
openai = ["openai>=1.0.0"]
```

### 3.2 Vector Database Storage

#### FAISS (Primary Choice)

**Library**: `faiss-cpu` or `faiss-gpu`

**What It Provides**:
- Efficient similarity search
- Index building and management
- Fast nearest-neighbor search
- Multiple index types (Flat, IVF, etc.)

**Usage**:
```python
import faiss
import numpy as np

class FAISSVectorStore:
    def __init__(self, dimension: int = 384):
        # Leverage FAISS for vector storage
        self.index = faiss.IndexFlatIP(dimension)
        self.dimension = dimension
    
    def add(self, embeddings: np.ndarray):
        """Add embeddings to index"""
        self.index.add(embeddings)
    
    def search(self, query: np.ndarray, k: int = 10):
        """Search for k nearest neighbors"""
        distances, indices = self.index.search(query, k)
        return distances, indices
```

**Why Leverage**:
- Battle-tested (used by Facebook/Meta at scale)
- Very fast similarity search
- Lightweight, no external dependencies
- Good documentation

**Dependencies to Add**:
```toml
[project.dependencies]
faiss-cpu = ">=1.7.4"  # or faiss-gpu for GPU support
```

#### Alternative: Chroma (For Development)

**Library**: `chromadb`

**What It Provides**:
- Simple embedded vector database
- Metadata filtering
- Easy setup and usage
- Good for prototyping

**Usage**:
```python
import chromadb

class ChromaVectorStore:
    def __init__(self, persist_directory: Path):
        # Leverage Chroma for simple vector storage
        self.client = chromadb.PersistentClient(path=str(persist_directory))
        self.collection = self.client.get_or_create_collection("context_segments")
    
    def add(self, ids: List[str], embeddings: List[np.ndarray], metadata: List[Dict]):
        self.collection.add(
            ids=ids,
            embeddings=[e.tolist() for e in embeddings],
            metadatas=metadata
        )
    
    def search(self, query_embedding: np.ndarray, n_results: int = 10):
        return self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )
```

**Why Leverage**:
- Simple API
- Built-in metadata support
- Good for development/testing
- Easy to use

**Dependencies to Add**:
```toml
[project.optional-dependencies]
chroma = ["chromadb>=0.4.0"]
```

#### Alternative: Qdrant (For Production)

**Library**: `qdrant-client`

**What It Provides**:
- Full-featured vector database
- REST API support
- Advanced filtering
- Production-ready

**Usage**:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

class QdrantVectorStore:
    def __init__(self, url: str, collection_name: str = "context_segments"):
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        # Create collection if needed
        # ... setup code
    
    def add(self, points):
        self.client.upsert(collection_name=self.collection_name, points=points)
    
    def search(self, query_vector, limit=10, filter=None):
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter
        )
```

**Why Leverage**:
- Production-grade features
- Metadata filtering built-in
- Scalable architecture
- REST API for distributed systems

**Dependencies to Add**:
```toml
[project.optional-dependencies]
qdrant = ["qdrant-client>=1.7.0"]
```

### 3.3 Token Counting

#### tiktoken

**Library**: `tiktoken`

**What It Provides**:
- Fast token counting for OpenAI models
- Multiple encoding support (cl100k_base, etc.)
- Accurate token estimates

**Usage**:
```python
import tiktoken

class TokenCounter:
    def __init__(self, model: str = "gpt-4"):
        # Leverage tiktoken for token counting
        self.encoding = tiktoken.encoding_for_model(model)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    def count_tokens_batch(self, texts: List[str]) -> List[int]:
        """Count tokens for multiple texts"""
        return [len(self.encoding.encode(text)) for text in texts]
```

**Why Leverage**:
- Fast and accurate
- Official OpenAI tokenizer
- Multiple model support
- Well-maintained

**Dependencies to Add**:
```toml
[project.dependencies]
tiktoken = ">=0.5.0"
```

#### Alternative: Transformers Tokenizer

**Library**: `transformers`

**What It Provides**:
- Token counting for various models
- HuggingFace model support
- More flexible than tiktoken

**Usage**:
```python
from transformers import AutoTokenizer

class TransformersTokenCounter:
    def __init__(self, model_name: str = "gpt2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))
```

**Why Leverage**:
- Supports many model families
- Useful for non-OpenAI models
- More flexible

**Dependencies to Add**:
```toml
[project.optional-dependencies]
transformers = ["transformers>=4.30.0"]
```

### 3.4 Memory Patterns from LangChain

#### Inspiration: LangChain Memory Components

**Library**: `langchain` (for patterns, not full integration)

**What We Can Learn**:
- Memory storage patterns
- Context segmentation approaches
- Buffer management strategies
- Summary generation patterns

**Patterns to Leverage**:

1. **ConversationBufferWindowMemory Pattern**:
   - Keep sliding window of recent messages
   - Discard oldest messages when limit reached
   - Useful for maintaining recent context

2. **ConversationSummaryMemory Pattern**:
   - Summarize old messages
   - Keep summaries + recent messages
   - Trade-off between detail and space

3. **VectorStore-backed Memory Pattern**:
   - Store messages in vector DB
   - Retrieve by semantic similarity
   - RAG-like retrieval

**Usage (Inspiration Only)**:
```python
# We don't use LangChain directly, but learn from patterns

class SlidingWindowBuffer:
    """Inspired by ConversationBufferWindowMemory"""
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.messages = []
    
    def add_message(self, message: str):
        self.messages.append(message)
        if len(self.messages) > self.window_size:
            self.messages.pop(0)  # Remove oldest
    
    def get_messages(self) -> List[str]:
        return self.messages
```

**Why Leverage Patterns**:
- Proven memory management patterns
- Well-thought-out trade-offs
- Battle-tested approaches

**Dependencies**: None (we learn patterns, not import library)

### 3.5 Context Compression Libraries

#### context-compressor (Optional)

**Library**: `context-compressor`

**What It Provides**:
- Multiple compression strategies
- Extractive and abstractive compression
- Quality evaluation

**Usage** (if we decide to use compression libraries):
```python
from context_compressor import Compressor

class CompressionService:
    def __init__(self, strategy: str = "extractive"):
        # Leverage context-compressor if needed
        self.compressor = Compressor(strategy=strategy)
    
    def compress(self, text: str, target_ratio: float = 0.6) -> str:
        return self.compressor.compress(text, compression_ratio=target_ratio)
```

**Why Consider**:
- Ready-made compression utilities
- Multiple strategies available
- Could save development time

**Note**: We may build our own LLM-driven compression instead (per design doc)

**Dependencies to Add** (if used):
```toml
[project.optional-dependencies]
compression = ["context-compressor>=0.1.0"]
```

### 3.6 MCP Protocol Implementation

#### MCP Python SDK

**Library**: `mcp` (official MCP Python SDK)

**What It Provides**:
- MCP protocol implementation
- Server and client utilities
- Tool definition helpers
- Protocol compliance

**Usage**:
```python
from mcp.server import Server
from mcp.types import Tool, TextContent

# Leverage MCP SDK for protocol implementation
server = Server("out-of-context")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="check_context_usage",
            description="Check current context usage statistics",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "check_context_usage":
        # Our implementation
        usage = get_context_usage()
        return [TextContent(type="text", text=json.dumps(usage))]
```

**Why Leverage**:
- Official SDK ensures protocol compliance
- Handles protocol details
- Well-maintained
- Community support

**Dependencies to Add**:
```toml
[project.dependencies]
mcp = ">=1.0.0"  # Check latest version
```

### 3.7 Data Validation

#### Pydantic

**Library**: `pydantic`

**What It Provides**:
- Data validation and serialization
- Type hints enforcement
- Schema generation (for MCP tools)
- Easy model definition

**Usage**:
```python
from pydantic import BaseModel, Field

# Leverage Pydantic for data models
class ContextSegment(BaseModel):
    segment_id: str
    text: str
    type: SegmentType
    tokens: int = Field(ge=0)
    timestamp: datetime
    metadata: dict = Field(default_factory=dict)

class CompressionResult(BaseModel):
    segment_id: str
    original_tokens: int
    compressed_tokens: int
    tokens_saved: int
    compression_ratio: float = Field(ge=0.0, le=1.0)
```

**Why Leverage**:
- Industry standard for data validation
- Excellent type hints support
- Automatic schema generation
- Well-documented

**Dependencies to Add**:
```toml
[project.dependencies]
pydantic = ">=2.0.0"
```

### 3.8 Storage and Persistence

#### SQLite (Built-in, via sqlite3)

**Library**: `sqlite3` (Python standard library)

**What It Provides**:
- Lightweight embedded database
- Metadata storage
- Persistent storage
- No external dependencies

**Usage**:
```python
import sqlite3
from pathlib import Path

class MetadataStore:
    def __init__(self, db_path: Path):
        # Leverage SQLite for metadata storage
        self.db = sqlite3.connect(db_path)
        self._init_schema()
    
    def _init_schema(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS segments (
                segment_id TEXT PRIMARY KEY,
                session_id TEXT,
                text TEXT,
                tokens INTEGER,
                timestamp TEXT
            )
        """)
```

**Why Leverage**:
- No external dependencies
- Lightweight and fast
- Perfect for metadata storage
- Persistent storage

**Dependencies**: None (built-in)

#### Alternative: TinyDB

**Library**: `tinydb`

**What It Provides**:
- Document-oriented database
- Simple JSON-based storage
- Easy querying

**Usage**:
```python
from tinydb import TinyDB, Query

class TinyDBMetadataStore:
    def __init__(self, db_path: Path):
        # Leverage TinyDB for simple document storage
        self.db = TinyDB(db_path)
        self.segments = self.db.table('segments')
    
    def store_segment(self, segment: ContextSegment):
        self.segments.insert(segment.model_dump())
```

**Why Consider**:
- Simpler than SQLite for document storage
- Easy querying
- Good for prototyping

**Dependencies to Add** (if used):
```toml
[project.optional-dependencies]
tinydb = ["tinydb>=4.8.0"]
```

## 4. What We Build Ourselves

### 4.1 Core MCP Server

**Why We Build**:
- MCP protocol integration specific to context management
- Our unique tool definitions and orchestration
- Agent-driven control logic

**What We Build**:
- MCP server implementation using MCP SDK
- Tool definitions for context management
- Tool orchestration and workflow
- Agent interaction patterns

### 4.2 Platform Integration Layer

**Why We Build**:
- Unique to our approach (platform-level integration)
- Platform-specific adapters (Cursor, Claude Desktop, etc.)
- Context reading/modification at platform level

**What We Build**:
- Platform adapter interfaces
- Cursor/VS Code adapter
- Claude Desktop adapter
- File system adapter (fallback)
- Platform detection logic

### 4.3 Context Analysis Engine

**Why We Build**:
- Our unique multi-signal relevance scoring
- Context segment analysis
- Pruning decision logic
- Agent-driven compression orchestration

**What We Build**:
- Relevance scoring algorithms
- Context segment analysis
- Pruning strategy selection
- Compression orchestration (using LLM)
- Multi-signal combination logic

### 4.4 Storage Orchestration

**Why We Build**:
- Our unique storage architecture
- Integration of vector DB + metadata store
- Context lifecycle management
- Cross-storage coordination

**What We Build**:
- Vector store wrapper (using FAISS/Chroma/Qdrant)
- Metadata store wrapper (using SQLite/TinyDB)
- Storage synchronization
- Context retrieval orchestration

## 5. Integration Patterns

### 5.1 Embedding + Vector Store Pattern

**Leveraging**:
- `sentence-transformers` for embeddings
- `faiss-cpu` for vector storage

**Integration**:
```python
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class ContextVectorStore:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        # Leverage sentence-transformers
        self.embedder = SentenceTransformer(embedding_model)
        self.dimension = self.embedder.get_sentence_embedding_dimension()
        
        # Leverage FAISS
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata_store = {}  # Our implementation
    
    def add_segment(self, segment: ContextSegment):
        # Use sentence-transformers for embedding
        embedding = self.embedder.encode(segment.text, normalize_embeddings=True)
        
        # Use FAISS for storage
        self.index.add(embedding.reshape(1, -1))
        
        # Our metadata storage
        self.metadata_store[segment.segment_id] = segment
    
    def search(self, query: str, k: int = 10):
        # Use sentence-transformers for query embedding
        query_embedding = self.embedder.encode(query, normalize_embeddings=True)
        
        # Use FAISS for search
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1), k
        )
        
        # Our result formatting
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0:
                segment_id = list(self.metadata_store.keys())[idx]
                results.append({
                    "segment": self.metadata_store[segment_id],
                    "similarity": float(dist)
                })
        return results
```

### 5.2 Token Counting Pattern

**Leveraging**:
- `tiktoken` for token counting

**Integration**:
```python
import tiktoken

class ContextAnalyzer:
    def __init__(self, model: str = "gpt-4"):
        # Leverage tiktoken
        self.tokenizer = tiktoken.encoding_for_model(model)
    
    def analyze_context(self, segments: List[ContextSegment]) -> ContextAnalysis:
        total_tokens = 0
        segment_counts = []
        
        for segment in segments:
            # Use tiktoken for counting
            count = len(self.tokenizer.encode(segment.text))
            total_tokens += count
            segment_counts.append({
                "segment_id": segment.segment_id,
                "tokens": count
            })
        
        return ContextAnalysis(
            total_tokens=total_tokens,
            segment_breakdown=segment_counts,
            estimated_percent=total_tokens / MAX_TOKENS * 100
        )
```

### 5.3 Memory Pattern Inspiration

**Leveraging**:
- LangChain memory patterns (concepts, not library)

**Integration**:
```python
# Inspired by LangChain's ConversationBufferWindowMemory
class SlidingWindowContext:
    """Pattern inspired by LangChain, but our implementation"""
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.segments = []
    
    def add_segment(self, segment: ContextSegment):
        self.segments.append(segment)
        if len(self.segments) > self.window_size:
            # Remove oldest (or stash it)
            oldest = self.segments.pop(0)
            self._handle_overflow(oldest)
    
    def get_context(self) -> List[ContextSegment]:
        return self.segments
```

### 5.4 Compression Pattern (Using LLM)

**Leveraging**:
- OpenAI API or Anthropic API for LLM-driven compression

**Integration**:
```python
from openai import OpenAI

class LLMCompressor:
    def __init__(self, api_key: str):
        # Leverage OpenAI API for compression
        self.client = OpenAI(api_key=api_key)
    
    def compress_segment(
        self, 
        segment: ContextSegment,
        preserve_metadata: List[str]
    ) -> str:
        # Build compression prompt (our logic)
        prompt = self._build_compression_prompt(segment, preserve_metadata)
        
        # Use OpenAI API for compression (leverage library)
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return response.choices[0].message.content
```

## 6. Dependency Strategy

### Core Dependencies (Required)

```toml
[project.dependencies]
# MCP Protocol
mcp = ">=1.0.0"

# Data Validation
pydantic = ">=2.0.0"

# Embeddings
sentence-transformers = ">=2.2.0"

# Vector Storage
faiss-cpu = ">=1.7.4"

# Token Counting
tiktoken = ">=0.5.0"

# Standard library (no dependency needed)
# sqlite3 - built-in
```

### Optional Dependencies (Features)

```toml
[project.optional-dependencies]
# Alternative embeddings
openai = ["openai>=1.0.0"]

# Alternative vector stores
chroma = ["chromadb>=0.4.0"]
qdrant = ["qdrant-client>=1.7.0"]

# Alternative tokenizers
transformers = ["transformers>=4.30.0"]

# Compression utilities (if we decide to use)
compression = ["context-compressor>=0.1.0"]

# Alternative storage
tinydb = ["tinydb>=4.8.0"]
```

### Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
]
```

## 7. Architecture Integration

### Layered Architecture with Leveraged Components

```
┌─────────────────────────────────────────────────────────────┐
│                  Our MCP Server (We Build)                   │
│  - Tool definitions and orchestration                       │
│  - Agent interaction patterns                               │
│  - Platform integration                                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Uses
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              Context Analysis Engine (We Build)              │
│  - Relevance scoring                                        │
│  - Decision logic                                           │
│  - Multi-signal combination                                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Uses
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              Leveraged Libraries Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │ sentence-       │  │ tiktoken        │                 │
│  │ transformers    │  │ (token counting)│                 │
│  │ (embeddings)    │  └─────────────────┘                 │
│  └─────────────────┘                                       │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │ FAISS/Chroma/   │  │ SQLite          │                 │
│  │ Qdrant          │  │ (metadata)      │                 │
│  │ (vector store)  │  └─────────────────┘                 │
│  └─────────────────┘                                       │
│  ┌─────────────────┐                                       │
│  │ MCP SDK         │                                       │
│  │ (protocol)      │                                       │
│  └─────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

## 8. Implementation Examples

### Example: Complete Context Store

```python
from sentence_transformers import SentenceTransformer
import faiss
import sqlite3
import tiktoken
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np

class ContextStore:
    """Leverages multiple libraries, builds orchestration layer"""
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        db_path: Path = Path("context_store.db"),
        token_model: str = "gpt-4"
    ):
        # Leverage sentence-transformers
        self.embedder = SentenceTransformer(embedding_model)
        self.dimension = self.embedder.get_sentence_embedding_dimension()
        
        # Leverage FAISS
        self.vector_index = faiss.IndexFlatIP(self.dimension)
        self.id_to_idx = {}  # Our mapping
        
        # Leverage SQLite
        self.db = sqlite3.connect(db_path)
        self._init_db_schema()
        
        # Leverage tiktoken
        self.tokenizer = tiktoken.encoding_for_model(token_model)
    
    def _init_db_schema(self):
        """Initialize SQLite schema"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS segments (
                segment_id TEXT PRIMARY KEY,
                session_id TEXT,
                text TEXT,
                tokens INTEGER,
                type TEXT,
                timestamp TEXT,
                metadata TEXT
            )
        """)
    
    def add_segment(self, segment: ContextSegment):
        """Add segment using leveraged libraries"""
        # Generate embedding (sentence-transformers)
        embedding = self.embedder.encode(segment.text, normalize_embeddings=True)
        
        # Count tokens (tiktoken)
        token_count = len(self.tokenizer.encode(segment.text))
        segment.tokens = token_count
        
        # Store in vector index (FAISS)
        idx = self.vector_index.ntotal
        self.vector_index.add(embedding.reshape(1, -1))
        self.id_to_idx[segment.segment_id] = idx
        
        # Store metadata (SQLite)
        self.db.execute("""
            INSERT INTO segments 
            (segment_id, session_id, text, tokens, type, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            segment.segment_id,
            segment.session_id,
            segment.text,
            segment.tokens,
            segment.type.value,
            segment.timestamp.isoformat(),
            json.dumps(segment.metadata)
        ))
        self.db.commit()
    
    def search_similar(self, query: str, k: int = 10) -> List[Dict]:
        """Search using leveraged libraries"""
        # Generate query embedding (sentence-transformers)
        query_embedding = self.embedder.encode(query, normalize_embeddings=True)
        
        # Search vector index (FAISS)
        distances, indices = self.vector_index.search(
            query_embedding.reshape(1, -1), k
        )
        
        # Retrieve metadata (SQLite)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0:
                segment_id = list(self.id_to_idx.keys())[
                    list(self.id_to_idx.values()).index(idx)
                ]
                
                cursor = self.db.execute(
                    "SELECT * FROM segments WHERE segment_id = ?",
                    (segment_id,)
                )
                row = cursor.fetchone()
                
                results.append({
                    "segment_id": row[0],
                    "similarity": float(dist),
                    "segment": self._row_to_segment(row)
                })
        
        return results
```

### Example: Token Counting Integration

```python
import tiktoken
from typing import List

class ContextUsageMonitor:
    """Leverages tiktoken for token counting"""
    
    def __init__(self, model: str = "gpt-4"):
        # Leverage tiktoken
        self.tokenizer = tiktoken.encoding_for_model(model)
        self.max_tokens = self._get_max_tokens(model)
    
    def get_usage_stats(self, segments: List[ContextSegment]) -> UsageStats:
        """Calculate usage statistics"""
        total_tokens = 0
        segment_counts = []
        
        for segment in segments:
            # Use tiktoken for accurate counting
            count = len(self.tokenizer.encode(segment.text))
            total_tokens += count
            segment_counts.append({
                "id": segment.segment_id,
                "tokens": count
            })
        
        return UsageStats(
            total_tokens=total_tokens,
            max_tokens=self.max_tokens,
            usage_percent=(total_tokens / self.max_tokens) * 100,
            remaining_tokens=self.max_tokens - total_tokens,
            segment_breakdown=segment_counts
        )
    
    def estimate_tokens_to_remove(
        self, 
        target_tokens: int, 
        current_tokens: int
    ) -> int:
        """Estimate tokens needed to remove"""
        return max(0, current_tokens - target_tokens)
```

## 9. What NOT to Leverage

### Frameworks We Avoid

**LangChain Framework**:
- **Why**: Framework-bound, we're building MCP server not LangChain app
- **Instead**: Learn patterns, use libraries directly

**AutoGPT Framework**:
- **Why**: Different architecture, not compatible with our approach
- **Instead**: Learn context handling patterns if useful

**Full Agent Frameworks**:
- **Why**: We're building a tool/server, not an agent framework
- **Instead**: Use libraries, not frameworks

### Libraries We Don't Need

**Heavy ML Frameworks** (unless needed):
- PyTorch/TensorFlow for embeddings (sentence-transformers handles this)
- Only include if we need custom model training

**Full Database Systems**:
- PostgreSQL, MySQL (SQLite is sufficient for metadata)
- Only if we need distributed storage

## 10. Testing Strategy for Leveraged Libraries

### Mocking Strategy

**When to Mock**:
- External API calls (OpenAI, embeddings)
- File system operations
- Network requests

**When NOT to Mock**:
- Library behavior we rely on (test with real libraries)
- Vector search accuracy (test with real FAISS)
- Token counting accuracy (test with real tiktoken)

### Integration Tests

```python
import pytest
from sentence_transformers import SentenceTransformer
import faiss

@pytest.mark.integration
def test_embedding_generation():
    """Test with real sentence-transformers"""
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    embedding = embedder.encode("test text")
    assert len(embedding) == 384  # Dimension of model

@pytest.mark.integration
def test_vector_search():
    """Test with real FAISS"""
    index = faiss.IndexFlatIP(384)
    vectors = np.random.rand(10, 384).astype('float32')
    index.add(vectors)
    
    query = np.random.rand(1, 384).astype('float32')
    distances, indices = index.search(query, k=3)
    
    assert len(indices[0]) == 3
```

## 11. Decisions Summary

- **D1: Use sentence-transformers for Embeddings**
  - **Rationale**: Mature, fast, multiple model options

- **D2: Use FAISS as Primary Vector Store**
  - **Rationale**: Fast, battle-tested, lightweight

- **D3: Use tiktoken for Token Counting**
  - **Rationale**: Accurate, fast, official OpenAI tokenizer

- **D4: Use SQLite for Metadata Storage**
  - **Rationale**: Built-in, lightweight, sufficient for our needs

- **D5: Use MCP SDK for Protocol Implementation**
  - **Rationale**: Official SDK, protocol compliance, maintained

- **D6: Learn from LangChain Patterns, Don't Import Framework**
  - **Rationale**: We need libraries, not framework-bound code

- **D7: Build Our Own Orchestration Layer**
  - **Rationale**: Unique value is in integration and agent-driven logic

## 12. Implementation Phases

### Phase 1: Core Libraries (MVP)
- sentence-transformers
- FAISS
- tiktoken
- MCP SDK
- Pydantic
- SQLite (built-in)

### Phase 2: Alternative Options
- Chroma for development
- OpenAI embeddings (optional)
- Qdrant for production

### Phase 3: Advanced Features
- Compression utilities (if needed)
- Additional tokenizers (if needed)

## 13. References

### Library Documentation

1. **Sentence Transformers**
   - URL: https://www.sbert.net/
   - GitHub: https://github.com/UKPLab/sentence-transformers

2. **FAISS**
   - GitHub: https://github.com/facebookresearch/faiss
   - Documentation: https://github.com/facebookresearch/faiss/wiki

3. **tiktoken**
   - GitHub: https://github.com/openai/tiktoken
   - Documentation: https://github.com/openai/tiktoken

4. **MCP Python SDK**
   - GitHub: https://github.com/modelcontextprotocol/python-sdk
   - Documentation: https://modelcontextprotocol.io/

5. **Pydantic**
   - URL: https://docs.pydantic.dev/
   - GitHub: https://github.com/pydantic/pydantic

6. **Chroma**
   - URL: https://www.trychroma.com/
   - GitHub: https://github.com/chroma-core/chroma

7. **Qdrant**
   - URL: https://qdrant.tech/
   - GitHub: https://github.com/qdrant/qdrant

8. **LangChain Memory** (for pattern reference)
   - URL: https://python.langchain.com/docs/modules/memory/
   - Note: Learn patterns, don't import framework

## Notes

* **Focus on integration**: Our value is in orchestrating existing tools, not building them from scratch
* **Keep dependencies minimal**: Only add what we actually use
* **Use optional dependencies**: Allow users to choose vector stores, embedding providers
* **Test with real libraries**: Ensure integration works with actual library behavior
* **Learn patterns, don't import frameworks**: Use libraries directly, learn from framework patterns


