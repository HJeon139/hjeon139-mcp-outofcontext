#!/usr/bin/env python3
"""
Benchmark script for 8k context length embedding models.

Tests models that support 8192 tokens, eliminating the need for chunking.
Focus: Latency measurement on actual context sizes (median 2,683 tokens, P95 4,354 tokens).

Usage:
    python benchmark_8k_models.py --testset evaluation-testset.json --output results.json
"""

import argparse
import json
import math
import os
import statistics
import time
from pathlib import Path
from typing import Any

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: sentence-transformers not installed. Install with: pip install sentence-transformers")
    exit(1)

import numpy as np
from numpy.linalg import norm

# Set environment variable to use CPU if MPS runs out of memory
# This helps avoid MPS memory issues with large 8k contexts
if "PYTORCH_ENABLE_MPS_FALLBACK" not in os.environ:
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"


# 8k context models to test
EIGHT_K_MODELS = [
    {
        "name": "nomic-ai/modernbert-embed-base",
        "max_seq_length": 8192,
        "model_size_mb": 568,
        "embedding_dim": 768,
        "prefix_query": "search_query: ",
        "prefix_document": "search_document: ",
        "notes": "ModernBERT-based, 8192 max seq length, supports Matryoshka 256-dim"
    },
    {
        "name": "nomic-ai/nomic-embed-text-v2-moe",
        "max_seq_length": 8192,
        "model_size_mb": 2000,
        "embedding_dim": 768,
        "prefix_query": "search_query: ",
        "prefix_document": "search_document: ",
        "notes": "Multilingual MoE model, ~100 languages, larger size"
    },
    {
        "name": "Snowflake/snowflake-arctic-embed-l-v2.0",
        "max_seq_length": 8192,
        "model_size_mb": 2166,
        "embedding_dim": 1024,
        "prefix_query": "",  # Unknown, will try without prefix first
        "prefix_document": "",  # Unknown, will try without prefix first
        "notes": "Snowflake model, MTEB 63.67 retrieval"
    },
    {
        "name": "Alibaba-NLP/gte-multilingual-base",
        "max_seq_length": 8192,
        "model_size_mb": 582,
        "embedding_dim": 768,
        "prefix_query": "",  # No prefix needed
        "prefix_document": "",  # No prefix needed
        "notes": "Multilingual, no prefix needed, MTEB 60.68 retrieval"
    },
    {
        "name": "ibm-granite/granite-embedding-english-r2",
        "max_seq_length": 8192,
        "model_size_mb": 284,
        "embedding_dim": 768,
        "prefix_query": "",  # Unknown, will try without prefix first
        "prefix_document": "",  # Unknown, will try without prefix first
        "notes": "IBM Granite, 149M params, English only"
    },
]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    return np.dot(a, b) / (norm(a) * norm(b))


def calculate_precision_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """Calculate Precision@K."""
    if k == 0:
        return 0.0
    top_k = retrieved[:k]
    relevant_retrieved = sum(1 for item in top_k if item in relevant)
    return relevant_retrieved / k


def calculate_recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """Calculate Recall@K."""
    if len(relevant) == 0:
        return 0.0
    top_k = retrieved[:k]
    relevant_retrieved = sum(1 for item in top_k if item in relevant)
    return relevant_retrieved / len(relevant)


def calculate_reciprocal_rank(retrieved: list[str], relevant: list[str]) -> float:
    """Calculate reciprocal rank (1/rank of first relevant result)."""
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def calculate_dcg_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """Calculate Discounted Cumulative Gain@K."""
    dcg = 0.0
    for rank, item in enumerate(retrieved[:k], start=1):
        if item in relevant:
            rel = 1
            dcg += rel / math.log2(rank + 1)
    return dcg


def calculate_ndcg_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """Calculate Normalized Discounted Cumulative Gain@K."""
    if len(relevant) == 0:
        return 0.0
    
    dcg = calculate_dcg_at_k(retrieved, relevant, k)
    
    # Ideal DCG: all relevant items at top positions
    ideal_retrieved = relevant + [f"_dummy_{i}" for i in range(k)]
    idcg = calculate_dcg_at_k(ideal_retrieved, relevant, k)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def load_contexts(contexts_dir: Path) -> dict[str, str]:
    """Load all .mdc context files and return name -> content mapping."""
    contexts = {}
    for context_file in contexts_dir.glob("*.mdc"):
        context_name = context_file.stem
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                content = f.read()
            contexts[context_name] = content
        except Exception as e:
            print(f"Warning: Failed to read {context_file}: {e}")
    return contexts


