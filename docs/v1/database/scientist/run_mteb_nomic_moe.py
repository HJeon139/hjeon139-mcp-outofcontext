#!/usr/bin/env python3
"""
Run MTEB benchmark on nomic-ai/nomic-embed-text-v2-moe model.

MTEB (Massive Text Embedding Benchmark) evaluates models across multiple tasks:
- Retrieval
- Classification
- Clustering
- Pair Classification
- Reranking
- STS (Semantic Textual Similarity)

This script runs MTEB to get comprehensive benchmark scores.
"""

import json
from pathlib import Path
from typing import Any

try:
    from mteb import evaluate, get_tasks
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"Error: Required package not installed: {e}")
    print("Install with: pip install mteb sentence-transformers")
    exit(1)


def run_mteb_benchmark(
    model_name: str,
    output_file: Path,
    tasks: list[str] | None = None,
    trust_remote_code: bool = True
) -> dict[str, Any]:
    """
    Run MTEB benchmark on a model.
    
    Args:
        model_name: HuggingFace model name
        output_file: Path to save results JSON
        tasks: List of task names to run (None = all tasks)
        trust_remote_code: Whether to trust remote code when loading model
    
    Returns:
        Dictionary with benchmark results
    """
    print("="*80)
    print(f"MTEB Benchmark: {model_name}")
    print("="*80)
    print()
    
    # Load model
    print(f"Loading model: {model_name}")
    try:
        model = SentenceTransformer(
            model_name,
            device="cpu",  # Use CPU to avoid MPS memory issues
            trust_remote_code=trust_remote_code
        )
        print(f"✅ Model loaded successfully")
        print(f"   Max sequence length: {model.max_seq_length}")
        print(f"   Embedding dimension: {model.get_sentence_embedding_dimension()}")
    except Exception as e:
        print(f"❌ ERROR: Failed to load model: {e}")
        return {
            "model_name": model_name,
            "status": "failed",
            "error": str(e)
        }
    
    # Get tasks to run
    if tasks is None:
        # Run a subset of tasks for faster evaluation
        # Focus on retrieval tasks which are most relevant for our use case
        print(f"\nGetting retrieval tasks (for faster evaluation)...")
        task_types = ["Retrieval"]  # Main retrieval tasks
    else:
        task_types = tasks
    
    print(f"Task types to run: {task_types}")
    print(f"\n⚠️  NOTE: This may take a while depending on the tasks selected.")
    print(f"   Full MTEB can take several hours. This script runs retrieval tasks.")
    print()
    
    # Get tasks
    print(f"Fetching tasks...")
    try:
        available_tasks = get_tasks(task_types=task_types)
        print(f"Found {len(available_tasks)} tasks")
        
        # Limit to first few tasks for faster evaluation (can remove this for full run)
        if len(available_tasks) > 5:
            print(f"⚠️  Limiting to first 5 tasks for faster evaluation")
            print(f"   (Remove this limit for full evaluation)")
            available_tasks = available_tasks[:5]
    except Exception as e:
        print(f"❌ Error getting tasks: {e}")
        return {
            "model_name": model_name,
            "status": "failed",
            "error": f"Failed to get tasks: {e}"
        }
    
    if not available_tasks:
        print(f"⚠️  No tasks found")
        return {
            "model_name": model_name,
            "status": "failed",
            "error": "No tasks found"
        }
    
    # Run evaluation using the newer mteb.evaluate API
    print(f"\n{'='*80}")
    print(f"Running MTEB evaluation on {len(available_tasks)} tasks...")
    print(f"{'='*80}")
    print()
    
    try:
        # Run each task
        task_results = {}
        for i, task in enumerate(available_tasks, 1):
            task_name = getattr(task, 'description', {}).get('name', f'task_{i}')
            print(f"\n[{i}/{len(available_tasks)}] Running: {task_name}")
            try:
                result = evaluate(
                    model=model,
                    tasks=task,
                    show_progress_bar=True
                )
                task_results[task_name] = result
                print(f"✅ Completed: {task_name}")
            except Exception as e:
                print(f"❌ Failed: {task_name} - {e}")
                task_results[task_name] = {"error": str(e)}
        
        print(f"\n✅ Evaluation complete!")
        
        # Extract summary
        summary = {
            "model_name": model_name,
            "status": "success",
            "tasks_completed": len([r for r in task_results.values() if "error" not in r]),
            "tasks_failed": len([r for r in task_results.values() if "error" in r]),
            "results": task_results
        }
        
        # Calculate summary statistics
        summary = {
            "model_name": model_name,
            "status": "success",
            "tasks_completed": sum(len(v) for v in results.values()),
            "results": results
        }
        
    except Exception as e:
        print(f"\n❌ ERROR during evaluation: {e}")
        return {
            "model_name": model_name,
            "status": "failed",
            "error": str(e)
        }
    
    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print(f"✅ Benchmark complete!")
    print(f"Results saved to: {output_file}")
    print(f"{'='*80}")
    
    return summary


def main() -> None:
    """Main entry point."""
    model_name = "nomic-ai/nomic-embed-text-v2-moe"
    output_file = Path("mteb-nomic-embed-text-v2-moe-results.json")
    
    print("="*80)
    print("MTEB Benchmark for nomic-ai/nomic-embed-text-v2-moe")
    print("="*80)
    print()
    print("This will run MTEB retrieval tasks to get benchmark scores.")
    print("Note: Full MTEB can take hours. This script focuses on retrieval tasks.")
    print()
    
    # Run benchmark with retrieval tasks only (faster)
    # To run all tasks, change tasks=None (will take much longer)
    results = run_mteb_benchmark(
        model_name=model_name,
        output_file=output_file,
        tasks=["Retrieval"],  # Focus on retrieval (most relevant for our use case)
        trust_remote_code=True
    )
    
    if results.get("status") == "success":
        print(f"\n✅ Successfully completed {results.get('tasks_completed', 0)} tasks")
        print(f"\nTo view full results, check: {output_file}")
    else:
        print(f"\n❌ Benchmark failed: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()

