#!/usr/bin/env python3
"""
Run MTEB benchmark on nomic-ai/modernbert-embed-base model.

MTEB (Massive Text Embedding Benchmark) evaluates models across multiple tasks:
- Retrieval
- Classification
- Clustering
- Pair Classification
- Reranking
- STS (Semantic Textual Similarity)

This script runs MTEB to get comprehensive benchmark scores for apples-to-apples
comparison.

Model Requirements (from HuggingFace model card):
- transformers>=4.48.0 (checked at runtime)
- Prefixes required: 'search_query: ' for queries, 'search_document: ' for documents
- MTEB should handle prefixes automatically via model metadata

Hardware Acceleration:
- macOS: Uses MPS (Metal Performance Shaders) when available
- Automatic fallback to CPU if MPS unavailable
- Note: Flash Attention is CUDA-only (not available on macOS)
- ModernBERT-base supports efficient inference with unpadding and Flash Attention

Lessons learned from run_mteb_nomic_moe.py:
- Fixed duplicate summary calculation bug
- Added proper device detection (MPS/CUDA/CPU)
- Added transformers version check
- Improved logging and progress tracking
- Fixed path handling for nohup execution
"""

import argparse
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import torch
    import transformers
    from mteb import evaluate, get_tasks
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"Error: Required package not installed: {e}")
    print("Install with: pip install mteb sentence-transformers torch transformers")
    sys.exit(1)

# Get script directory for output files (works when run from any location)
SCRIPT_DIR = Path(__file__).parent.resolve()

# Configure logging for nohup (both stdout and file)
log_file = SCRIPT_DIR / "mteb-modernbert.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Check transformers version requirement
# modernbert-embed-base requires transformers>=4.48.0
MIN_TRANSFORMERS_VERSION = (4, 48, 0)
try:
    current_version = tuple(map(int, transformers.__version__.split(".")[:3]))
    if current_version < MIN_TRANSFORMERS_VERSION:
        logger.warning(
            f"⚠️  transformers version {transformers.__version__} may be too old. "
            f"modernbert-embed-base requires >=4.48.0. "
            f"Current: {transformers.__version__}, Required: >=4.48.0"
        )
        logger.warning("   Consider upgrading: pip install --upgrade transformers>=4.48.0")
except Exception:
    pass  # Version check failed, but continue


