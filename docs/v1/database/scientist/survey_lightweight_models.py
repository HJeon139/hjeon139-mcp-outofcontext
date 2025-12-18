#!/usr/bin/env python3
"""
Survey lightweight models from MTEB leaderboard.

This script helps identify lightweight embedding models that meet our criteria:
- Max sequence length ≥ 512 tokens
- Model size < 500MB
- Sentence-transformers compatible
- Good MTEB scores

Note: This is a reference script. Actual MTEB scores should be verified from:
https://huggingface.co/spaces/mteb/leaderboard
"""

# Comprehensive list of lightweight models from MTEB leaderboard
# Based on research and MTEB leaderboard data
LIGHTWEIGHT_MODELS = [
    {
        "name": "intfloat/e5-small-v2",
        "max_seq_length": 512,
        "model_size_mb": 130,
        "embedding_dim": 384,
        "mteb_avg": 62.0,
        "mteb_retrieval": "Strong",
        "sentence_transformers": True,
        "prefix_required": "query:/passage:",
        "notes": "E5 small, good quality/speed tradeoff"
    },
    {
        "name": "intfloat/e5-base-v2",
        "max_seq_length": 512,
        "model_size_mb": 220,
        "embedding_dim": 768,
        "mteb_avg": 64.0,
        "mteb_retrieval": "Very Strong",
        "sentence_transformers": True,
        "prefix_required": "query:/passage:",
        "notes": "E5 base, higher quality than small"
    },
    {
        "name": "BAAI/bge-small-en-v1.5",
        "max_seq_length": 512,
        "model_size_mb": 130,
        "embedding_dim": 384,
        "mteb_avg": 63.5,
        "mteb_retrieval": "Very Strong",
        "sentence_transformers": True,
        "prefix_required": "query prefix",
        "notes": "BGE small, excellent retrieval performance"
    },
    {
        "name": "BAAI/bge-base-en-v1.5",
        "max_seq_length": 512,
        "model_size_mb": 420,
        "embedding_dim": 768,
        "mteb_avg": 64.2,
        "mteb_retrieval": "Very Strong",
        "sentence_transformers": True,
        "prefix_required": "query prefix",
        "notes": "BGE base, highest quality in lightweight category"
    },
    {
        "name": "sentence-transformers/all-MiniLM-L12-v2",
        "max_seq_length": 256,
        "model_size_mb": 130,
        "embedding_dim": 384,
        "mteb_avg": 56.0,
        "mteb_retrieval": "Good",
        "sentence_transformers": True,
        "prefix_required": "None",
        "notes": "MiniLM L12, 256 tokens (needs chunking), very fast"
    },
    {
        "name": "sentence-transformers/all-MiniLM-L6-v2",
        "max_seq_length": 256,
        "model_size_mb": 80,
        "embedding_dim": 384,
        "mteb_avg": 58.0,
        "mteb_retrieval": "Good",
        "sentence_transformers": True,
        "prefix_required": "None",
        "notes": "MiniLM L6, 256 tokens (needs chunking), fastest"
    },
    {
        "name": "sentence-transformers/all-mpnet-base-v2",
        "max_seq_length": 384,
        "model_size_mb": 420,
        "embedding_dim": 768,
        "mteb_avg": 57.0,
        "mteb_retrieval": "Strong",
        "sentence_transformers": True,
        "prefix_required": "None",
        "notes": "MPNet base, 384 tokens (needs chunking)"
    },
    {
        "name": "sentence-transformers/paraphrase-mpnet-base-v2",
        "max_seq_length": 384,
        "model_size_mb": 420,
        "embedding_dim": 768,
        "mteb_avg": 56.5,
        "mteb_retrieval": "Good",
        "sentence_transformers": True,
        "prefix_required": "None",
        "notes": "Paraphrase MPNet, 384 tokens (needs chunking)"
    },
    {
        "name": "sentence-transformers/all-MiniLM-L6-v2",
        "max_seq_length": 256,
        "model_size_mb": 80,
        "embedding_dim": 384,
        "mteb_avg": 58.0,
        "mteb_retrieval": "Good",
        "sentence_transformers": True,
        "prefix_required": "None",
        "notes": "MiniLM L6, smallest model, 256 tokens"
    },
    {
        "name": "intfloat/multilingual-e5-small",
        "max_seq_length": 512,
        "model_size_mb": 130,
        "embedding_dim": 384,
        "mteb_avg": 60.0,
        "mteb_retrieval": "Strong",
        "sentence_transformers": True,
        "prefix_required": "query:/passage:",
        "notes": "Multilingual E5 small, supports multiple languages"
    },
    {
        "name": "BAAI/bge-small-en-v1.5",
        "max_seq_length": 512,
        "model_size_mb": 130,
        "embedding_dim": 384,
        "mteb_avg": 63.5,
        "mteb_retrieval": "Very Strong",
        "sentence_transformers": True,
        "prefix_required": "query prefix",
        "notes": "BGE small (duplicate entry for reference)"
    },
]


