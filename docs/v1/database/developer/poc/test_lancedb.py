#!/usr/bin/env python3
"""
POC: LanceDB for Semantic Search
Tests LanceDB performance and API ergonomics
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import statistics
import tempfile
import shutil

# Check if dependencies available
try:
    import lancedb
    from sentence_transformers import SentenceTransformer
    import numpy as np
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False
    print("⚠️  Dependencies not installed. Run:")
    print("    pip install lancedb sentence-transformers")


def load_test_queries(limit: int = 10) -> List[Dict[str, Any]]:
    """Load first N queries from evaluation test set."""
    testset_path = Path(__file__).parent.parent.parent / "scientist" / "evaluation-testset.json"
    with open(testset_path) as f:
        data = json.load(f)
    return data["queries"][:limit]


def benchmark_lancedb():
    """Benchmark LanceDB performance."""
    if not DEPS_AVAILABLE:
        return
    
    print("=" * 60)
    print("LanceDB POC Benchmark")
    print("=" * 60)
    
    # Initialize embedding model
    print("\n1. Loading embedding model...")
    start = time.time()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    load_time = time.time() - start
    print(f"   Model loaded in {load_time:.2f}s")
    
    # Initialize LanceDB (temp directory)
    print("\n2. Initializing LanceDB...")
    temp_dir = tempfile.mkdtemp()
    try:
        start = time.time()
        db = lancedb.connect(temp_dir)
        init_time = time.time() - start
        print(f"   LanceDB initialized in {init_time:.3f}s")
        print(f"   Using temp directory: {temp_dir}")
        
        # Create mock context data (simulate 2K contexts)
        print("\n3. Inserting mock contexts (2000 vectors)...")
        start = time.time()
        
        # Generate sample context texts
        mock_contexts = []
        for i in range(2000):
            mock_contexts.append(f"Context {i}: Sample text about project management, development, and testing.")
        
        # Generate embeddings (LanceDB expects all data upfront for table creation)
        print("   Generating embeddings...")
        embeddings = model.encode(mock_contexts, show_progress_bar=True)
        
        # Prepare data for LanceDB
        data = []
        for i, (text, embedding) in enumerate(zip(mock_contexts, embeddings)):
            data.append({
                "id": f"ctx_{i}",
                "text": text,
                "vector": embedding.tolist(),
                "mtime": time.time()
            })
        
        # Create table
        table = db.create_table("contexts", data=data, mode="overwrite")
        
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
            results = table.search(query_embedding.tolist()).limit(5).to_list()
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
        print(f"   + Fast Rust-based implementation")
        print(f"   + Good for larger scale (optimized for 100K+ vectors)")
        print(f"   + Columnar storage (efficient disk usage)")
        print(f"   + Active development")
        print(f"   - More complex API (requires upfront schema)")
        print(f"   - Requires file-based storage (no pure in-memory)")
        
        print("\n" + "=" * 60)
        
        return {
            "total_p95": total_p95,
            "search_p95": search_p95,
            "embed_p95": percentile(embed_latencies, 95),
            "passes": total_p95 < 100 and search_p95 < 50
        }
    
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    if DEPS_AVAILABLE:
        results = benchmark_lancedb()
        print(f"\nLanceDB POC Results: {'✅ PASS' if results['passes'] else '❌ NEEDS OPTIMIZATION'}")
    else:
        print("\nInstall dependencies to run benchmark:")
        print("  pip install lancedb sentence-transformers")

