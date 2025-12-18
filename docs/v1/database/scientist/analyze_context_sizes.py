#!/usr/bin/env python3
"""
Analyze token counts for context files to verify document size assumptions.

Usage:
    python analyze_context_sizes.py --contexts-dir ../../../../.out_of_context/contexts
"""

import argparse
import statistics
from pathlib import Path
from typing import Any

try:
    import tiktoken
except ImportError:
    print("Error: tiktoken not installed. Install with: pip install tiktoken")
    exit(1)


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def analyze_contexts(contexts_dir: Path) -> dict[str, Any]:
    """Analyze token counts for all context files."""
    results = {
        "files": [],
        "statistics": {}
    }
    
    token_counts = []
    word_counts = []
    char_counts = []
    
    # Analyze each context file
    for context_file in sorted(contexts_dir.glob("*.mdc")):
        context_name = context_file.stem
        
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count tokens (using cl100k_base - same as GPT-4)
            token_count = count_tokens(content)
            
            # Also count words and characters for reference
            word_count = len(content.split())
            char_count = len(content)
            
            token_counts.append(token_count)
            word_counts.append(word_count)
            char_counts.append(char_count)
            
            results["files"].append({
                "name": context_name,
                "tokens": token_count,
                "words": word_count,
                "characters": char_count,
                "file_size_kb": context_file.stat().st_size / 1024
            })
            
        except Exception as e:
            print(f"Warning: Failed to read {context_file}: {e}")
    
    # Calculate statistics
    if token_counts:
        results["statistics"] = {
            "num_files": len(token_counts),
            "tokens": {
                "min": min(token_counts),
                "max": max(token_counts),
                "mean": statistics.mean(token_counts),
                "median": statistics.median(token_counts),
                "p75": statistics.quantiles(token_counts, n=4)[2] if len(token_counts) >= 4 else max(token_counts),
                "p95": statistics.quantiles(token_counts, n=20)[18] if len(token_counts) >= 20 else max(token_counts),
                "p99": statistics.quantiles(token_counts, n=100)[98] if len(token_counts) >= 100 else max(token_counts),
            },
            "words": {
                "min": min(word_counts),
                "max": max(word_counts),
                "mean": statistics.mean(word_counts),
                "median": statistics.median(word_counts),
            },
            "characters": {
                "min": min(char_counts),
                "max": max(char_counts),
                "mean": statistics.mean(char_counts),
                "median": statistics.median(char_counts),
            }
        }
    
    return results


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze context file token counts")
    parser.add_argument(
        "--contexts-dir",
        type=Path,
        default=Path("../../../../.out_of_context/contexts"),
        help="Path to contexts directory"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional: Path to save results JSON"
    )
    
    args = parser.parse_args()
    
    if not args.contexts_dir.exists():
        print(f"Error: Contexts directory not found: {args.contexts_dir}")
        return
    
    print(f"Analyzing contexts in: {args.contexts_dir}")
    print()
    
    # Analyze
    results = analyze_contexts(args.contexts_dir)
    
    # Print results
    print("=" * 60)
    print("Context File Token Analysis")
    print("=" * 60)
    print()
    
    print("Individual Files:")
    print("-" * 60)
    for file_info in results["files"]:
        print(f"  {file_info['name']:40s} {file_info['tokens']:6d} tokens  {file_info['words']:5d} words")
    print()
    
    if results["statistics"]:
        stats = results["statistics"]
        print("Statistics:")
        print("-" * 60)
        print(f"  Number of files:     {stats['num_files']}")
        print()
        print("  Token Counts:")
        print(f"    Min:               {stats['tokens']['min']:6d} tokens")
        print(f"    Max:               {stats['tokens']['max']:6d} tokens")
        print(f"    Mean:              {stats['tokens']['mean']:6.1f} tokens")
        print(f"    Median:            {stats['tokens']['median']:6.1f} tokens")
        print(f"    P75:               {stats['tokens']['p75']:6.1f} tokens")
        print(f"    P95:               {stats['tokens']['p95']:6.1f} tokens")
        if 'p99' in stats['tokens']:
            print(f"    P99:               {stats['tokens']['p99']:6.1f} tokens")
        print()
        print("  Word Counts (for reference):")
        print(f"    Mean:              {stats['words']['mean']:6.1f} words")
        print(f"    Median:            {stats['words']['median']:6.1f} words")
        print()
        
        # Analysis and recommendations
        print("=" * 60)
        print("Analysis & Recommendations")
        print("=" * 60)
        print()
        
        max_tokens = stats['tokens']['max']
        p95_tokens = stats['tokens']['p95']
        median_tokens = stats['tokens']['median']
        
        print(f"Current assumption: 500-1000 tokens per context")
        print(f"Actual median:      {median_tokens:.0f} tokens")
        print(f"Actual P95:        {p95_tokens:.0f} tokens")
        print(f"Actual max:        {max_tokens:.0f} tokens")
        print()
        
        # Model recommendations
        print("Model Context Length Requirements:")
        print("-" * 60)
        
        models = [
            ("intfloat/e5-small-v2", 512),
            ("intfloat/e5-base-v2", 512),
            ("BAAI/bge-small-en-v1.5", 512),
            ("BAAI/bge-base-en-v1.5", 512),
            ("sentence-transformers/all-mpnet-base-v2", 384),
        ]
        
        for model_name, max_length in models:
            if max_tokens <= max_length:
                status = "✅ Fits (no chunking)"
            elif p95_tokens <= max_length:
                status = "⚠️  P95 fits, max needs chunking"
            elif median_tokens <= max_length:
                status = "⚠️  Median fits, most need chunking"
            else:
                status = "❌ Needs chunking"
            
            print(f"  {model_name:45s} {max_length:4d} tokens  {status}")
        
        print()
        
        # Recommendation
        if max_tokens > 512:
            print("⚠️  WARNING: Some contexts exceed 512 tokens!")
            print(f"   Max context: {max_tokens} tokens")
            print(f"   P95 context: {p95_tokens:.0f} tokens")
            print()
            print("   Recommendation:")
            if p95_tokens <= 512:
                print("   - Use 512-token model with truncation for outliers")
                print("   - Or implement chunking for contexts > 512 tokens")
            else:
                print("   - Implement chunking strategy")
                print("   - Or consider model with larger context window")
        else:
            print("✅ All contexts fit within 512 tokens")
            print("   - 512-token models are sufficient")
            print("   - No chunking required")
    
    # Save results if requested
    if args.output:
        import json
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()

