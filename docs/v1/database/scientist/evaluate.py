#!/usr/bin/env python3
"""
Evaluation script for baseline and semantic search performance.

Usage:
    python evaluate.py --testset evaluation-testset.json --output baseline-results.json --search-method substring
"""

import argparse
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


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
            # Binary relevance: rel = 1 if relevant, 0 otherwise
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


def search_contexts_substring(query: str, contexts_dir: Path) -> list[str]:
    """
    Simulate word-based substring search.
    
    This is more realistic than exact phrase matching - it finds documents
    that contain any significant words from the query.
    """
    results_with_scores = []
    
    # Extract significant words (filter stop words)
    stop_words = {
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'to', 'of', 'in', 'on', 'at',
        'for', 'with', 'by', 'from', 'as', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'under', 'over', 'i', 'you', 'he',
        'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our',
        'their', 'this', 'that', 'these', 'those', 'what', 'which', 'who', 'when',
        'where', 'why', 'how'
    }
    
    query_words = [w.lower() for w in query.split() if w.lower() not in stop_words and len(w) > 2]
    
    if not query_words:
        # Fallback to full query if all words filtered
        query_words = [query.lower()]
    
    # Read all context files
    for context_file in contexts_dir.glob("*.mdc"):
        context_name = context_file.stem
        
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
            
            # Count how many query words appear in the document
            matches = sum(1 for word in query_words if word in content)
            
            # Only include if at least one word matches
            if matches > 0:
                # Score by percentage of query words matched
                score = matches / len(query_words)
                results_with_scores.append((context_name, score))
        except Exception as e:
            print(f"Warning: Failed to read {context_file}: {e}")
    
    # Sort by score (descending) and return names only
    results_with_scores.sort(key=lambda x: x[1], reverse=True)
    return [name for name, score in results_with_scores]


def evaluate_testset(
    testset_path: Path,
    contexts_dir: Path,
    search_method: str = "substring"
) -> dict[str, Any]:
    """
    Evaluate search performance against test set.
    
    Args:
        testset_path: Path to evaluation-testset.json
        contexts_dir: Path to contexts directory
        search_method: "substring" or "semantic"
    
    Returns:
        Results dictionary with metrics and per-query results
    """
    # Load test set
    with open(testset_path, 'r', encoding='utf-8') as f:
        testset = json.load(f)
    
    queries = testset['queries']
    
    # Count available contexts
    num_contexts = len(list(contexts_dir.glob("*.mdc")))
    
    # Initialize results
    results = {
        "metadata": {
            "evaluation_date": datetime.now().isoformat(),
            "search_method": search_method,
            "test_set_version": testset['metadata']['version'],
            "num_queries": len(queries),
            "system_info": {
                "num_contexts": num_contexts,
                "contexts_directory": str(contexts_dir)
            }
        },
        "metrics": {},
        "per_query_results": []
    }
    
    # Evaluate each query
    all_precision_at_5 = []
    all_recall_at_5 = []
    all_mrr = []
    all_ndcg_at_10 = []
    
    for query_obj in queries:
        query_id = query_obj['id']
        query_text = query_obj['query']
        query_type = query_obj['type']
        relevant_contexts = query_obj['relevant_contexts']
        
        # Search
        if search_method == "substring":
            retrieved = search_contexts_substring(query_text, contexts_dir)
        else:
            raise ValueError(f"Unsupported search method: {search_method}")
        
        # Calculate metrics for this query
        p_at_5 = calculate_precision_at_k(retrieved, relevant_contexts, 5)
        r_at_5 = calculate_recall_at_k(retrieved, relevant_contexts, 5)
        rr = calculate_reciprocal_rank(retrieved, relevant_contexts)
        ndcg_at_10 = calculate_ndcg_at_k(retrieved, relevant_contexts, 10)
        
        all_precision_at_5.append(p_at_5)
        all_recall_at_5.append(r_at_5)
        all_mrr.append(rr)
        all_ndcg_at_10.append(ndcg_at_10)
        
        # Store per-query result
        per_query_result = {
            "query_id": query_id,
            "query": query_text,
            "query_type": query_type,
            "relevant_contexts": relevant_contexts,
            "retrieved_contexts": retrieved,
            "num_relevant_total": len(relevant_contexts),
            "num_relevant_retrieved_at_5": sum(1 for ctx in retrieved[:5] if ctx in relevant_contexts),
            "precision_at_5": p_at_5,
            "recall_at_5": r_at_5,
            "reciprocal_rank": rr,
            "ndcg_at_10": ndcg_at_10
        }
        
        results["per_query_results"].append(per_query_result)
    
    # Aggregate metrics
    def mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0
    
    results["metrics"] = {
        "precision_at_5": mean(all_precision_at_5),
        "recall_at_5": mean(all_recall_at_5),
        "mrr": mean(all_mrr),
        "ndcg_at_10": mean(all_ndcg_at_10)
    }
    
    # Add per-type metrics
    query_types = set(q['type'] for q in queries)
    type_metrics = {}
    
    for qtype in query_types:
        type_results = [r for r in results["per_query_results"] if r["query_type"] == qtype]
        if type_results:
            type_metrics[qtype] = {
                "count": len(type_results),
                "precision_at_5": mean([r["precision_at_5"] for r in type_results]),
                "recall_at_5": mean([r["recall_at_5"] for r in type_results]),
                "mrr": mean([r["reciprocal_rank"] for r in type_results]),
                "ndcg_at_10": mean([r["ndcg_at_10"] for r in type_results])
            }
    
    results["metrics_by_type"] = type_metrics
    
    return results


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Evaluate search performance")
    parser.add_argument(
        "--testset",
        type=Path,
        required=True,
        help="Path to evaluation-testset.json"
    )
    parser.add_argument(
        "--contexts-dir",
        type=Path,
        default=Path(".out_of_context/contexts"),
        help="Path to contexts directory (default: .out_of_context/contexts)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to save results JSON"
    )
    parser.add_argument(
        "--search-method",
        choices=["substring", "semantic"],
        default="substring",
        help="Search method to evaluate"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.testset.exists():
        print(f"Error: Test set not found: {args.testset}")
        return
    
    if not args.contexts_dir.exists():
        print(f"Error: Contexts directory not found: {args.contexts_dir}")
        return
    
    print(f"Evaluating {args.search_method} search...")
    print(f"Test set: {args.testset}")
    print(f"Contexts: {args.contexts_dir}")
    print()
    
    # Run evaluation
    results = evaluate_testset(args.testset, args.contexts_dir, args.search_method)
    
    # Save results
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Evaluation complete!")
    print()
    print("Overall Metrics:")
    print(f"  Precision@5: {results['metrics']['precision_at_5']:.3f}")
    print(f"  Recall@5:    {results['metrics']['recall_at_5']:.3f}")
    print(f"  MRR:         {results['metrics']['mrr']:.3f}")
    print(f"  NDCG@10:     {results['metrics']['ndcg_at_10']:.3f}")
    print()
    print(f"Results saved to: {args.output}")


if __name__ == "__main__":
    main()

