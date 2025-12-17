#!/usr/bin/env python3
"""
Comprehensive Database Comparison: ChromaDB vs LanceDB

Addresses critique:
1. Independent sentence transformers (fix embedding measurement)
2. Test at max capacity (4K contexts)
3. Evaluate hybrid search capabilities
4. Measure performance degradation at scale
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import statistics
import tempfile
import shutil

# Check dependencies
try:
    import chromadb
    import lancedb
    from sentence_transformers import SentenceTransformer
    import numpy as np
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    print(f"⚠️  Missing dependencies: {e}")
    print("Run: pip install chromadb lancedb sentence-transformers")


def load_all_test_queries() -> List[Dict[str, Any]]:
    """Load ALL queries from evaluation test set (55 queries)."""
    testset_path = Path(__file__).parent.parent.parent / "scientist" / "evaluation-testset.json"
    with open(testset_path) as f:
        data = json.load(f)
    return data["queries"]


def generate_mock_contexts(count: int) -> List[str]:
    """Generate realistic mock context texts."""
    templates = [
        "Project overview: This context describes the architecture and goals of the {topic} system.",
        "Implementation details for {topic} including best practices and common pitfalls.",
        "Troubleshooting guide for {topic} covering error handling and debugging strategies.",
        "API reference for {topic} with detailed parameter descriptions and examples.",
        "Configuration guide for {topic} explaining environment setup and dependencies.",
        "Testing strategy for {topic} including unit tests and integration tests.",
        "Security considerations for {topic} covering authentication and authorization.",
        "Performance optimization tips for {topic} with benchmarking approaches.",
    ]
    
    topics = [
        "database", "authentication", "API", "frontend", "backend", "storage",
        "caching", "messaging", "logging", "monitoring", "deployment", "CI/CD",
        "networking", "security", "testing", "documentation", "search", "indexing"
    ]
    
    contexts = []
    for i in range(count):
        template = templates[i % len(templates)]
        topic = topics[i % len(topics)]
        contexts.append(template.format(topic=topic))
    
    return contexts


def percentile(data: List[float], p: int) -> float:
    """Calculate percentile."""
    sorted_data = sorted(data)
    index = int(len(sorted_data) * p / 100)
    return sorted_data[min(index, len(sorted_data)-1)]


def print_stats(name: str, latencies: List[float]):
    """Print latency statistics."""
    print(f"   {name}:")
    print(f"     p50: {percentile(latencies, 50):.1f}ms")
    print(f"     p95: {percentile(latencies, 95):.1f}ms")
    print(f"     p99: {percentile(latencies, 99):.1f}ms")
    print(f"     avg: {statistics.mean(latencies):.1f}ms")


def benchmark_chromadb_at_scale(context_counts: List[int]):
    """Benchmark ChromaDB at different scales."""
    if not DEPS_AVAILABLE:
        return None
    
    print("=" * 70)
    print("ChromaDB Comprehensive Benchmark")
    print("=" * 70)
    
    # Load embedding model ONCE (shared across all queries)
    print("\n1. Loading embedding model (one-time cost)...")
    start = time.time()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    load_time = time.time() - start
    print(f"   ✅ Model loaded in {load_time:.2f}s")
    
    # Load all test queries (55 queries for reliable p95)
    test_queries = load_all_test_queries()
    print(f"   ✅ Loaded {len(test_queries)} test queries")
    
    results = {}
    
    for num_contexts in context_counts:
        print(f"\n{'=' * 70}")
        print(f"Testing with {num_contexts} contexts")
        print(f"{'=' * 70}")
        
        # Initialize ChromaDB
        print(f"\n2. Initializing ChromaDB...")
        start = time.time()
        client = chromadb.Client()
        collection = client.create_collection(
            name=f"contexts_{num_contexts}",
            metadata={"hnsw:space": "cosine"}
        )
        init_time = time.time() - start
        print(f"   ✅ Initialized in {init_time:.3f}s")
        
        # Insert contexts
        print(f"\n3. Inserting {num_contexts} contexts...")
        start = time.time()
        mock_contexts = generate_mock_contexts(num_contexts)
        
        # Generate embeddings in batches (independent sentence transformers)
        batch_size = 100
        insert_times = []
        for i in range(0, len(mock_contexts), batch_size):
            batch = mock_contexts[i:i+batch_size]
            batch_start = time.time()
            embeddings = model.encode(batch, show_progress_bar=False)
            batch_time = time.time() - batch_start
            insert_times.append(batch_time)
            
            ids = [f"ctx_{j}" for j in range(i, i+len(batch))]
            collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                metadatas=[{"mtime": time.time()} for _ in batch],
                documents=batch
            )
        
        insert_time = time.time() - start
        print(f"   ✅ Inserted in {insert_time:.2f}s ({insert_time/num_contexts*1000:.1f}ms per context)")
        
        # Benchmark queries
        print(f"\n4. Benchmarking {len(test_queries)} queries...")
        query_latencies = []
        embed_latencies = []
        search_latencies = []
        
        for q in test_queries:
            query_text = q["query"]
            
            # Measure embedding time (independent sentence transformers)
            start = time.time()
            query_embedding = model.encode([query_text], show_progress_bar=False)[0]
            embed_time = time.time() - start
            embed_latencies.append(embed_time * 1000)
            
            # Measure search time (pure vector search)
            start = time.time()
            search_results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=5
            )
            search_time = time.time() - start
            search_latencies.append(search_time * 1000)
            
            query_latencies.append((embed_time + search_time) * 1000)
        
        print(f"\n   Results ({len(test_queries)} queries, {num_contexts} contexts):")
        print(f"   {'-' * 50}")
        print_stats("Total Latency", query_latencies)
        print_stats("\n   Embedding Time", embed_latencies)
        print_stats("\n   Vector Search Time", search_latencies)
        
        # Evaluation
        total_p95 = percentile(query_latencies, 95)
        search_p95 = percentile(search_latencies, 95)
        
        print(f"\n   Evaluation:")
        if total_p95 < 100:
            print(f"   ✅ PASS: p95 latency ({total_p95:.1f}ms) < 100ms target")
        else:
            print(f"   ❌ FAIL: p95 latency ({total_p95:.1f}ms) > 100ms target")
        
        results[num_contexts] = {
            "total_p95": total_p95,
            "total_avg": statistics.mean(query_latencies),
            "embed_p95": percentile(embed_latencies, 95),
            "embed_avg": statistics.mean(embed_latencies),
            "search_p95": search_p95,
            "search_avg": statistics.mean(search_latencies),
            "insert_time": insert_time,
            "passes": total_p95 < 100
        }
    
    return results


def benchmark_lancedb_at_scale(context_counts: List[int]):
    """Benchmark LanceDB at different scales."""
    if not DEPS_AVAILABLE:
        return None
    
    print("\n\n" + "=" * 70)
    print("LanceDB Comprehensive Benchmark")
    print("=" * 70)
    
    # Load embedding model ONCE
    print("\n1. Loading embedding model (one-time cost)...")
    start = time.time()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    load_time = time.time() - start
    print(f"   ✅ Model loaded in {load_time:.2f}s")
    
    # Load all test queries
    test_queries = load_all_test_queries()
    print(f"   ✅ Loaded {len(test_queries)} test queries")
    
    results = {}
    temp_dir = tempfile.mkdtemp()
    
    try:
        for num_contexts in context_counts:
            print(f"\n{'=' * 70}")
            print(f"Testing with {num_contexts} contexts")
            print(f"{'=' * 70}")
            
            # Initialize LanceDB
            print(f"\n2. Initializing LanceDB...")
            start = time.time()
            db = lancedb.connect(temp_dir)
            init_time = time.time() - start
            print(f"   ✅ Initialized in {init_time:.3f}s")
            
            # Insert contexts
            print(f"\n3. Inserting {num_contexts} contexts...")
            start = time.time()
            mock_contexts = generate_mock_contexts(num_contexts)
            
            # Generate embeddings (independent sentence transformers)
            embeddings = model.encode(mock_contexts, show_progress_bar=False)
            
            # Prepare data
            data = []
            for i, (text, embedding) in enumerate(zip(mock_contexts, embeddings)):
                data.append({
                    "id": f"ctx_{i}",
                    "text": text,
                    "vector": embedding.tolist(),
                    "mtime": time.time()
                })
            
            # Create table
            table = db.create_table(f"contexts_{num_contexts}", data=data, mode="overwrite")
            insert_time = time.time() - start
            print(f"   ✅ Inserted in {insert_time:.2f}s ({insert_time/num_contexts*1000:.1f}ms per context)")
            
            # Benchmark queries
            print(f"\n4. Benchmarking {len(test_queries)} queries...")
            query_latencies = []
            embed_latencies = []
            search_latencies = []
            
            for q in test_queries:
                query_text = q["query"]
                
                # Measure embedding time
                start = time.time()
                query_embedding = model.encode([query_text], show_progress_bar=False)[0]
                embed_time = time.time() - start
                embed_latencies.append(embed_time * 1000)
                
                # Measure search time
                start = time.time()
                search_results = table.search(query_embedding.tolist()).limit(5).to_list()
                search_time = time.time() - start
                search_latencies.append(search_time * 1000)
                
                query_latencies.append((embed_time + search_time) * 1000)
            
            print(f"\n   Results ({len(test_queries)} queries, {num_contexts} contexts):")
            print(f"   {'-' * 50}")
            print_stats("Total Latency", query_latencies)
            print_stats("\n   Embedding Time", embed_latencies)
            print_stats("\n   Vector Search Time", search_latencies)
            
            # Evaluation
            total_p95 = percentile(query_latencies, 95)
            search_p95 = percentile(search_latencies, 95)
            
            print(f"\n   Evaluation:")
            if total_p95 < 100:
                print(f"   ✅ PASS: p95 latency ({total_p95:.1f}ms) < 100ms target")
            else:
                print(f"   ❌ FAIL: p95 latency ({total_p95:.1f}ms) > 100ms target")
            
            results[num_contexts] = {
                "total_p95": total_p95,
                "total_avg": statistics.mean(query_latencies),
                "embed_p95": percentile(embed_latencies, 95),
                "embed_avg": statistics.mean(embed_latencies),
                "search_p95": search_p95,
                "search_avg": statistics.mean(search_latencies),
                "insert_time": insert_time,
                "passes": total_p95 < 100
            }
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    return results


def print_comparison(chromadb_results: Dict, lancedb_results: Dict):
    """Print side-by-side comparison."""
    print("\n\n" + "=" * 70)
    print("COMPREHENSIVE COMPARISON")
    print("=" * 70)
    
    for num_contexts in sorted(chromadb_results.keys()):
        chroma = chromadb_results[num_contexts]
        lance = lancedb_results[num_contexts]
        
        print(f"\n{num_contexts} Contexts:")
        print(f"  {'Metric':<25} {'ChromaDB':>15} {'LanceDB':>15} {'Winner':>12}")
        print(f"  {'-' * 69}")
        
        def compare(name, chroma_val, lance_val, lower_better=True):
            if lower_better:
                winner = "ChromaDB" if chroma_val < lance_val else "LanceDB"
                factor = max(chroma_val, lance_val) / min(chroma_val, lance_val)
            else:
                winner = "ChromaDB" if chroma_val > lance_val else "LanceDB"
                factor = max(chroma_val, lance_val) / min(chroma_val, lance_val)
            
            print(f"  {name:<25} {chroma_val:>14.1f}ms {lance_val:>14.1f}ms {winner:>8} ({factor:.1f}x)")
        
        compare("Total p95", chroma["total_p95"], lance["total_p95"])
        compare("Total avg", chroma["total_avg"], lance["total_avg"])
        compare("Embed p95", chroma["embed_p95"], lance["embed_p95"])
        compare("Search p95", chroma["search_p95"], lance["search_p95"])
        
        print(f"\n  Meets < 100ms target:")
        print(f"    ChromaDB: {'✅ YES' if chroma['passes'] else '❌ NO'}")
        print(f"    LanceDB:  {'✅ YES' if lance['passes'] else '❌ NO'}")


def research_hybrid_search():
    """Research hybrid search capabilities."""
    print("\n\n" + "=" * 70)
    print("HYBRID SEARCH CAPABILITIES")
    print("=" * 70)
    
    print("\nChromaDB:")
    print("  ✅ Built-in hybrid search support")
    print("  ✅ Can combine semantic + keyword search")
    print("  ✅ Uses 'where' and 'where_document' filters")
    print("  ✅ Metadata filtering (type, tags, etc.)")
    print("  📖 Example:")
    print("     collection.query(")
    print("         query_embeddings=[embedding],")
    print("         where={'type': 'project-info'},  # metadata filter")
    print("         where_document={'$contains': 'API'}  # keyword filter")
    print("     )")
    
    print("\nLanceDB:")
    print("  ✅ Full-text search (FTS) support via Lance 0.16+")
    print("  ✅ Can combine semantic + FTS in single query")
    print("  ✅ SQL-like 'where' clause for metadata filtering")
    print("  ✅ Reranking support for hybrid results")
    print("  📖 Example:")
    print("     table.search(embedding)")
    print("         .where(\"type = 'project-info'\")  # metadata filter")
    print("         .rerank(reranker=...)  # combine semantic + lexical")
    print("         .limit(5)")
    
    print("\n  Note: LanceDB FTS requires additional setup (tantivy indices)")
    print("  Note: ChromaDB hybrid search is more straightforward")
    
    print("\n📊 Verdict:")
    print("  - Both support hybrid search (semantic + lexical)")
    print("  - ChromaDB: Simpler API, built-in support")
    print("  - LanceDB: More powerful but requires setup")


if __name__ == "__main__":
    if not DEPS_AVAILABLE:
        print("\n❌ Install dependencies:")
        print("   pip install chromadb lancedb sentence-transformers")
        exit(1)
    
    # Test at different scales: 1K, 2K, 4K (max capacity)
    scales = [1000, 2000, 4000]
    
    print("Testing at scales: 1K, 2K, 4K contexts")
    print("Using all 55 test queries for reliable p95 statistics")
    print("")
    
    # Benchmark both databases
    chromadb_results = benchmark_chromadb_at_scale(scales)
    lancedb_results = benchmark_lancedb_at_scale(scales)
    
    # Compare results
    print_comparison(chromadb_results, lancedb_results)
    
    # Research hybrid search
    research_hybrid_search()
    
    print("\n\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)

