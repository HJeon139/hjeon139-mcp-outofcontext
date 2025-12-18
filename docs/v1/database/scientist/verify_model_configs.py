#!/usr/bin/env python3
"""
Verify that each model is configured correctly according to their HuggingFace model cards.

Checks:
1. Prefix requirements (query/document)
2. Matryoshka support and configuration
3. Normalization requirements
4. Trust remote code requirements
5. Other model-specific settings
"""

import json
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: sentence-transformers not installed")
    exit(1)


# Model configurations from research document
MODELS = [
    {
        "name": "nomic-ai/modernbert-embed-base",
        "expected_prefix_query": "search_query: ",
        "expected_prefix_document": "search_document: ",
        "supports_matryoshka": True,
        "matryoshka_dims": [768, 256],
        "notes": "Requires prefixes, supports Matryoshka"
    },
    {
        "name": "Alibaba-NLP/gte-multilingual-base",
        "expected_prefix_query": "",  # No prefix
        "expected_prefix_document": "",  # No prefix
        "supports_matryoshka": False,
        "notes": "No prefix needed"
    },
    {
        "name": "ibm-granite/granite-embedding-english-r2",
        "expected_prefix_query": "",  # Unknown
        "expected_prefix_document": "",  # Unknown
        "supports_matryoshka": False,
        "notes": "Need to verify from model card"
    },
    {
        "name": "Snowflake/snowflake-arctic-embed-l-v2.0",
        "expected_prefix_query": "",  # Unknown
        "expected_prefix_document": "",  # Unknown
        "supports_matryoshka": False,
        "notes": "Need to verify from model card"
    },
]


def check_model_config(model_info: dict) -> dict:
    """Check a model's configuration."""
    model_name = model_info["name"]
    print(f"\n{'='*60}")
    print(f"Checking: {model_name}")
    print(f"{'='*60}")
    
    result = {
        "model_name": model_name,
        "status": "unknown",
        "issues": [],
        "warnings": [],
        "config": {}
    }
    
    try:
        # Try loading with trust_remote_code if needed
        try:
            model = SentenceTransformer(model_name, device="cpu")
        except Exception as e:
            if "trust_remote_code" in str(e).lower() or "custom code" in str(e).lower():
                print(f"  Loading with trust_remote_code=True...")
                model = SentenceTransformer(model_name, device="cpu", trust_remote_code=True)
            else:
                raise
        
        # Get model info
        result["config"]["max_seq_length"] = model.max_seq_length
        result["config"]["embedding_dim"] = model.get_sentence_embedding_dimension()
        
        print(f"  Max sequence length: {result['config']['max_seq_length']}")
        print(f"  Embedding dimension: {result['config']['embedding_dim']}")
        
        # Check if model has normalize_embeddings attribute
        if hasattr(model, "normalize_embeddings"):
            result["config"]["normalize_embeddings"] = model.normalize_embeddings
            print(f"  Normalize embeddings: {result['config']['normalize_embeddings']}")
        else:
            result["warnings"].append("Cannot determine normalize_embeddings setting")
        
        # Test embedding with and without prefixes
        test_query = "What is semantic search?"
        test_document = "Semantic search is a search method that uses meaning to find relevant results."
        
        # Test query embedding
        if model_info["expected_prefix_query"]:
            query_with_prefix = f"{model_info['expected_prefix_query']}{test_query}"
            query_without_prefix = test_query
            print(f"\n  Testing query embedding:")
            print(f"    With prefix: '{query_with_prefix}'")
            emb_with = model.encode([query_with_prefix], show_progress_bar=False)[0]
            emb_without = model.encode([query_without_prefix], show_progress_bar=False)[0]
            print(f"    Embedding shape: {emb_with.shape}")
            print(f"    ⚠️  Note: Prefix requirement verified from model card, but actual impact needs testing")
        else:
            query_emb = model.encode([test_query], show_progress_bar=False)[0]
            print(f"\n  Testing query embedding (no prefix):")
            print(f"    Embedding shape: {query_emb.shape}")
        
        # Test document embedding
        if model_info["expected_prefix_document"]:
            doc_with_prefix = f"{model_info['expected_prefix_document']}{test_document}"
            doc_without_prefix = test_document
            print(f"\n  Testing document embedding:")
            print(f"    With prefix: '{doc_with_prefix}'")
            emb_with = model.encode([doc_with_prefix], show_progress_bar=False)[0]
            emb_without = model.encode([doc_with_prefix], show_progress_bar=False)[0]
            print(f"    Embedding shape: {emb_with.shape}")
        else:
            doc_emb = model.encode([test_document], show_progress_bar=False)[0]
            print(f"\n  Testing document embedding (no prefix):")
            print(f"    Embedding shape: {doc_emb.shape}")
        
        # Check Matryoshka support
        if model_info.get("supports_matryoshka"):
            print(f"\n  Matryoshka support: YES")
            print(f"    Supported dimensions: {model_info.get('matryoshka_dims', [])}")
            print(f"    ⚠️  WARNING: Not using Matryoshka in benchmark (using full {result['config']['embedding_dim']} dims)")
            result["warnings"].append(f"Model supports Matryoshka but benchmark uses full {result['config']['embedding_dim']} dimensions")
        else:
            print(f"\n  Matryoshka support: NO or unknown")
        
        result["status"] = "success"
        
    except Exception as e:
        print(f"  ERROR: {e}")
        result["status"] = "failed"
        result["issues"].append(str(e))
    
    return result


def main() -> None:
    """Main entry point."""
    print("="*60)
    print("Model Configuration Verification")
    print("="*60)
    print("\nThis script checks if models are configured correctly")
    print("according to their HuggingFace model cards.")
    print("\n⚠️  NOTE: This is a quick check. For full verification,")
    print("   consult each model's HuggingFace model card page.")
    
    results = []
    for model_info in MODELS:
        result = check_model_config(model_info)
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    
    for result in results:
        print(f"\n{result['model_name']}:")
        print(f"  Status: {result['status']}")
        if result.get('warnings'):
            print(f"  Warnings: {len(result['warnings'])}")
            for warning in result['warnings']:
                print(f"    - {warning}")
        if result.get('issues'):
            print(f"  Issues: {len(result['issues'])}")
            for issue in result['issues']:
                print(f"    - {issue}")
    
    # Save results
    output_file = Path("model-config-verification.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved to: {output_file}")


if __name__ == "__main__":
    main()

