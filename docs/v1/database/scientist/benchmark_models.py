#!/usr/bin/env python3
"""
Benchmark script for embedding model selection.

Tests multiple sentence-transformers models on the evaluation test set,
measuring quality (P@5, R@5, MRR, NDCG) and latency.

Usage:
    python benchmark_models.py --testset evaluation-testset.json --output results.json
"""

import argparse
import json
import math
import statistics
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: sentence-transformers not installed. Install with: pip install sentence-transformers")
    exit(1)

import numpy as np
from numpy.linalg import norm


# Candidate models to test
CANDIDATE_MODELS = [
    {
        "name": "intfloat/e5-small-v2",
        "max_seq_length": 512,
        "expected_size_mb": 130,
        "notes": "E5 small model, 512 tokens, good quality/speed tradeoff"
    },
    {
        "name": "intfloat/e5-base-v2",
        "max_seq_length": 512,
        "expected_size_mb": 220,
        "notes": "E5 base model, 512 tokens, higher quality than small"
    },
    {
        "name": "BAAI/bge-small-en-v1.5",
        "max_seq_length": 512,
        "expected_size_mb": 130,
        "notes": "BGE small, 512 tokens, strong MTEB performance"
    },
    {
        "name": "BAAI/bge-base-en-v1.5",
        "max_seq_length": 512,
        "expected_size_mb": 420,
        "notes": "BGE base, 512 tokens, high quality"
    },
    {
        "name": "sentence-transformers/all-mpnet-base-v2",
        "max_seq_length": 384,
        "expected_size_mb": 420,
        "notes": "MPNet base, 384 tokens (may need chunking), high quality"
    },
    {
        "name": "sentence-transformers/all-MiniLM-L12-v2",
        "max_seq_length": 256,
        "expected_size_mb": 130,
        "notes": "MiniLM L12, 256 tokens (will need chunking), fast"
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


def embed_contexts(model: SentenceTransformer, contexts: dict[str, str], model_name: str) -> dict[str, np.ndarray]:
    """Embed all contexts using the model."""
    print(f"  Embedding {len(contexts)} contexts...")
    context_names = list(contexts.keys())
    context_texts = [contexts[name] for name in context_names]
    
    # E5 models require "passage: " prefix
    # BGE models don't need prefix for passages
    if "e5" in model_name.lower():
        context_texts = [f"passage: {text}" for text in context_texts]
    
    # Batch embed
    embeddings = model.encode(context_texts, show_progress_bar=True, convert_to_numpy=True)
    
    # Return as dict
    return {name: emb for name, emb in zip(context_names, embeddings)}


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
    num_runs: int = 10
) -> dict[str, float]:
    """Measure embedding latency for test texts."""
    latencies = []
    
    for _ in range(num_runs):
        start = time.time()
        _ = model.encode(test_texts, show_progress_bar=False, convert_to_numpy=True)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        latencies.append(elapsed)
    
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
    baseline_metrics: dict[str, float]
) -> dict[str, Any]:
    """Benchmark a single embedding model."""
    print(f"\n{'='*60}")
    print(f"Benchmarking: {model_name}")
    print(f"{'='*60}")
    
    # Load model
    print(f"  Loading model: {model_name}")
    try:
        model = SentenceTransformer(model_name)
        actual_max_seq_length = model.max_seq_length
        print(f"  Max sequence length: {actual_max_seq_length}")
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
    
    # Embed contexts
    context_embeddings = embed_contexts(model, contexts, model_name)
    
    # Measure embedding latency on sample contexts
    print(f"  Measuring embedding latency...")
    sample_contexts = list(contexts.values())[:5]  # Use first 5 contexts
    # E5 models require "passage: " prefix
    # BGE models don't need prefix for passages
    if "e5" in model_name.lower():
        sample_contexts = [f"passage: {text}" for text in sample_contexts]
    latency_metrics = measure_embedding_latency(model, sample_contexts)
    print(f"  Latency: {latency_metrics['mean_ms']:.1f}ms mean, {latency_metrics['p95_ms']:.1f}ms p95")
    
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
        # E5 models require "query: " prefix
        # BGE models require "Represent this sentence for searching relevant passages: " prefix
        query_text_processed = query_text
        if "e5" in model_name.lower():
            query_text_processed = f"query: {query_text}"
        elif "bge" in model_name.lower():
            query_text_processed = f"Represent this sentence for searching relevant passages: {query_text}"
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
    
    return {
        "model_name": model_name,
        "max_seq_length": actual_max_seq_length,
        "status": "success",
        "quality_metrics": quality_metrics,
        "improvement_vs_baseline": improvement,
        "latency_metrics": {
            "embedding": latency_metrics,
            "query": query_latency_stats
        },
        "per_query_results": per_query_results
    }


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark embedding models")
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
    parser.add_argument(
        "--models",
        nargs="+",
        help="Specific models to test (default: all candidates)"
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
    
    print("Baseline Metrics:")
    print(f"  Precision@5: {baseline_metrics['precision_at_5']:.3f}")
    print(f"  Recall@5:    {baseline_metrics['recall_at_5']:.3f}")
    print(f"  MRR:         {baseline_metrics['mrr']:.3f}")
    print(f"  NDCG@10:     {baseline_metrics['ndcg_at_10']:.3f}")
    print()
    
    # Determine which models to test
    if args.models:
        models_to_test = [{"name": name} for name in args.models]
    else:
        models_to_test = CANDIDATE_MODELS
    
    print(f"Testing {len(models_to_test)} models...")
    print()
    
    # Benchmark each model
    results = {
        "metadata": {
            "testset_path": str(args.testset),
            "contexts_dir": str(args.contexts_dir),
            "baseline_metrics": baseline_metrics,
            "num_models_tested": len(models_to_test)
        },
        "models": []
    }
    
    for model_info in models_to_test:
        model_name = model_info["name"]
        result = benchmark_model(model_name, args.testset, args.contexts_dir, baseline_metrics)
        results["models"].append(result)
    
    # Save results
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Benchmark complete!")
    print(f"Results saved to: {args.output}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

