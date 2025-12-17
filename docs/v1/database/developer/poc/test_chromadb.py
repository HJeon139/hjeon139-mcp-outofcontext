#!/usr/bin/env python3
"""
POC: ChromaDB for Semantic Search
Tests ChromaDB performance and API ergonomics
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import statistics

# Check if dependencies available
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False
    print("⚠️  Dependencies not installed. Run:")
    print("    pip install chromadb sentence-transformers")


def load_test_queries(limit: int = 10) -> List[Dict[str, Any]]:
    """Load first N queries from evaluation test set."""
    testset_path = Path(__file__).parent.parent.parent / "scientist" / "evaluation-testset.json"
    with open(testset_path) as f:
        data = json.load(f)
    return data["queries"][:limit]


def benchmark_chromadb():
    """Benchmark ChromaDB performance."""
    if not DEPS_AVAILABLE:
        return
    
    print("=" * 60)
    print("ChromaDB POC Benchmark")
    print("=" * 60)
    
    # Initialize embedding model
    print("\n1. Loading embedding model...")
    start = time.time()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    load_time = time.time() - start
    print(f"   Model loaded in {load_time:.2f}s")
    
    # Initialize ChromaDB (ephemeral, in-memory)
    print("\n2. Initializing ChromaDB...")
    start = time.time()
    client = chromadb.Client()
    collection = client.create_collection(
        name="contexts",
        metadata={"hnsw:space": "cosine"}
    )
    init_time = time.time() - start
    print(f"   ChromaDB initialized in {init_time:.3f}s")
    
    # Create mock context data (simulate 2K contexts)
    print("\n3. Inserting mock contexts (2000 vectors)...")
    start = time.time()
    
    # Generate sample context texts
    mock_contexts = []
    for i in range(2000):
        mock_contexts.append(f"Context {i}: Sample text about project management, development, and testing.")
    
    # Generate embeddings in batches
    batch_size = 100
    for i in range(0, len(mock_contexts), batch_size):
        batch = mock_contexts[i:i+batch_size]
        embeddings = model.encode(batch, show_progress_bar=False)
        ids = [f"ctx_{j}" for j in range(i, i+len(batch))]
        
        collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            metadatas=[{"mtime": time.time()} for _ in batch],
            documents=batch
        )
    
    insert_time = time.time() - start
    print(f"   Inserted {len(mock_contexts)} contexts in {insert_time:.2f}s")
    print(f"   Avg: {insert_time/len(mock_contexts)*1000:.1f}ms per context")
    
    # Benchmark query performance
    print("\n4. Benchmarking query performance...")
    test_queries = load_test_queries(limit=10)
    
    query_latencies = []
    embed_latencies = []
    search_latencies = []
    
    for q in test_queries:
        query_text = q["query"]
        
        # Measure embedding time
        start = time.time()
        query_embedding = model.encode([query_text], show_progress_bar=False)[0]
        embed_time = time.time() - start
        embed_latencies.append(embed_time * 1000)  # ms
        
        # Measure search time
        start = time.time()
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=5
        )
        search_time = time.time() - start
        search_latencies.append(search_time * 1000)  # ms
        
        total_time = embed_time + search_time
        query_latencies.append(total_time * 1000)  # ms
    
    # Calculate statistics
    def percentile(data, p):
        sorted_data = sorted(data)
        index = int(len(sorted_data) * p / 100)
        return sorted_data[min(index, len(sorted_data)-1)]
    
    print(f"\n   Results (10 queries, 2000 vectors):")
    print(f"   ----------------------------------")
    print(f"   Total Latency:")
    print(f"     p50: {percentile(query_latencies, 50):.1f}ms")
    print(f"     p95: {percentile(query_latencies, 95):.1f}ms")
    print(f"     p99: {percentile(query_latencies, 99):.1f}ms")
    print(f"     avg: {statistics.mean(query_latencies):.1f}ms")
    print(f"\n   Embedding Time:")
    print(f"     p50: {percentile(embed_latencies, 50):.1f}ms")
    print(f"     p95: {percentile(embed_latencies, 95):.1f}ms")
    print(f"     avg: {statistics.mean(embed_latencies):.1f}ms")
    print(f"\n   Vector Search Time:")
    print(f"     p50: {percentile(search_latencies, 50):.1f}ms")
    print(f"     p95: {percentile(search_latencies, 95):.1f}ms")
    print(f"     avg: {statistics.mean(search_latencies):.1f}ms")
    
    # Evaluation
    print(f"\n5. Evaluation:")
    total_p95 = percentile(query_latencies, 95)
    if total_p95 < 100:
        print(f"   ✅ PASS: p95 latency ({total_p95:.1f}ms) < 100ms target")
    else:
        print(f"   ❌ FAIL: p95 latency ({total_p95:.1f}ms) > 100ms target")
    
    search_p95 = percentile(search_latencies, 95)
    if search_p95 < 50:
        print(f"   ✅ PASS: Search p95 ({search_p95:.1f}ms) < 50ms target")
    else:
        print(f"   ⚠️  WARNING: Search p95 ({search_p95:.1f}ms) > 50ms target")
    
    # API ergonomics notes
    print(f"\n6. API Ergonomics:")
    print(f"   + Simple, intuitive API")
    print(f"   + Good documentation")
    print(f"   + Built-in persistence support")
    print(f"   + Mature ecosystem (most popular for RAG)")
    print(f"   - Requires chromadb dependency (~50MB)")
    
    print("\n" + "=" * 60)
    
    return {
        "total_p95": total_p95,
        "search_p95": search_p95,
        "embed_p95": percentile(embed_latencies, 95),
        "passes": total_p95 < 100 and search_p95 < 50
    }


if __name__ == "__main__":
    if DEPS_AVAILABLE:
        results = benchmark_chromadb()
        print(f"\nChromaDB POC Results: {'✅ PASS' if results['passes'] else '❌ NEEDS OPTIMIZATION'}")
    else:
        print("\nInstall dependencies to run benchmark:")
        print("  pip install chromadb sentence-transformers")