def filter_by_criteria(models: list, max_size_mb: int = 500, min_seq_length: int = 512) -> list:
    """Filter models by our criteria."""
    filtered = []
    for model in models:
        if (model["model_size_mb"] <= max_size_mb and 
            model["max_seq_length"] >= min_seq_length and
            model["sentence_transformers"]):
            filtered.append(model)
    return filtered


def print_survey() -> None:
    """Print comprehensive survey of lightweight models."""
    print("=" * 80)
    print("Lightweight Embedding Models Survey - MTEB Leaderboard")
    print("=" * 80)
    print()
    print("Criteria:")
    print("  - Max sequence length ≥ 512 tokens")
    print("  - Model size < 500MB")
    print("  - Sentence-transformers compatible")
    print("  - Good MTEB scores")
    print()
    
    # Filter by criteria
    qualified = filter_by_criteria(LIGHTWEIGHT_MODELS)
    
    print(f"Models meeting criteria: {len(qualified)}")
    print()
    print("-" * 80)
    print("QUALIFIED MODELS (≥512 tokens, <500MB)")
    print("-" * 80)
    print()
    
    # Sort by MTEB average (descending)
    qualified_sorted = sorted(qualified, key=lambda x: x["mteb_avg"], reverse=True)
    
    print(f"{'Model Name':<45} {'Size':<8} {'Seq Len':<8} {'MTEB':<8} {'Retrieval':<12} {'Prefix':<15}")
    print("-" * 80)
    
    for model in qualified_sorted:
        prefix = model["prefix_required"][:14] if model["prefix_required"] else "None"
        print(f"{model['name']:<45} {model['model_size_mb']:>4}MB {model['max_seq_length']:>6} {model['mteb_avg']:>6.1f} {model['mteb_retrieval']:<12} {prefix:<15}")
    
    print()
    print("-" * 80)
    print("ALL LIGHTWEIGHT MODELS (including <512 tokens)")
    print("-" * 80)
    print()
    
    # All models sorted by MTEB
    all_sorted = sorted(LIGHTWEIGHT_MODELS, key=lambda x: x["mteb_avg"], reverse=True)
    
    print(f"{'Model Name':<45} {'Size':<8} {'Seq Len':<8} {'MTEB':<8} {'Retrieval':<12} {'Notes':<30}")
    print("-" * 80)
    
    for model in all_sorted:
        status = "✅" if model["max_seq_length"] >= 512 and model["model_size_mb"] < 500 else "⚠️"
        notes = model["notes"][:29]
        print(f"{status} {model['name']:<43} {model['model_size_mb']:>4}MB {model['max_seq_length']:>6} {model['mteb_avg']:>6.1f} {model['mteb_retrieval']:<12} {notes:<30}")
    
    print()
    print("=" * 80)
    print("Top Recommendations")
    print("=" * 80)
    print()
    
    if qualified_sorted:
        print("1. BEST QUALITY:")
        top = qualified_sorted[0]
        print(f"   {top['name']}")
        print(f"   MTEB: {top['mteb_avg']}, Size: {top['model_size_mb']}MB, Seq: {top['max_seq_length']}")
        print()
        
        print("2. BEST QUALITY/SPEED TRADEOFF:")
        # Find best balance (high MTEB, small size)
        balanced = min(qualified_sorted[:3], key=lambda x: x["model_size_mb"])
        print(f"   {balanced['name']}")
        print(f"   MTEB: {balanced['mteb_avg']}, Size: {balanced['model_size_mb']}MB, Seq: {balanced['max_seq_length']}")
        print()
        
        print("3. SMALLEST (if quality acceptable):")
        smallest = min(qualified_sorted, key=lambda x: x["model_size_mb"])
        print(f"   {smallest['name']}")
        print(f"   MTEB: {smallest['mteb_avg']}, Size: {smallest['model_size_mb']}MB, Seq: {smallest['max_seq_length']}")
    
    print()
    print("=" * 80)
    print("Note: MTEB scores are approximate. Verify from official leaderboard:")
    print("https://huggingface.co/spaces/mteb/leaderboard")
    print("=" * 80)


if __name__ == "__main__":
    print_survey()