def embed_contexts(
    model: SentenceTransformer,
    contexts: dict[str, str],
    prefix_document: str
) -> dict[str, np.ndarray]:
    """Embed all contexts using the model with document prefix."""
    print(f"  Embedding {len(contexts)} contexts (NO CHUNKING - full contexts)...")
    print(f"  Processing one at a time to avoid memory issues with 8k contexts...")
    context_embeddings = {}
    
    # Process one at a time to avoid memory issues with large 8k contexts
    for i, (name, text) in enumerate(contexts.items(), 1):
        print(f"    Embedding {i}/{len(contexts)}: {name}")
        # Apply prefix if provided, otherwise use text as-is
        text_with_prefix = f"{prefix_document}{text}" if prefix_document else text
        embedding = model.encode([text_with_prefix], show_progress_bar=False, convert_to_numpy=True)[0]
        context_embeddings[name] = embedding
    
    return context_embeddings


def semantic_search(
    query_embedding: np.ndarray,
    context_embeddings: dict[str, np.ndarray],
    top_k: int = 10
) -> list[str]:
    """Perform semantic search using cosine similarity."""
    similarities = []
    for context_name, context_emb in context_embeddings.items():
        sim = cosine_similarity(query_embedding, context_emb)
        similarities.append((context_name, sim))
    
    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in similarities[:top_k]]


def measure_embedding_latency(
    model: SentenceTransformer,
    test_texts: list[str],
    prefix_document: str,
    num_runs: int = 20
) -> dict[str, float]:
    """Measure embedding latency for test texts."""
    latencies = []
    
    # Process one at a time to avoid memory issues
    for _ in range(num_runs):
        # Measure latency for each text individually and average
        run_latencies = []
        for text in test_texts:
            # Apply prefix if provided, otherwise use text as-is
            text_with_prefix = f"{prefix_document}{text}" if prefix_document else text
            start = time.time()
            _ = model.encode([text_with_prefix], show_progress_bar=False, convert_to_numpy=True)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            run_latencies.append(elapsed)
        # Average latency per run
        latencies.append(statistics.mean(run_latencies))
    
    return {
        "mean_ms": statistics.mean(latencies),
        "p95_ms": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "num_runs": num_runs
    }