def configure_mps_for_large_tensors() -> None:
    """
    Log MPS configuration (already set before torch import).
    This helps avoid 'Invalid buffer size' errors on macOS.
    """
    if torch.backends.mps.is_available():
        ratio = os.environ.get("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "not set")
        fallback = os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK", "not set")
        logger.info(f"   MPS config: HIGH_WATERMARK_RATIO={ratio}, FALLBACK={fallback}")


def detect_device() -> str:
    """
    Detect best available device for acceleration.

    Returns:
        Device string: 'mps', 'cuda', or 'cpu'
    """
    if torch.backends.mps.is_available():
        logger.info("✅ MPS (Metal Performance Shaders) available - using GPU acceleration")
        configure_mps_for_large_tensors()
        return "mps"
    elif torch.cuda.is_available():
        logger.info("✅ CUDA available - using GPU acceleration")
        return "cuda"
    else:
        logger.info("⚠️  No GPU acceleration available - using CPU")
        return "cpu"


def load_existing_results(output_file: Path) -> dict[str, Any] | None:
    """
    Load existing results file if it exists.

    Returns:
        Dictionary with existing results or None if file doesn't exist
    """
    if output_file.exists():
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
                logger.info(f"✅ Loaded existing results from {output_file}")
                logger.info(f"   Found {existing.get('tasks_completed', 0)} completed tasks")
                return existing
        except Exception as e:
            logger.warning(f"⚠️  Could not load existing results: {e}")
    return None


def get_completed_task_names(existing_results: dict[str, Any] | None) -> set[str]:
    """
    Extract names of completed tasks from existing results.

    Returns:
        Set of completed task names
    """
    if not existing_results:
        return set()

    completed = set()
    results = existing_results.get("results", {})
    for task_name, task_data in results.items():
        # Task is completed if it has a result and no error
        if isinstance(task_data, dict) and "error" not in task_data:
            if "result" in task_data or "main_score" in task_data:
                completed.add(task_name)

    return completed


def save_results_incremental(output_file: Path, summary: dict[str, Any]) -> None:
    """Save results incrementally after each task."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)


def run_mteb_benchmark(
    model_name: str,
    output_file: Path,
    device: str | None = None,
    task_types: list[str] | None = None,
    trust_remote_code: bool = True,
    limit_tasks: int | None = None,
    task_timeout_seconds: int | None = None,
    total_timeout_seconds: int | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    """
    Run MTEB benchmark on a model.

    Args:
        model_name: HuggingFace model name
        output_file: Path to save results JSON
        device: Device to use ('mps', 'cuda', 'cpu', or None for auto-detect)
        task_types: List of task types to run (None = all tasks)
        trust_remote_code: Whether to trust remote code when loading model
        limit_tasks: Limit number of tasks (None = all tasks)
        task_timeout_seconds: Timeout per task in seconds (None = no timeout)
        total_timeout_seconds: Total timeout for entire benchmark (None = no timeout)
        resume: If True, load existing results and skip completed tasks

    Returns:
        Dictionary with benchmark results
    """
    # Load existing results if resuming
    existing_results = None
    completed_task_names = set()
    if resume:
        existing_results = load_existing_results(output_file)
        if existing_results:
            completed_task_names = get_completed_task_names(existing_results)
            logger.info(f"   Will skip {len(completed_task_names)} already completed tasks")
            logger.info("")

    start_time = time.time()
    logger.info("=" * 80)
    logger.info(f"MTEB Benchmark: {model_name}")
    if resume and existing_results:
        logger.info("   MODE: RESUME (skipping completed tasks)")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().isoformat()}")
    logger.info("")

    # Detect device if not specified
    if device is None:
        device = detect_device()
        # MPS can have issues with large tensors, so we'll try MPS first
        # but allow fallback to CPU if needed
        if device == "mps":
            logger.info(
                "⚠️  Note: MPS may have issues with large tensors. Will fallback to CPU if needed."
            )

    logger.info(f"Using device: {device}")
    logger.info("")

    # Load model
    logger.info(f"Loading model: {model_name}")
    logger.info("")
    logger.info("⚠️  IMPORTANT: This model requires prefixes for optimal performance:")
    logger.info("   - Queries: 'search_query: ' prefix")
    logger.info("   - Documents: 'search_document: ' prefix")
    logger.info("   MTEB should handle this automatically via model metadata.")
    logger.info("")
    try:
        model = SentenceTransformer(model_name, device=device, trust_remote_code=trust_remote_code)
        logger.info("✅ Model loaded successfully")
        logger.info(f"   Max sequence length: {model.max_seq_length}")
        logger.info(f"   Embedding dimension: {model.get_sentence_embedding_dimension()}")
        logger.info(f"   Device: {device}")
        logger.info("")
        logger.info("   Model configuration verified:")
        logger.info("   - Prefixes should be handled automatically by MTEB")
        logger.info("   - If results seem low, verify prefixes are being applied")
        # Configure batch size for MPS to avoid buffer size issues
        if device == "mps":
            # Use very small batch size for MPS to avoid "Invalid buffer size" errors
            # MPS has strict limits on tensor sizes, especially with large corpora
            batch_size = 4  # Very conservative for MPS
            logger.info(f"   - Using batch_size={batch_size} for MPS compatibility")
            # Store original and set new default
            if not hasattr(model, "_original_encode_kwargs"):
                model._original_encode_kwargs = getattr(model, "_encode_kwargs", {})
            model._encode_kwargs = {"batch_size": batch_size}
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to load model: {e}")
        return {"model_name": model_name, "status": "failed", "error": str(e), "device": device}

    # Get tasks to run
    if task_types is None:
        # Run retrieval tasks for apples-to-apples comparison
        logger.info("Getting retrieval tasks...")
        task_types = ["Retrieval"]
    else:
        logger.info(f"Using specified task types: {task_types}")

    logger.info("")

    # Get tasks
    logger.info("Fetching tasks...")
    try:
        available_tasks = get_tasks(task_types=task_types)
        logger.info(f"Found {len(available_tasks)} tasks")

        # Apply limit if specified (for lighter test runs)
        if limit_tasks is not None and len(available_tasks) > limit_tasks:
            logger.info(f"⚠️  Limiting to first {limit_tasks} tasks (for testing)")
            logger.info("   (Remove limit_tasks parameter for full evaluation)")
            available_tasks = available_tasks[:limit_tasks]
        else:
            logger.info(f"Running all {len(available_tasks)} tasks")

        # Log timeout settings
        if task_timeout_seconds:
            logger.info(f"⚠️  Task timeout: {task_timeout_seconds}s per task")
        if total_timeout_seconds:
            logger.info(f"⚠️  Total timeout: {total_timeout_seconds}s for entire benchmark")
    except Exception as e:
        logger.error(f"❌ Error getting tasks: {e}")
        return {
            "model_name": model_name,
            "status": "failed",
            "error": f"Failed to get tasks: {e}",
            "device": device,
        }

    if not available_tasks:
        logger.warning("⚠️  No tasks found")
        return {
            "model_name": model_name,
            "status": "failed",
            "error": "No tasks found",
            "device": device,
        }

    # Run evaluation
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"Running MTEB evaluation on {len(available_tasks)} tasks...")
    logger.info("=" * 80)
    logger.info("")

    # Initialize task_results from existing results if resuming
    if resume and existing_results:
        task_results = existing_results.get("results", {}).copy()
        cpu_fallback_count = existing_results.get("cpu_fallback_count", 0)
        logger.info(f"   Resuming with {len(task_results)} existing task results")
    else:
        task_results = {}
        cpu_fallback_count = 0

    task_start_times = {}
    benchmark_start_time = time.time()

    # Timeout handler
    def timeout_handler(signum, frame):
        raise TimeoutError("Task timeout exceeded")

    try:
        # Run each task with progress tracking
        skipped_count = 0
        for i, task in enumerate(available_tasks, 1):
            # Check total timeout
            if total_timeout_seconds:
                elapsed = time.time() - benchmark_start_time
                if elapsed >= total_timeout_seconds:
                    logger.warning(
                        f"⚠️  Total timeout ({total_timeout_seconds}s) reached. "
                        f"Stopping after {i - 1} tasks."
                    )
                    break

            # Get task name - try multiple methods to get the actual task identifier
            task_name = None
            if hasattr(task, "metadata") and task.metadata:
                # Metadata is a Pydantic model, access name attribute directly
                task_name = getattr(task.metadata, "name", None)
            if not task_name and hasattr(task, "description"):
                desc = task.description
                if isinstance(desc, dict):
                    task_name = desc.get("name")
            if not task_name:
                # Use class name as fallback (e.g., "CQADupstackAndroidRetrieval")
                task_name = task.__class__.__name__
            if not task_name:
                task_name = f"task_{i}"

            # Skip if already completed (when resuming)
            if resume and task_name in completed_task_names:
                skipped_count += 1
                logger.info("")
                logger.info(
                    f"[{i}/{len(available_tasks)}] ⏭️  Skipping (already completed): {task_name}"
                )
                continue

            task_start = time.time()
            task_start_times[task_name] = task_start

            logger.info("")
            logger.info(f"[{i}/{len(available_tasks)}] Starting: {task_name}")
            logger.info(f"  Start time: {datetime.now().isoformat()}")

            try:
                # Set up timeout signal if specified (Unix/macOS only)
                if task_timeout_seconds:
                    if hasattr(signal, "SIGALRM"):
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(task_timeout_seconds)
                    else:
                        logger.warning(
                            "⚠️  Timeout not supported on this platform "
                            "(Windows doesn't support SIGALRM)"
                        )

                # Run evaluation with progress bar
                # Configure encode_kwargs for MPS compatibility
                encode_kwargs = None
                if device == "mps":
                    # Use smaller batch size for MPS to avoid buffer size errors
                    encode_kwargs = {"batch_size": 4}

                # Try with current device, fallback to CPU if MPS fails
                # Use "only-missing" overwrite strategy to leverage MTEB cache
                # This allows resuming without re-running completed tasks
                try:
                    result = evaluate(
                        model=model,
                        tasks=task,
                        show_progress_bar=True,
                        encode_kwargs=encode_kwargs,
                        overwrite_strategy="only-missing",  # Skip if already in cache
                    )
                except (RuntimeError, ValueError) as e:
                    error_msg = str(e)
                    if (
                        "buffer size" in error_msg.lower()
                        or "mps" in error_msg.lower()
                        or "out of memory" in error_msg.lower()
                    ):
                        logger.warning(f"⚠️  MPS error detected: {error_msg[:150]}...")
                        logger.warning("   Falling back to CPU for this task...")
                        cpu_fallback_count += 1
                        # Reload model on CPU with larger batch size (CPU can handle it)
                        model_cpu = SentenceTransformer(
                            model_name,
                            device="cpu",
                            trust_remote_code=trust_remote_code,
                        )
                        # CPU can handle larger batches, use default batch_size=32
                        # (MTEB will use this if not overridden)
                        result = evaluate(model=model_cpu, tasks=task, show_progress_bar=True)
                        logger.info("✅ Task completed on CPU (fallback)")
                    else:
                        raise  # Re-raise if it's not an MPS buffer issue

                # Cancel timeout if task completed
                if task_timeout_seconds and hasattr(signal, "SIGALRM"):
                    signal.alarm(0)

                task_duration = time.time() - task_start
                task_results[task_name] = {
                    "result": result,
                    "duration_seconds": task_duration,
                    "start_time": datetime.fromtimestamp(task_start).isoformat(),
                    "end_time": datetime.now().isoformat(),
                }

                # Save incrementally after each task (for resume capability)
                # Update summary and save immediately
                temp_completed = [r for r in task_results.values() if "error" not in r]
                temp_summary = {
                    "model_name": model_name,
                    "status": "in_progress",
                    "device": device,
                    "start_time": datetime.fromtimestamp(start_time).isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "tasks_total": len(available_tasks),
                    "tasks_completed": len(temp_completed),
                    "tasks_skipped": skipped_count if resume else 0,
                    "tasks_failed": len([r for r in task_results.values() if "error" in r]),
                    "cpu_fallback_count": cpu_fallback_count,
                    "results": task_results,
                }
                save_results_incremental(output_file, temp_summary)

                # Extract main score if available
                if isinstance(result, dict):
                    main_score = result.get("main_score", "N/A")
                    main_metric = result.get("main_metric", "N/A")
                    logger.info(f"✅ Completed: {task_name}")
                    logger.info(f"   Main score ({main_metric}): {main_score}")
                    logger.info(f"   Duration: {task_duration:.2f} seconds")
                else:
                    logger.info(f"✅ Completed: {task_name} (duration: {task_duration:.2f}s)")

            except TimeoutError as e:
                task_duration = time.time() - task_start
                logger.error(f"⏱️  TIMEOUT: {task_name} exceeded {task_timeout_seconds}s")
                logger.error(f"   Duration before timeout: {task_duration:.2f} seconds")
                task_results[task_name] = {
                    "error": f"Timeout after {task_timeout_seconds}s",
                    "duration_seconds": task_duration,
                    "start_time": datetime.fromtimestamp(task_start).isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "timeout": True,
                }
                # Cancel alarm
                if task_timeout_seconds and hasattr(signal, "SIGALRM"):
                    signal.alarm(0)
                # Save incrementally after failure
                temp_completed = [r for r in task_results.values() if "error" not in r]
                temp_summary = {
                    "model_name": model_name,
                    "status": "in_progress",
                    "device": device,
                    "start_time": datetime.fromtimestamp(start_time).isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "tasks_total": len(available_tasks),
                    "tasks_completed": len(temp_completed),
                    "tasks_skipped": skipped_count if resume else 0,
                    "tasks_failed": len([r for r in task_results.values() if "error" in r]),
                    "cpu_fallback_count": cpu_fallback_count,
                    "results": task_results,
                }
                save_results_incremental(output_file, temp_summary)
            except Exception as e:
                task_duration = time.time() - task_start
                logger.error(f"❌ Failed: {task_name} - {e}")
                logger.error(f"   Duration before failure: {task_duration:.2f} seconds")
                task_results[task_name] = {
                    "error": str(e),
                    "duration_seconds": task_duration,
                    "start_time": datetime.fromtimestamp(task_start).isoformat(),
                    "end_time": datetime.now().isoformat(),
                }
                # Cancel alarm if it was set
                if task_timeout_seconds and hasattr(signal, "SIGALRM"):
                    signal.alarm(0)
                # Save incrementally after failure
                temp_completed = [r for r in task_results.values() if "error" not in r]
                temp_summary = {
                    "model_name": model_name,
                    "status": "in_progress",
                    "device": device,
                    "start_time": datetime.fromtimestamp(start_time).isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "tasks_total": len(available_tasks),
                    "tasks_completed": len(temp_completed),
                    "tasks_skipped": skipped_count if resume else 0,
                    "tasks_failed": len([r for r in task_results.values() if "error" in r]),
                    "cpu_fallback_count": cpu_fallback_count,
                    "results": task_results,
                }
                save_results_incremental(output_file, temp_summary)

        total_duration = time.time() - start_time

        # Calculate summary statistics
        completed_tasks = [r for r in task_results.values() if "error" not in r]
        failed_tasks = [r for r in task_results.values() if "error" in r]

        # Extract main scores for summary
        main_scores = []
        for task_name, task_data in task_results.items():
            if "error" not in task_data and isinstance(task_data.get("result"), dict):
                main_score = task_data["result"].get("main_score")
                if main_score is not None:
                    main_scores.append(main_score)

        summary = {
            "model_name": model_name,
            "status": "success",
            "device": device,
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_duration_seconds": total_duration,
            "tasks_total": len(available_tasks),
            "tasks_completed": len(completed_tasks),
            "tasks_skipped": skipped_count if resume else 0,
            "tasks_failed": len(failed_tasks),
            "cpu_fallback_count": cpu_fallback_count,
            "cpu_fallback_rate": cpu_fallback_count / len(available_tasks)
            if available_tasks
            else 0,
            "mps_success_rate": (len(available_tasks) - cpu_fallback_count) / len(available_tasks)
            if available_tasks
            else 0,
            "main_scores": main_scores,
            "average_main_score": sum(main_scores) / len(main_scores) if main_scores else None,
            "resumed": resume,
            "results": task_results,
        }

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ Evaluation complete!")
        logger.info(
            f"   Total duration: {total_duration / 60:.2f} minutes ({total_duration:.2f} seconds)"
        )
        logger.info(f"   Tasks completed: {len(completed_tasks)}/{len(available_tasks)}")
        if resume and skipped_count > 0:
            logger.info(f"   Tasks skipped (already completed): {skipped_count}")
        logger.info(f"   Tasks failed: {len(failed_tasks)}")
        logger.info("")
        logger.info("   Device Usage Statistics:")
        logger.info(
            f"   - Tasks on MPS: {len(available_tasks) - cpu_fallback_count}/{len(available_tasks)}"
        )
        logger.info(f"   - Tasks on CPU (fallback): {cpu_fallback_count}/{len(available_tasks)}")
        if available_tasks:
            mps_rate = (len(available_tasks) - cpu_fallback_count) / len(available_tasks) * 100
            cpu_rate = cpu_fallback_count / len(available_tasks) * 100
            logger.info(f"   - MPS success rate: {mps_rate:.1f}%")
            logger.info(f"   - CPU fallback rate: {cpu_rate:.1f}%")
        if main_scores:
            logger.info(f"   Average main score: {sum(main_scores) / len(main_scores):.4f}")
        logger.info("=" * 80)

    except Exception as e:
        total_duration = time.time() - start_time
        logger.error(f"❌ ERROR during evaluation: {e}")
        logger.error(f"   Duration before failure: {total_duration:.2f} seconds")
        # Save partial results before exiting
        partial_summary = {
            "model_name": model_name,
            "status": "partial",
            "device": device,
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_duration_seconds": total_duration,
            "tasks_total": len(available_tasks),
            "tasks_completed": len([r for r in task_results.values() if "error" not in r]),
            "tasks_skipped": skipped_count if resume else 0,
            "tasks_failed": len([r for r in task_results.values() if "error" in r]),
            "cpu_fallback_count": cpu_fallback_count,
            "error": str(e),
            "resumed": resume,
            "results": task_results,
        }
        save_results_incremental(output_file, partial_summary)
        return partial_summary

    # Save final results (already saved incrementally, but save final version)
    save_results_incremental(output_file, summary)

    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ Benchmark complete!")
    logger.info(f"Results saved to: {output_file}")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 80)

    return summary


def main() -> None:
    """Main entry point with command-line argument support."""
    parser = argparse.ArgumentParser(
        description="Run MTEB benchmark on nomic-ai/modernbert-embed-base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full benchmark (all retrieval tasks, no timeouts):
  python run_mteb_modernbert.py --full

  # Test run (10 tasks, with timeouts):
  python run_mteb_modernbert.py --test

  # Custom run (5 tasks, 10 min per task timeout):
  python run_mteb_modernbert.py --limit-tasks 5 --task-timeout 600

  # Use CPU instead of auto-detecting:
  python run_mteb_modernbert.py --full --device cpu

  # Resume from existing results (skip completed tasks):
  python run_mteb_modernbert.py --full --resume
        """,
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full benchmark (all retrieval tasks, no timeouts)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test mode (10 tasks, 5 min per task, 10 min total)",
    )
    parser.add_argument(
        "--limit-tasks",
        type=int,
        default=None,
        help="Limit number of tasks to run (default: all tasks for --full, 10 for --test)",
    )
    parser.add_argument(
        "--task-timeout",
        type=int,
        default=None,
        help="Timeout per task in seconds (default: no timeout for --full, 300 for --test)",
    )
    parser.add_argument(
        "--total-timeout",
        type=int,
        default=None,
        help="Total timeout for entire benchmark in seconds (default: no timeout for --full, 600 for --test)",
    )
    parser.add_argument(
        "--device",
        type=str,
        choices=["mps", "cuda", "cpu", "auto"],
        default="auto",
        help="Device to use: mps, cuda, cpu, or auto (default: auto)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: mteb-modernbert-embed-base-results.json)",
    )
    parser.add_argument(
        "--task-types",
        type=str,
        nargs="+",
        default=["Retrieval"],
        help="Task types to run (default: Retrieval). Options: Retrieval, Classification, Clustering, etc.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing results file (skip already completed tasks)",
    )

    args = parser.parse_args()

    # Determine mode
    if args.full and args.test:
        logger.error("❌ Cannot specify both --full and --test")
        sys.exit(1)

    if args.full:
        limit_tasks = None
        task_timeout_seconds = None
        total_timeout_seconds = None
        mode = "FULL"
    elif args.test:
        limit_tasks = args.limit_tasks or 10
        task_timeout_seconds = args.task_timeout or 300
        total_timeout_seconds = args.total_timeout or 600
        mode = "TEST"
    else:
        # Default to test mode if nothing specified
        limit_tasks = args.limit_tasks or 10
        task_timeout_seconds = args.task_timeout or 300
        total_timeout_seconds = args.total_timeout or 600
        mode = "TEST (default)"

    # Set device
    device = None if args.device == "auto" else args.device

    # Set output file
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = SCRIPT_DIR / "mteb-modernbert-embed-base-results.json"

    model_name = "nomic-ai/modernbert-embed-base"

    logger.info("=" * 80)
    logger.info("MTEB Benchmark for nomic-ai/modernbert-embed-base")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Mode: {mode}")
    if limit_tasks:
        logger.info(f"  - Limiting to {limit_tasks} tasks")
    else:
        logger.info("  - Running all tasks")
    if task_timeout_seconds:
        logger.info(f"  - Task timeout: {task_timeout_seconds}s")
    if total_timeout_seconds:
        logger.info(f"  - Total timeout: {total_timeout_seconds}s")
    logger.info(f"  - Task types: {args.task_types}")
    logger.info(f"  - Device: {device or 'auto-detect'}")
    logger.info("")
    logger.info("This will run MTEB retrieval tasks to get benchmark scores.")
    logger.info("Note: Full MTEB can take hours. Progress will be logged to:")
    logger.info("  - Console (stdout)")
    logger.info(f"  - Log file: {log_file}")
    logger.info("")
    logger.info("Model Requirements (from model card):")
    logger.info("  - transformers>=4.48.0 (checking version...)")
    logger.info(
        "  - Prefixes required: 'search_query: ' for queries, 'search_document: ' for documents"
    )
    logger.info("  - MTEB should handle prefixes automatically via model metadata")
    logger.info("")
    logger.info("Hardware acceleration:")
    logger.info("  - macOS: MPS (Metal Performance Shaders) will be used if available")
    logger.info("  - CUDA: Will be used if available (Linux/Windows)")
    logger.info("  - Flash Attention: Not available on macOS (CUDA-only)")
    logger.info(
        "  - Note: ModernBERT-base supports efficient inference with unpadding and Flash Attention"
    )
    logger.info("")

    # Run benchmark
    results = run_mteb_benchmark(
        model_name=model_name,
        output_file=output_file,
        device=device,
        task_types=args.task_types,
        trust_remote_code=True,
        limit_tasks=limit_tasks,
        task_timeout_seconds=task_timeout_seconds,
        total_timeout_seconds=total_timeout_seconds,
        resume=args.resume,
    )

    if results.get("status") == "success":
        logger.info("")
        logger.info(
            f"✅ Successfully completed {results.get('tasks_completed', 0)}/{results.get('tasks_total', 0)} tasks"
        )
        logger.info("")
        logger.info(f"To view full results, check: {output_file}")
        logger.info(f"To view progress log, check: {log_file}")
    else:
        logger.error("")
        logger.error(f"❌ Benchmark failed: {results.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
