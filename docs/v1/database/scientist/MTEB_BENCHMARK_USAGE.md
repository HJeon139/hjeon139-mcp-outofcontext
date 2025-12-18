# MTEB Benchmark Usage Guide

## Quick Start

### Full Benchmark (All Retrieval Tasks)

**From terminal:**
```bash
cd docs/v1/database/scientist
hatch run python run_mteb_modernbert.py --full
```

**With nohup (background):**
```bash
cd docs/v1/database/scientist
./run_mteb_modernbert.sh --full
```

### Test Run (10 Tasks)

**From terminal:**
```bash
cd docs/v1/database/scientist
hatch run python run_mteb_modernbert.py --test
```

**With nohup (background):**
```bash
cd docs/v1/database/scientist
./run_mteb_modernbert.sh --test
```

## Command-Line Options

```bash
python run_mteb_modernbert.py [OPTIONS]
```

### Options

- `--full`: Run full benchmark (all retrieval tasks, no timeouts)
- `--test`: Run test mode (10 tasks, 5 min per task, 10 min total)
- `--limit-tasks N`: Limit number of tasks to run
- `--task-timeout SECONDS`: Timeout per task in seconds
- `--total-timeout SECONDS`: Total timeout for entire benchmark
- `--device {mps,cuda,cpu,auto}`: Device to use (default: auto)
- `--output PATH`: Output file path
- `--task-types TYPE [TYPE ...]`: Task types to run (default: Retrieval)

### Examples

```bash
# Full benchmark
python run_mteb_modernbert.py --full

# Test run
python run_mteb_modernbert.py --test

# Custom: 5 tasks, 10 min per task
python run_mteb_modernbert.py --limit-tasks 5 --task-timeout 600

# Use CPU instead of auto-detecting
python run_mteb_modernbert.py --full --device cpu

# Run with custom output file
python run_mteb_modernbert.py --full --output my-results.json
```

## Monitoring Progress

### While Running

```bash
# Watch the main log file (most detailed)
tail -f docs/v1/database/scientist/mteb-modernbert.log

# Watch nohup output (if using shell script)
tail -f docs/v1/database/scientist/nohup-mteb-modernbert.out
```

### Check Status

```bash
# Check if process is still running
ps aux | grep run_mteb_modernbert

# Or check the PID file
cat docs/v1/database/scientist/mteb-modernbert.pid
```

## Results

Results are saved to:
- **JSON Results**: `mteb-modernbert-embed-base-results.json`
- **Log File**: `mteb-modernbert.log`

### Results Structure

```json
{
  "model_name": "nomic-ai/modernbert-embed-base",
  "status": "success",
  "device": "mps",
  "tasks_total": 361,
  "tasks_completed": 361,
  "tasks_failed": 0,
  "cpu_fallback_count": 72,
  "cpu_fallback_rate": 0.199,
  "mps_success_rate": 0.801,
  "results": { ... }
}
```

## MTEB API Verification

✅ **Implementation is correct:**
- Uses `mteb.evaluate()` with proper parameters
- Passes `encode_kwargs` for batch size control
- Uses `mteb.get_tasks()` to fetch tasks
- Handles prefixes automatically via model metadata
- Follows MTEB best practices

## Hardware Acceleration

- **macOS**: Automatically uses MPS (Metal Performance Shaders)
- **Linux/Windows**: Automatically uses CUDA if available
- **Fallback**: Automatically falls back to CPU if GPU fails
- **Batch Size**: Uses batch_size=4 for MPS, batch_size=32 for CPU

## Expected Performance

- **MPS Success Rate**: ~80% (based on 10-task sample)
- **CPU Fallback Rate**: ~20% (for very large corpora)
- **Full Benchmark**: 361 retrieval tasks, may take 8-24 hours depending on hardware

## Troubleshooting

### MPS Buffer Size Errors
- Script automatically falls back to CPU
- This is expected for very large corpora (22k+ documents)

### Timeout Issues
- Use `--task-timeout` to increase per-task timeout
- Use `--total-timeout` to set overall benchmark timeout

### Memory Issues
- Script uses batch_size=4 for MPS to minimize memory usage
- CPU fallback uses batch_size=32 (CPU can handle larger batches)