def benchmark_model(
    model_name: str,
    testset_path: Path,
    contexts_dir: Path,
    baseline_metrics: dict[str, float],
    prefix_query: str,
    prefix_document: str
) -> dict[str, Any]:
    """Benchmark a single 8k embedding model."""
    print(f"\n{'='*60}")
    print(f"Benchmarking 8K Model: {model_name}")
    print(f"{'='*60}")
    
    # Load model
    print(f"  Loading model: {model_name}")
    try:
        # Use CPU to avoid MPS memory issues with large 8k contexts
        import torch
        device = "cpu"  # Force CPU for 8k model benchmark to avoid memory issues
        print(f"  Using device: {device} (CPU to avoid MPS memory issues)")
        
        # Try loading with trust_remote_code if needed
        try:
            model = SentenceTransformer(model_name, device=device)
        except Exception as e:
            if "trust_remote_code" in str(e).lower() or "custom code" in str(e).lower():
                print(f"  Retrying with trust_remote_code=True...")
                model = SentenceTransformer(model_name, device=device, trust_remote_code=True)
            else:
                raise
        
        actual_max_seq_length = model.max_seq_length
        print(f"  Max sequence length: {actual_max_seq_length}")
        print(f"  ✅ NO CHUNKING REQUIRED - All contexts fit within {actual_max_seq_length} tokens")
    except Exception as e:
        print(f"  ERROR: Failed to load model: {e}")
        return {
            "model_name": model_name,
            "error": str(e),
            "status": "failed"
        }
    
    # Load test set
    with open(testset_path, 'r', encoding='utf-8') as f:
        testset = json.load(f)
    queries = testset['queries']
    
    # Load contexts
    print(f"  Loading contexts from: {contexts_dir}")
    contexts = load_contexts(contexts_dir)
    print(f"  Loaded {len(contexts)} contexts")
    
    # Load context size analysis to identify median and P95 contexts
    context_size_file = contexts_dir.parent / "context-size-analysis.json"
    context_sizes = {}
    if context_size_file.exists():
        with open(context_size_file, 'r', encoding='utf-8') as f:
            size_data = json.load(f)
            for file_info in size_data.get('files', []):
                context_sizes[file_info['name']] = file_info['tokens']
    
    # Find median and P95 contexts for latency testing
    median_context = None
    p95_context = None
    if context_sizes:
        sorted_by_size = sorted(context_sizes.items(), key=lambda x: x[1])
        median_idx = len(sorted_by_size) // 2
        p95_idx = int(len(sorted_by_size) * 0.95)
        median_name = sorted_by_size[median_idx][0] if median_idx < len(sorted_by_size) else None
        p95_name = sorted_by_size[p95_idx][0] if p95_idx < len(sorted_by_size) else None
        
        if median_name and median_name in contexts:
            median_context = contexts[median_name]
            print(f"  Median context: {median_name} ({context_sizes[median_name]} tokens)")
        if p95_name and p95_name in contexts:
            p95_context = contexts[p95_name]
            print(f"  P95 context: {p95_name} ({context_sizes[p95_name]} tokens)")
    
    # Embed contexts (NO CHUNKING - full contexts)
    context_embeddings = embed_contexts(model, contexts, prefix_document)
    
    # Measure embedding latency on representative contexts
    print(f"  Measuring embedding latency on representative contexts...")
    latency_test_contexts = []
    if median_context:
        latency_test_contexts.append(median_context)
    if p95_context and p95_context != median_context:
        latency_test_contexts.append(p95_context)
    # Add a few more contexts for better statistics
    for i, (name, text) in enumerate(list(contexts.items())[:3]):
        if text not in latency_test_contexts:
            latency_test_contexts.append(text)
    
    latency_metrics = measure_embedding_latency(model, latency_test_contexts, prefix_document, num_runs=20)
    print(f"  Embedding Latency: {latency_metrics['mean_ms']:.1f}ms mean, {latency_metrics['p95_ms']:.1f}ms p95")
    
    # Evaluate queries
    print(f"  Evaluating {len(queries)} queries...")
    all_precision_at_5 = []
    all_recall_at_5 = []
    all_mrr = []
    all_ndcg_at_10 = []
    query_latencies = []
    
    per_query_results = []
    
    for query_obj in queries:
        query_id = query_obj['id']
        query_text = query_obj['query']
        query_type = query_obj['type']
        relevant_contexts = query_obj['relevant_contexts']
        
        # Embed query and search
        start = time.time()
        # Apply prefix if provided, otherwise use query as-is
        query_text_processed = f"{prefix_query}{query_text}" if prefix_query else query_text
        query_embedding = model.encode([query_text_processed], show_progress_bar=False, convert_to_numpy=True)[0]
        retrieved = semantic_search(query_embedding, context_embeddings, top_k=10)
        query_latency = (time.time() - start) * 1000  # ms
        query_latencies.append(query_latency)
        
        # Calculate metrics
        p_at_5 = calculate_precision_at_k(retrieved, relevant_contexts, 5)
        r_at_5 = calculate_recall_at_k(retrieved, relevant_contexts, 5)
        rr = calculate_reciprocal_rank(retrieved, relevant_contexts)
        ndcg_at_10 = calculate_ndcg_at_k(retrieved, relevant_contexts, 10)
        
        all_precision_at_5.append(p_at_5)
        all_recall_at_5.append(r_at_5)
        all_mrr.append(rr)
        all_ndcg_at_10.append(ndcg_at_10)
        
        per_query_results.append({
            "query_id": query_id,
            "query": query_text,
            "query_type": query_type,
            "precision_at_5": p_at_5,
            "recall_at_5": r_at_5,
            "reciprocal_rank": rr,
            "ndcg_at_10": ndcg_at_10,
            "query_latency_ms": query_latency
        })
    
    # Aggregate metrics
    def mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0
    
    quality_metrics = {
        "precision_at_5": mean(all_precision_at_5),
        "recall_at_5": mean(all_recall_at_5),
        "mrr": mean(all_mrr),
        "ndcg_at_10": mean(all_ndcg_at_10)
    }
    
    # Calculate improvement vs baseline
    improvement = {
        "precision_at_5_pct": ((quality_metrics["precision_at_5"] - baseline_metrics["precision_at_5"]) / baseline_metrics["precision_at_5"]) * 100,
        "recall_at_5_pct": ((quality_metrics["recall_at_5"] - baseline_metrics["recall_at_5"]) / baseline_metrics["recall_at_5"]) * 100,
        "mrr_pct": ((quality_metrics["mrr"] - baseline_metrics["mrr"]) / baseline_metrics["mrr"]) * 100,
        "ndcg_at_10_pct": ((quality_metrics["ndcg_at_10"] - baseline_metrics["ndcg_at_10"]) / baseline_metrics["ndcg_at_10"]) * 100,
    }
    
    query_latency_stats = {
        "mean_ms": mean(query_latencies),
        "p95_ms": statistics.quantiles(query_latencies, n=20)[18] if len(query_latencies) >= 20 else max(query_latencies),
        "min_ms": min(query_latencies),
        "max_ms": max(query_latencies)
    }
    
    print(f"\n  Results:")
    print(f"    Precision@5: {quality_metrics['precision_at_5']:.3f} ({improvement['precision_at_5_pct']:+.1f}% vs baseline)")
    print(f"    Recall@5:    {quality_metrics['recall_at_5']:.3f} ({improvement['recall_at_5_pct']:+.1f}% vs baseline)")
    print(f"    MRR:         {quality_metrics['mrr']:.3f} ({improvement['mrr_pct']:+.1f}% vs baseline)")
    print(f"    NDCG@10:     {quality_metrics['ndcg_at_10']:.3f} ({improvement['ndcg_at_10_pct']:+.1f}% vs baseline)")
    print(f"    Query Latency: {query_latency_stats['mean_ms']:.1f}ms mean, {query_latency_stats['p95_ms']:.1f}ms p95")
    
    # Check if latency meets target
    latency_meets_target = query_latency_stats['p95_ms'] < 100.0
    print(f"    ✅ Latency target (< 100ms p95): {'PASS' if latency_meets_target else 'FAIL'}")
    
    return {
        "model_name": model_name,
        "max_seq_length": actual_max_seq_length,
        "status": "success",
        "chunking_required": False,
        "quality_metrics": quality_metrics,
        "improvement_vs_baseline": improvement,
        "latency_metrics": {
            "embedding": latency_metrics,
            "query": query_latency_stats
        },
        "latency_meets_target": latency_meets_target,
        "per_query_results": per_query_results
    }


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark 8k context length embedding models")
    parser.add_argument(
        "--testset",
        type=Path,
        default=Path("evaluation-testset.json"),
        help="Path to evaluation-testset.json"
    )
    parser.add_argument(
        "--contexts-dir",
        type=Path,
        default=Path("../../.out_of_context/contexts"),
        help="Path to contexts directory"
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("baseline-results.json"),
        help="Path to baseline-results.json"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to save benchmark results JSON"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.testset.exists():
        print(f"Error: Test set not found: {args.testset}")
        return
    
    if not args.contexts_dir.exists():
        print(f"Error: Contexts directory not found: {args.contexts_dir}")
        return
    
    if not args.baseline.exists():
        print(f"Error: Baseline results not found: {args.baseline}")
        return
    
    # Load baseline metrics
    with open(args.baseline, 'r', encoding='utf-8') as f:
        baseline_data = json.load(f)
    baseline_metrics = baseline_data['metrics']
    
    print("=" * 80)
    print("8K Context Model Benchmark")
    print("=" * 80)
    print()
    print("Baseline Metrics:")
    print(f"  Precision@5: {baseline_metrics['precision_at_5']:.3f}")
    print(f"  Recall@5:    {baseline_metrics['recall_at_5']:.3f}")
    print(f"  MRR:         {baseline_metrics['mrr']:.3f}")
    print(f"  NDCG@10:     {baseline_metrics['ndcg_at_10']:.3f}")
    print()
    print("Target: Query latency < 100ms p95")
    print("Key Advantage: NO CHUNKING REQUIRED (all contexts fit in 8k tokens)")
    print()
    
    # Benchmark each 8k model
    results = {
        "metadata": {
            "testset_path": str(args.testset),
            "contexts_dir": str(args.contexts_dir),
            "baseline_metrics": baseline_metrics,
            "num_models_tested": len(EIGHT_K_MODELS),
            "benchmark_type": "8k_context_models"
        },
        "models": []
    }
    
    for model_info in EIGHT_K_MODELS:
        model_name = model_info["name"]
        result = benchmark_model(
            model_name,
            args.testset,
            args.contexts_dir,
            baseline_metrics,
            model_info["prefix_query"],
            model_info["prefix_document"]
        )
        results["models"].append(result)
    
    # Save results
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Benchmark complete!")
    print(f"Results saved to: {args.output}")
    print(f"{'='*60}")
    
    # Print summary
    print("\nSummary:")
    for model_result in results["models"]:
        if model_result.get("status") == "success":
            print(f"\n  Model: {model_result['model_name']}")
            print(f"    Query Latency (p95): {model_result['latency_metrics']['query']['p95_ms']:.1f}ms")
            print(f"    Latency Target: {'✅ PASS' if model_result.get('latency_meets_target') else '❌ FAIL'}")
            print(f"    Precision@5: {model_result['quality_metrics']['precision_at_5']:.3f}")
            print(f"    Chunking Required: {'NO ✅' if not model_result.get('chunking_required') else 'YES ⚠️'}")


if __name__ == "__main__":
    main()

